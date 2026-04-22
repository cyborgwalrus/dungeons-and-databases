import random
from typing import Any

from flask import Blueprint, jsonify

from backend.db.cache_helpers import get_all_enemy_type_data, get_all_item_type_data
from backend.db.models import Character, Encounter, EncounterState, db
from backend.utils.game_utils import add_inventory_item, clear_loot_flags, destroy_loot_items, get_player
from backend.utils.route_helpers import get_character, json_error
from backend.utils.api_response_cache import invalidate_user_characters_cache, invalidate_user_inventory_cache

dungeon_bp = Blueprint('dungeon', __name__)


def _combat_damage_roll(max_damage: int) -> int:
    """Roll a bounded combat damage value for one turn."""
    return random.randint(max(1, max_damage // 2), max(1, max_damage))


def _get_or_create_encounter_state(character: Character, encounter: Encounter) -> EncounterState:
    """Return the live combat state for the current encounter, creating it if needed."""
    encounter_state = encounter.state
    if encounter_state:
        return encounter_state

    encounter_state = EncounterState(
        encounter=encounter,
        character_id=character.id,
        player_health=character.health,
        enemy_health=0,
        enemy_max_health=0,
        enemy_damage=0,
    )
    db.session.add(encounter_state)
    return encounter_state


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

    existing_encounter = Encounter.query.filter_by(character_id=character.id).first()
    if existing_encounter:
        db.session.delete(existing_encounter)

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
    )
    db.session.add(encounter)
    db.session.flush()
    db.session.add(
        EncounterState(
            encounter=encounter,
            character_id=character.id,
            player_health=character.health,
            enemy_health=enemy_health,
            enemy_max_health=enemy_health,
            enemy_damage=enemy_damage,
        )
    )
    db.session.commit()
    return encounter


def _next_enemy_level(character: Character, encounter: Encounter) -> int:
    """Calculate the next encounter's enemy level."""
    return encounter.enemy_level + (1 + max(0, (character.level - 1) // 3))


def _apply_victory_experience(character: Character, encounter: Encounter, message_lines: list[str]) -> None:
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
    )
    db.session.add(next_encounter)
    db.session.flush()
    db.session.add(
        EncounterState(
            encounter=next_encounter,
            character_id=character.id,
            player_health=character.health,
            enemy_health=enemy_health,
            enemy_max_health=enemy_health,
            enemy_damage=enemy_damage,
        )
    )
    return next_encounter


def check_character_death(health: int) -> bool:
    """Return whether the character has died."""
    return health <= 0


def _destroy_active_loot_and_encounter(character: Character) -> None:
    """Delete active loot and the encounter after defeat or retreat."""
    destroy_loot_items(character)
    encounter = _get_active_encounter(character)
    if encounter:
        db.session.delete(encounter)


def _serialize_combat_character(character: Character, current_health: int) -> dict[str, Any]:
    """Build the player payload returned to the dungeon UI."""
    character_data = character.to_dict()
    character_data['health'] = current_health
    return character_data


def _resolve_encounter_state(encounter: Encounter) -> EncounterState:
    """Return the encounter state for a populated encounter."""
    if encounter.state:
        return encounter.state
    raise RuntimeError('Encounter state is missing')


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
                'level': max(1, monster_level + random.choice([-1, 0, 0, 1])),
            }
        )

    return items_dropped


def build_combat_response(
    character: dict[str, Any],
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
        'character': character,
        'enemy': None if player_died or success or encounter is None else encounter.to_dict(),
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
    encounter_state = _resolve_encounter_state(encounter)
    effective_damage = character.damage + character.bonus_damage
    player_hits = _combat_damage_roll(effective_damage)
    monster_hits = _combat_damage_roll(encounter_state.enemy_damage)

    encounter_state.enemy_health = max(0, encounter_state.enemy_health - player_hits)

    if encounter_state.enemy_health > 0:
        encounter_state.player_health = max(0, encounter_state.player_health - monster_hits)
        if check_character_death(encounter_state.player_health):
            character.health = encounter_state.player_health
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
                'character': _serialize_combat_character(character, encounter_state.player_health),
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
            'character': _serialize_combat_character(character, encounter_state.player_health),
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

    character.health = encounter_state.player_health
    _apply_victory_experience(character, encounter, message_lines)

    db.session.delete(encounter)
    next_encounter = _create_next_encounter(character, encounter)
    db.session.commit()

    return {
        'message': '\n'.join(message_lines),
        'victory': True,
        'items_dropped': items_dropped,
        'player_died': False,
        'encounter': next_encounter,
        'character': character.to_dict(),
    }


def _resolve_run_turn(character: Character, encounter: Encounter) -> dict[str, Any]:
    """Resolve a run attempt and return the resulting combat state."""
    enemy_name = encounter.enemy_type.name
    encounter_state = _resolve_encounter_state(encounter)
    dice_roll = random.randint(1, 6)

    if dice_roll >= 4:
        character.health = encounter_state.player_health
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
            'character': character.to_dict(),
        }

    damage_taken = _combat_damage_roll(encounter_state.enemy_damage)
    encounter_state.player_health = max(0, encounter_state.player_health - damage_taken)
    if check_character_death(encounter_state.player_health):
        character.health = encounter_state.player_health
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
        'character': _serialize_combat_character(character, encounter_state.player_health),
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
    return jsonify(encounter.to_dict())


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
    elif outcome['victory']:
        character.health = outcome['character']['health']
    db.session.commit()
    if outcome['victory'] or outcome['player_died']:
        invalidate_user_inventory_cache(character.user_id)
        invalidate_user_characters_cache(character.user_id, [character.id])

    return build_combat_response(
        outcome['character'],
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
        clear_loot_flags(character)
    else:
        character.health = outcome['character']['health']
    db.session.commit()
    if outcome['success'] or outcome['player_died']:
        invalidate_user_inventory_cache(character.user_id)
        invalidate_user_characters_cache(character.user_id, [character.id])
    return build_combat_response(
        outcome['character'],
        outcome['encounter'],
        outcome['message'],
        victory=outcome['victory'],
        items_dropped=outcome['items_dropped'],
        player_died=outcome['player_died'],
        success=outcome['success'],
        damage=outcome['damage'],
        dice_roll=outcome['dice_roll'],
    )