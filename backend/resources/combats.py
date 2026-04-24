"""Combat resources for resolving dungeon encounters."""

import random
from typing import Any

from flask import jsonify
from flask_restful import Resource
from sqlalchemy import delete

from backend.db.models import Combat
from backend.db.session import db
from backend.utils.game_utils import get_enemy_types, get_player
from backend.utils.api_response_cache import (
    invalidate_user_characters_cache,
    invalidate_user_inventory_cache,
)
from backend.utils.game_utils import add_inventory_item, get_item_types
from backend.utils.route_helpers import json_error, require_current_character


def _scaled_enemy_stats(base_health: int, base_damage: int, level: int) -> tuple[int, int]:
    """Return the live health and damage values for a seeded enemy."""
    return base_health + (level * 10), base_damage + (level * 2)


def create_new_combat(
    character=None,
    *,
    level: int = 1,
) -> Combat | None:
    """Create a fresh combat row for the current player."""
    character = character or get_player()
    if character is None:
        return None

    assert character.id is not None

    db.session.execute(delete(Combat).where(Combat.character_id == character.id))
    db.session.flush()

    enemy_types_data = get_enemy_types()
    enemy_type = random.choice(enemy_types_data) if enemy_types_data else None
    if not enemy_type:
        db.session.rollback()
        return None

    level = max(1, int(level))
    enemy_health, enemy_damage = _scaled_enemy_stats(
        enemy_type['base_health'],
        enemy_type['base_damage'],
        level,
    )

    combat = Combat(
        character_id=character.id,
        enemy_type_id=enemy_type['id'],
        enemy_level=level,
        character_health=character.health,
        enemy_current_health=enemy_health,
        enemy_max_health=enemy_health,
        enemy_damage=enemy_damage,
    )
    db.session.add(combat)
    db.session.commit()
    return combat


