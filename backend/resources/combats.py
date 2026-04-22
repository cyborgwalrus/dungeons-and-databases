"""Combat resources for resolving dungeon encounters."""

import random
from typing import Any

from flask import jsonify
from flask_restful import Resource

from backend.db.models import Combat, Encounter, db
from backend.db.reference_data import get_all_item_type_data
from backend.resources.encounters import create_new_encounter
from backend.utils.api_response_cache import (
    invalidate_user_characters_cache,
    invalidate_user_inventory_cache,
)
from backend.utils.game_utils import add_inventory_item, clear_loot_flags, destroy_loot_items
from backend.utils.route_helpers import json_error


def _combat_damage_roll(max_damage: int) -> int:
    """Roll a bounded combat damage value for one turn."""
    return random.randint(max(1, max_damage // 2), max(1, max_damage))


def check_character_death(health: int) -> bool:
    """Return whether the character has died."""
    return health <= 0


def _serialize_combat_character(character, current_health: int) -> dict[str, Any]:
    """Build the player payload returned to the dungeon UI."""
    character_data = character.to_dict()
    character_data['health'] = current_health
    return character_data


def _destroy_active_loot_and_encounter(character) -> None:
    """Delete active loot and the encounter after defeat or retreat."""
    destroy_loot_items(character)
    encounter = character.encounters[0] if character.encounters else None
    if encounter:
        db.session.delete(encounter)


def _resolve_encounter_state(encounter: Encounter) -> Combat:
    """Return the combat state for a populated encounter."""
    if encounter.combat:
        return encounter.combat
    raise RuntimeError('Combat state is missing')


def _scaled_enemy_stats(base_health: int, base_damage: int, enemy_level: int) -> tuple[int, int]:
    """Return the live health and damage values for a seeded enemy."""
    return base_health + (enemy_level * 10), base_damage + (enemy_level * 2)


def _resolve_attack_turn(character, encounter: Encounter) -> dict[str, Any]:
    """Resolve a single attack turn and return the resulting combat state."""
    enemy_name = encounter.enemy_name
    combat = _resolve_encounter_state(encounter)
    effective_damage = character.damage + character.bonus_damage
    player_hits = _combat_damage_roll(effective_damage)
    monster_hits = _combat_damage_roll(combat.enemy_damage)

    combat.enemy_current_health = max(0, combat.enemy_current_health - player_hits)

    if combat.enemy_current_health > 0:
        combat.character_health = max(0, combat.character_health - monster_hits)
        if check_character_death(combat.character_health):
            character.health = combat.character_health
            return {
                'message': (
                    'Defeat!\n'
                    f'You have been defeated by {enemy_name}!\n'
                    'You lost the loot from this dungeon run...'
                ),
                'victory': False,
                'items_dropped': [],
                'player_died': True,
                'encounter': encounter,
                'combat': combat,
                'character': _serialize_combat_character(character, combat.character_health),
            }

        return {
            'message': (
                f'You dealt {player_hits} damage to {enemy_name}!\n'
                f'{enemy_name} dealt {monster_hits} damage to you!'
            ),
            'victory': False,
            'items_dropped': [],
            'player_died': False,
            'encounter': encounter,
            'combat': combat,
            'character': _serialize_combat_character(character, combat.character_health),
        }

    message_lines = [
        'Victory!',
        f'You dealt {player_hits} damage and defeated the {enemy_name}!',
    ]
    items_dropped = drop_loot(encounter)
    if items_dropped:
        item_names = ', '.join(item['name'] for item in items_dropped)
        message_lines.append(f'You found {item_names}!')
        for item in items_dropped:
            add_inventory_item(character, item['id'], level=item['level'], is_loot=True)

    character.health = combat.character_health
    _apply_victory_experience(character, encounter, message_lines)

    db.session.delete(encounter)
    next_enemy_level = max(1, encounter.enemy_level + 1)
    next_encounter, next_combat = create_new_encounter(character, enemy_level=next_enemy_level)
    db.session.commit()

    return {
        'message': '\n'.join(message_lines),
        'victory': True,
        'items_dropped': items_dropped,
        'player_died': False,
        'encounter': next_encounter,
        'combat': next_combat,
        'character': character.to_dict(),
    }


def _resolve_run_turn(character, encounter: Encounter) -> dict[str, Any]:
    """Resolve a run attempt and return the resulting combat state."""
    enemy_name = encounter.enemy_name
    combat = _resolve_encounter_state(encounter)
    dice_roll = random.randint(1, 6)

    if dice_roll >= 4:
        character.health = combat.character_health
        db.session.delete(encounter)
        return {
            'message': f'You rolled a {dice_roll}! You successfully escaped and returned home!',
            'victory': False,
            'items_dropped': [],
            'player_died': False,
            'success': True,
            'damage': 0,
            'dice_roll': dice_roll,
            'encounter': encounter,
            'combat': combat,
            'character': character.to_dict(),
        }

    damage_taken = _combat_damage_roll(combat.enemy_damage)
    combat.character_health = max(0, combat.character_health - damage_taken)
    if check_character_death(combat.character_health):
        character.health = combat.character_health
        return {
            'message': (
                f'You rolled a {dice_roll} and failed to escape!\n'
                f'{enemy_name} dealt {damage_taken} damage! '
                'You lost the loot from this dungeon run and returned to the start...'
            ),
            'victory': False,
            'items_dropped': [],
            'player_died': True,
            'success': False,
            'damage': damage_taken,
            'dice_roll': dice_roll,
            'encounter': encounter,
            'combat': combat,
            'character': character.to_dict(),
        }

    return {
        'message': (
            f'You rolled a {dice_roll} and failed to escape!\n'
            f'{enemy_name} caught you and dealt {damage_taken} damage!'
        ),
        'victory': False,
        'items_dropped': [],
        'player_died': False,
        'success': False,
        'damage': damage_taken,
        'dice_roll': dice_roll,
        'encounter': encounter,
        'combat': combat,
        'character': _serialize_combat_character(character, combat.character_health),
    }


def _apply_victory_experience(character, encounter: Encounter, message_lines: list[str]) -> None:
    """Grant XP for a victory and append any level-up messages."""
    enemy_level = encounter.enemy_level if encounter.enemy_level else 1
    experience_gained = 20 + (enemy_level * 10)
    character.gain_experience(experience_gained)
    message_lines.append(f'You gained {experience_gained} XP!')

    leveled_up = False
    while character.level_up():
        leveled_up = True
        message_lines.append(f'You reached level {character.level}!')

    if leveled_up:
        message_lines.append(f'Next level at {character.experience_to_next_level} XP.')


def drop_loot(encounter: Encounter) -> list[dict[str, Any]]:
    """Create loot drops for a defeated encounter."""
    items_dropped: list[dict[str, Any]] = []
    all_items = get_all_item_type_data()
    if not all_items:
        return items_dropped

    monster_level = max(1, encounter.enemy_level or 1)
    num_items = min(3, 1 + max(0, (monster_level - 1) // 4))
    for _ in range(num_items):
        item_type = random.choice(all_items)
        items_dropped.append(
            {
                **item_type,
                'level': max(1, monster_level + random.choice([-1, 0, 0, 1])),
            }
        )

    return items_dropped


def build_combat_response(outcome: dict[str, Any]) -> Any:
    """Build the JSON payload returned by combat endpoints."""
    character = outcome['character']
    encounter = outcome['encounter']
    combat = outcome['combat']
    payload: dict[str, Any] = {
        'character': character,
        'encounter': (
            None
            if outcome['player_died']
            or outcome.get('success', False)
            or encounter is None
            else encounter.to_dict()
        ),
        'combat': (
            None
            if outcome['player_died']
            or outcome.get('success', False)
            or combat is None
            else combat.to_dict()
        ),
        'message': outcome['message'],
        'victory': outcome['victory'],
        'items_dropped': outcome['items_dropped'],
        'player_died': outcome['player_died'],
        'success': outcome.get('success', False),
    }

    if outcome.get('dice_roll') is not None:
        payload['dice_roll'] = outcome['dice_roll']
    if outcome.get('success', False):
        payload['damage'] = outcome.get('damage', 0)

    return jsonify(payload)


class CombatResource(Resource):
    """Resolve a single combat action."""

    def post(self, combat: Combat, action: str):
        """Resolve a combat action for the requested combat row."""
        character = combat.character
        if not character:
            return json_error('Character not found', 404)

        encounter = combat.encounter
        if not encounter:
            return json_error('Encounter not found', 404)

        action_name = (action or '').lower().strip()
        if action_name == 'attack':
            outcome = _resolve_attack_turn(character, encounter)
        elif action_name == 'run':
            outcome = _resolve_run_turn(character, encounter)
        else:
            return json_error('Invalid combat action', 400)

        if outcome['player_died']:
            _destroy_active_loot_and_encounter(character)
        elif outcome['victory']:
            character.health = outcome['character']['health']
        elif outcome.get('success', False):
            clear_loot_flags(character)
        else:
            character.health = outcome['character']['health']

        db.session.commit()
        if outcome['victory'] or outcome['player_died'] or outcome.get('success', False):
            invalidate_user_inventory_cache(character.user_id)
            invalidate_user_characters_cache(character.user_id, [character.id])

        return build_combat_response(outcome)


def register_combat_resources(api):
    """Register combat routes on the provided API instance."""
    api.add_resource(CombatResource, '/combats/<combat:combat>/<string:action>')
