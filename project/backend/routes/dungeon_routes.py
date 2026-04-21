import random
from typing import Any

from flask import Blueprint, jsonify

from ..db.cache_helpers import get_all_enemy_type_data, get_all_item_type_data
from ..utils.serializers import serialize_character, serialize_encounter
from ..utils.game_utils import add_inventory_item, clear_loot_flags, destroy_loot_items, get_player
from ..db.models import Character, Encounter, db
from .common import get_character, json_error

dungeon_bp = Blueprint('dungeon', __name__)


def _combat_damage_roll(max_damage: int) -> int:
    """Roll a bounded combat damage value for one turn."""
    return random.randint(max(1, max_damage // 2), max(1, max_damage))


def _get_or_create_encounter(character: Character) -> Encounter | None:
    """Return the active encounter for a character or create a new one."""
    encounter = Encounter.query.filter_by(character_id=character.id).first()
    if encounter:
        return encounter
    return create_new_encounter(character)


def _get_active_encounter(character: Character) -> Encounter | None:
    """Return the current active encounter for a character, if present."""
    return Encounter.query.filter_by(character_id=character.id).first()


def create_new_encounter(character: Character | None = None) -> Encounter | None:
    """Create a fresh encounter for the current player."""
    character = character or get_player()
    if character is None:
        return None

    Encounter.query.filter_by(character_id=character.id).delete()

    enemy_types = get_all_enemy_type_data()
    enemy_type = random.choice(enemy_types) if enemy_types else None
    if not enemy_type:
        return None

    enemy_level = 1
    enemy_health = enemy_type['health'] + (enemy_level * 10)
    enemy_damage = enemy_type['damage'] + (enemy_level * 2)

    encounter = Encounter(
        character_id=character.id,
        enemy_type_id=enemy_type['id'],
        enemy_level=enemy_level,
        max_health=enemy_health,
        health=enemy_health,
        damage=enemy_damage,
    )
    db.session.add(encounter)
    db.session.commit()
    return encounter


def _experience_reward_for_enemy(encounter: Encounter) -> int:
    """Calculate the XP reward for defeating the current enemy."""
    enemy_level = encounter.enemy_level if encounter.enemy_level else 1
    return 20 + (enemy_level * 10)


def _enemy_level_step(character: Character) -> int:
    """Return the enemy level increment based on the character's level."""
    return 1 + max(0, (character.level - 1) // 3)


def _next_enemy_level(character: Character, encounter: Encounter) -> int:
    """Calculate the next encounter's enemy level."""
    return encounter.enemy_level + _enemy_level_step(character)


def _apply_victory_experience(character: Character, encounter: Encounter, message_lines: list[str]) -> None:
    """Grant XP for a victory and append any level-up messages."""
    experience_gained = _experience_reward_for_enemy(encounter)
    character.gain_experience(experience_gained)
    message_lines.append(f'You gained {experience_gained} XP!')

    leveled_up = False
    while character.level_up():
        leveled_up = True
        message_lines.append(f'You reached level {character.level}!')

    if leveled_up:
        message_lines.append(f'Next level at {character.experience_to_next_level} XP.')


def _create_next_encounter(character: Character, encounter: Encounter) -> Encounter | None:
    """Generate the next encounter after a win using the scaled enemy level."""
    # New encounters inherit the character's progress so dungeon runs ramp up over time.
    next_enemy_level = _next_enemy_level(character, encounter)
    enemy_types = get_all_enemy_type_data()
    enemy_type = random.choice(enemy_types) if enemy_types else None
    if not enemy_type:
        return None

    enemy_health = enemy_type['health'] + (next_enemy_level * 10)
    enemy_damage = enemy_type['damage'] + (next_enemy_level * 2)

    next_encounter = Encounter(
        character_id=character.id,
        enemy_type_id=enemy_type['id'],
        enemy_level=next_enemy_level,
        max_health=enemy_health,
        health=enemy_health,
        damage=enemy_damage,
    )
    db.session.add(next_encounter)
    return next_encounter


def check_character_death(character: Character) -> bool:
    """Return whether the character has died."""
    return character.health <= 0


def _remove_active_encounter(character: Character) -> None:
    """Delete the active encounter for the character."""
    Encounter.query.filter_by(character_id=character.id).delete()


def _finalize_loot(character: Character) -> None:
    """Mark remaining loot as safe to keep after a successful escape."""
    clear_loot_flags(character)


def _destroy_active_loot_and_encounter(character: Character) -> None:
    """Delete active loot and the encounter after defeat or retreat."""
    destroy_loot_items(character)
    _remove_active_encounter(character)


def _loot_item_level(monster_level: int) -> int:
    """Roll the item level for dropped loot around the monster's level."""
    return max(1, monster_level + random.choice([-1, 0, 0, 1]))


def drop_loot(encounter: Encounter) -> list[dict[str, Any]]:
    """Create loot drops for a defeated encounter."""
    items_dropped: list[dict[str, Any]] = []
    all_items = get_all_item_type_data()
    if not all_items:
        return items_dropped

    # Loot scales from the enemy's level, not the enemy type, so harder fights pay out better gear.
    monster_level = max(1, encounter.enemy_level or 1)
    num_items = min(3, 1 + max(0, (monster_level - 1) // 4))
    for _ in range(num_items):
        item_type = random.choice(all_items)
        items_dropped.append(
            {
                **item_type,
                'level': _loot_item_level(monster_level),
            }
        )

    return items_dropped


def build_combat_response(
    character: Character,
    encounter: Encounter | None,
    message: str,
    *,
    victory: bool,
    items_dropped: list[dict[str, Any]],
    player_died: bool,
    success: bool = False,
    damage: int = 0,
    dice_roll: int | None = None,
) -> Any:
    """Build the JSON payload returned by dungeon combat endpoints."""
    payload: dict[str, Any] = {
        'character': serialize_character(character),
        'enemy': None if player_died or success else serialize_encounter(encounter),
        'message': message,
        'victory': victory,
        'items_dropped': items_dropped,
        'player_died': player_died,
        'success': success,
    }

    if dice_roll is not None:
        payload['dice_roll'] = dice_roll
    if success:
        payload['damage'] = damage

    return jsonify(payload)


def _resolve_attack_turn(character: Character, encounter: Encounter) -> dict[str, Any]:
    """Resolve a single attack turn and return the resulting combat state."""
    enemy_name = encounter.enemy_type.name
    effective_damage = character.damage + character.bonus_damage
    player_hits = _combat_damage_roll(effective_damage)
    monster_hits = _combat_damage_roll(encounter.damage)

    encounter.health = max(0, encounter.health - player_hits)

    if encounter.health > 0:
        character.health = max(0, character.health - monster_hits)
        if check_character_death(character):
            return {
                'message': (
                    'Defeat!\n'
                    f'You have been defeated by {enemy_name} and lost the loot from this dungeon run...'
                ),
                'victory': False,
                'items_dropped': [],
                'player_died': True,
                'encounter': encounter,
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

    _apply_victory_experience(character, encounter, message_lines)

    _remove_active_encounter(character)
    next_encounter = _create_next_encounter(character, encounter)
    db.session.commit()

    return {
        'message': '\n'.join(message_lines),
        'victory': True,
        'items_dropped': items_dropped,
        'player_died': False,
        'encounter': next_encounter,
    }


def _resolve_run_turn(character: Character, encounter: Encounter) -> dict[str, Any]:
    """Resolve a run attempt and return the resulting combat state."""
    enemy_name = encounter.enemy_type.name
    dice_roll = random.randint(1, 6)

    if dice_roll >= 4:
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
        }

    damage_taken = _combat_damage_roll(encounter.damage)
    character.health = max(0, character.health - damage_taken)
    if check_character_death(character):
        return {
            'message': (
                f'You rolled a {dice_roll} and failed to escape. '
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
        }

    return {
        'message': (
            f'You rolled a {dice_roll}! Failed to escape! '
            f'{enemy_name} caught you and dealt {damage_taken} damage!'
        ),
        'victory': False,
        'items_dropped': [],
        'player_died': False,
        'success': False,
        'damage': damage_taken,
        'dice_roll': dice_roll,
        'encounter': encounter,
    }


@dungeon_bp.route('/dungeon/enter', methods=['POST'])
def enter_dungeon() -> Any:
    """Enter the dungeon and return the active encounter."""
    character = get_character()
    if not character:
        return json_error('No active character selected', 400)
    encounter = _get_or_create_encounter(character)
    if not encounter:
        return jsonify({'error': 'No enemy types available'}), 404
    return jsonify(serialize_encounter(encounter))


@dungeon_bp.route('/dungeon/attack', methods=['POST'])
def attack_monster() -> Any:
    """Attack the current dungeon enemy."""
    character = get_character()
    if not character:
        return json_error('No active character selected', 400)
    encounter = _get_active_encounter(character)
    if not encounter:
        return json_error('No active encounter. Enter the dungeon first', 400)
    outcome = _resolve_attack_turn(character, encounter)
    if outcome['player_died']:
        _destroy_active_loot_and_encounter(character)
    db.session.commit()

    return build_combat_response(
        character,
        outcome['encounter'],
        outcome['message'],
        victory=outcome['victory'],
        items_dropped=outcome['items_dropped'],
        player_died=outcome['player_died'],
    )


@dungeon_bp.route('/dungeon/run', methods=['POST'])
def run_away() -> Any:
    """Attempt to flee from the current dungeon encounter."""
    character = get_character()
    if not character:
        return json_error('No active character selected', 400)
    encounter = _get_active_encounter(character)
    if not encounter:
        return json_error('No active encounter. Enter the dungeon first', 400)
    outcome = _resolve_run_turn(character, encounter)
    if outcome['player_died']:
        _destroy_active_loot_and_encounter(character)
    elif outcome['success']:
        _finalize_loot(character)
    db.session.commit()
    return build_combat_response(
        character,
        outcome['encounter'],
        outcome['message'],
        victory=outcome['victory'],
        items_dropped=outcome['items_dropped'],
        player_died=outcome['player_died'],
        success=outcome['success'],
        damage=outcome['damage'],
        dice_roll=outcome['dice_roll'],
    )


@dungeon_bp.route('/dungeon/leave', methods=['POST'])
def leave_dungeon() -> Any:
    """Leave the dungeon and clean up the active encounter state."""
    character = get_character()
    if not character:
        return json_error('No active character selected', 400)

    _destroy_active_loot_and_encounter(character)
    db.session.commit()
    return jsonify({'message': 'You left the dungeon'})