def _combat_damage_roll(max_damage: int) -> int:
    """Roll a bounded combat damage value for one turn."""
    return random.randint(max(1, max_damage // 2), max(1, max_damage))


class MessageBuilder:
    """Build combat outcome messages."""

    @staticmethod
    def victory(enemy_name: str, player_hits: int) -> list[str]:
        """Build the opening victory message for a defeated enemy."""
        return [
            'Victory!',
            f'You dealt {player_hits} damage and defeated the {enemy_name}!',
        ]

    @staticmethod
    def attack_round(enemy_name: str, player_hits: int, monster_hits: int) -> str:
        """Build the message for an attack round where combat continues."""
        return (
            f'You dealt {player_hits} damage to {enemy_name}!\n'
            f'{enemy_name} dealt {monster_hits} damage to you!'
        )

    @staticmethod
    def defeat(enemy_name: str) -> str:
        """Build the message for a defeated attack round."""
        return (
            'Defeat!\n'
            f'You have been defeated by {enemy_name}!\n'
            'You lost the loot from this dungeon run...'
        )

    @staticmethod
    def escape_success(dice_roll: int) -> str:
        """Build the message for a successful escape."""
        return f'You rolled a {dice_roll}! You successfully escaped and returned home!'

    @staticmethod
    def escape_failure(dice_roll: int, enemy_name: str, damage_taken: int, defeated: bool) -> str:
        """Build the message for a failed escape attempt."""
        if defeated:
            return (
                f'You rolled a {dice_roll} and failed to escape!\n'
                f'{enemy_name} dealt {damage_taken} damage! '
                'You lost the loot from this dungeon run and returned to the start...'
            )

        return (
            f'You rolled a {dice_roll} and failed to escape!\n'
            f'{enemy_name} caught you and dealt {damage_taken} damage!'
        )


def _victory_outcome(character, combat: Combat, player_hits: int) -> tuple[list[str], list[dict[str, Any]]]:
    """Build the complete victory message list and loot drops for a combat round."""
    message_lines = MessageBuilder.victory(combat.enemy_name, player_hits)

    items_dropped = drop_loot(combat)
    if items_dropped:
        item_names = ', '.join(item['name'] for item in items_dropped)
        message_lines.append(f'You found {item_names}!')
        for item in items_dropped:
            add_inventory_item(character, item['id'], level=item['level'])

    _apply_victory_experience(character, combat, message_lines)
    return message_lines, items_dropped


def check_character_death(health: int) -> bool:
    """Return whether the character has died."""
    return health <= 0


def _resolve_attack_turn(character, combat: Combat) -> dict[str, Any]:
    """Resolve a single attack turn and return the resulting combat state."""
    enemy_name = combat.enemy_name

    if combat.enemy_current_health <= 0:
        return {
            'message': 'You need to go deeper to face the next enemy.',
            'victory': False,
            'items_dropped': [],
            'player_died': False,
            'combat': combat,
            'character': character.to_response(health=combat.character_health).model_dump(),
        }

    effective_damage = character.damage + character.bonus_damage
    player_hits = _combat_damage_roll(effective_damage)
    monster_hits = _combat_damage_roll(combat.enemy_damage)

    combat.enemy_current_health = max(0, combat.enemy_current_health - player_hits)

    if combat.enemy_current_health > 0:
        combat.character_health = max(0, combat.character_health - monster_hits)
        if check_character_death(combat.character_health):
            character.health = combat.character_health
            return {
                'message': MessageBuilder.defeat(enemy_name),
                'victory': False,
                'items_dropped': [],
                'player_died': True,
                'combat': combat,
                'character': character.to_response(health=combat.character_health).model_dump(),
            }

        return {
            'message': MessageBuilder.attack_round(enemy_name, player_hits, monster_hits),
            'victory': False,
            'items_dropped': [],
            'player_died': False,
            'combat': combat,
            'character': character.to_response(health=combat.character_health).model_dump(),
        }

    character.health = combat.character_health
    message_lines, items_dropped = _victory_outcome(character, combat, player_hits)

    return {
        'message': '\n'.join(message_lines),
        'victory': True,
        'items_dropped': items_dropped,
        'player_died': False,
        'combat': combat,
        'character': character.to_response().model_dump(),
    }


def _resolve_deeper_turn(character, combat: Combat) -> dict[str, Any]:
    """Delete the cleared combat and generate the next dungeon fight."""
    enemy_name = combat.enemy_name
    if combat.enemy_current_health > 0:
        return {
            'message': 'You can only go deeper after defeating the enemy.',
            'victory': False,
            'items_dropped': [],
            'player_died': False,
            'combat': combat,
            'character': character.to_response(health=combat.character_health).model_dump(),
        }

    character.health = combat.character_health
    next_level = max(1, combat.enemy_level + 1)
    db.session.delete(combat)
    next_combat = create_new_combat(character, level=next_level)
    if not next_combat:
        return {
            'message': 'No enemy types available',
            'victory': False,
            'items_dropped': [],
            'player_died': False,
            'combat': None,
            'character': character.to_response(health=character.health).model_dump(),
        }

    return {
        'message': (
            'Sneaking!\n'
            f'You go deeper past the defeated {enemy_name}!\n'
            'A new enemy emerges from the shadows!'
        ),
        'victory': False,
        'items_dropped': [],
        'player_died': False,
        'combat': next_combat,
        'character': character.to_response(health=combat.character_health).model_dump(),
    }


def _resolve_home_turn(character, combat: Combat) -> dict[str, Any]:
    """Resolve a go-home action after a victory."""
    character.health = combat.character_health
    db.session.delete(combat)

    return {
        'message': 'You returned home with your spoils!',
        'victory': False,
        'items_dropped': [],
        'player_died': False,
        'success': True,
        'damage': 0,
        'combat': combat,
        'character': character.to_response().model_dump(),
    }


def _resolve_run_turn(character, combat: Combat) -> dict[str, Any]:
    """Resolve a run attempt and return the resulting combat state."""
    enemy_name = combat.enemy_name
    dice_roll = random.randint(1, 6)

    if dice_roll >= 4:
        character.health = combat.character_health
        db.session.delete(combat)
        return {
            'message': MessageBuilder.escape_success(dice_roll),
            'victory': False,
            'items_dropped': [],
            'player_died': False,
            'success': True,
            'damage': 0,
            'dice_roll': dice_roll,
            'combat': combat,
            'character': character.to_response().model_dump(),
        }

    damage_taken = _combat_damage_roll(combat.enemy_damage)
    combat.character_health = max(0, combat.character_health - damage_taken)
    if check_character_death(combat.character_health):
        character.health = combat.character_health
        return {
            'message': MessageBuilder.escape_failure(dice_roll, enemy_name, damage_taken, True),
            'victory': False,
            'items_dropped': [],
            'player_died': True,
            'success': False,
            'damage': damage_taken,
            'dice_roll': dice_roll,
            'combat': combat,
            'character': character.to_response().model_dump(),
        }

    return {
        'message': MessageBuilder.escape_failure(dice_roll, enemy_name, damage_taken, False),
        'victory': False,
        'items_dropped': [],
        'player_died': False,
        'success': False,
        'damage': damage_taken,
        'dice_roll': dice_roll,
        'combat': combat,
        'character': character.to_response(health=combat.character_health).model_dump(),
    }


def _apply_victory_experience(character, combat: Combat, message_lines: list[str]) -> None:
    """Grant XP for a victory and append any level-up messages."""
    experience_gained = 20 + (max(1, combat.enemy_level) * 10)
    character.gain_experience(experience_gained)
    message_lines.append(f'You gained {experience_gained} XP!')

    leveled_up = False
    while character.level_up():
        leveled_up = True
        message_lines.append(f'You reached level {character.level}!')

    if leveled_up:
        message_lines.append(f'Next level at {character.experience_to_next_level} XP.')


def drop_loot(combat: Combat) -> list[dict[str, Any]]:
    """Create loot drops for a defeated encounter."""
    items_dropped: list[dict[str, Any]] = []
    all_items = get_item_types()
    if not all_items:
        return items_dropped

    monster_level = max(1, combat.enemy_level or 1)
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
    combat = outcome['combat']
    payload: dict[str, Any] = {
        'character': character,
        'combat': (
            None
            if outcome['player_died']
            or outcome.get('success', False)
            or combat is None
            else combat.to_response().model_dump()
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

    def post(self, combat: Combat | None = None, action: str | None = None):
        """Create a new combat row for the current character."""
        if combat is not None or action is not None:
            return json_error('Invalid combat action', 400)

        character, error_response = require_current_character()
        if error_response:
            return error_response

        assert character is not None

        combat = create_new_combat(character)
        if not combat:
            return json_error('No enemy types available', 404)

        return {
            'combat': combat.to_response().model_dump(),
            'character': character.to_response().model_dump(),
        }, 201

    def get(self, combat: Combat, action: str | None = None):
        """Return combat state or resolve a combat action for the requested row."""
        if action is None:
            return combat.to_response().model_dump()

        character = combat.character
        if not character:
            return json_error('Character not found', 404)

        action_name = (action or '').lower().strip()
        if action_name == 'attack':
            outcome = _resolve_attack_turn(character, combat)
        elif action_name == 'deeper':
            outcome = _resolve_deeper_turn(character, combat)
        elif action_name == 'run':
            outcome = _resolve_run_turn(character, combat)
        elif action_name == 'home':
            if combat.enemy_current_health > 0:
                return json_error('You can only go home after defeating the enemy', 400)
            outcome = _resolve_home_turn(character, combat)
        else:
            return json_error('Invalid combat action', 400)

        if outcome['player_died']:
            db.session.delete(combat)
        elif outcome['victory']:
            character.health = outcome['character']['health']
        else:
            character.health = outcome['character']['health']

        db.session.commit()
        character_ids = [character.id] if character.id is not None else None
        invalidate_user_characters_cache(character.user_id, character_ids)
        if outcome['victory']:
            invalidate_user_inventory_cache(character.user_id)

        return build_combat_response(outcome)


def register_combat_resources(api):
    """Register combat routes on the provided API instance."""
    api.add_resource(
        CombatResource,
        '/combats',
        '/combats/<combat:combat>',
        '/combats/<combat:combat>/<string:action>',
    )
