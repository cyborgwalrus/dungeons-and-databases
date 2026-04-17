import random
from typing import Any

from flask import Blueprint, jsonify

from ..game_utils import get_player
from ..db.models import Character, Encounter, EnemyType, ItemType, db
from ..serializers import serialize_character, serialize_encounter, serialize_item_type
from .common import get_character

dungeon_bp = Blueprint('dungeon', __name__)


def _combat_damage_roll(max_damage: int) -> int:
    return random.randint(max(1, max_damage // 2), max(1, max_damage))


def _get_or_create_encounter(character: Character) -> Encounter | None:
    encounter = Encounter.query.filter_by(character_id=character.id).first()
    if encounter:
        return encounter
    return create_new_encounter(character)


def create_new_encounter(character: Character | None = None) -> Encounter | None:
    character = character or get_player()
    if character is None:
        return None

    Encounter.query.filter_by(character_id=character.id).delete()

    enemy_type = EnemyType.query.order_by(db.func.random()).first()
    if not enemy_type:
        return None

    enemy_health = enemy_type.base_health + (character.level * 10)
    enemy_damage = enemy_type.base_damage + (character.level * 2)

    encounter = Encounter(
        character_id=character.id,
        enemy_type_id=enemy_type.id,
        enemy_health=enemy_health,
        enemy_damage=enemy_damage,
    )
    db.session.add(encounter)
    db.session.commit()
    return encounter


def check_player_death(character: Character) -> bool:
    if character.health <= 0:
        Encounter.query.filter_by(character_id=character.id).delete()
        return True
    return False


def drop_loot() -> list[dict[str, Any]]:
    items_dropped: list[dict[str, Any]] = []
    all_items = ItemType.query.all()
    if not all_items:
        return items_dropped

    num_items = random.randint(1, min(3, len(all_items)))
    for _ in range(num_items):
        item_type = serialize_item_type(random.choice(all_items))
        if item_type is not None:
            items_dropped.append(item_type)

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
    payload: dict[str, Any] = {
        'player': serialize_character(character),
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
    enemy_name = encounter.enemy_type.name
    effective_damage = character.damage + character.bonus_damage
    player_hits = _combat_damage_roll(effective_damage)
    monster_hits = _combat_damage_roll(encounter.enemy_damage)

    encounter.enemy_health = max(0, encounter.enemy_health - player_hits)

    if encounter.enemy_health > 0:
        character.health = max(0, character.health - monster_hits)
        if check_player_death(character):
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
    items_dropped = drop_loot()
    if items_dropped:
        item_names = ', '.join(item['name'] for item in items_dropped)
        message_lines.append(f'You found {item_names}!')

    if random.random() < 0.4:
        character.level += 1
        character.damage += 3
        character.health = min(character.health + 20, 100 + (character.level * 10) + character.bonus_health)
        message_lines.append('You leveled up!')

    db.session.delete(encounter)
    db.session.commit()
    next_encounter = create_new_encounter(character)

    return {
        'message': '\n'.join(message_lines),
        'victory': True,
        'items_dropped': items_dropped,
        'player_died': False,
        'encounter': next_encounter,
    }


def _resolve_run_turn(character: Character, encounter: Encounter) -> dict[str, Any]:
    enemy_name = encounter.enemy_type.name
    dice_roll = random.randint(1, 6)

    if dice_roll >= 5:
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

    damage_taken = _combat_damage_roll(encounter.enemy_damage)
    character.health = max(0, character.health - damage_taken)
    if check_player_death(character):
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


@dungeon_bp.route('/dungeon/encounters/', methods=['GET'])
def get_encounter(character_id: int | None = None):
    character = get_character(character_id)
    encounter = _get_or_create_encounter(character)
    if not encounter:
        return jsonify({'error': 'No encounters available'}), 404
    return jsonify(serialize_encounter(encounter))


@dungeon_bp.route('/dungeon/encounters/', methods=['POST'])
def create_encounter(character_id: int | None = None):
    character = get_character(character_id)
    encounter = create_new_encounter(character)
    if not encounter:
        return jsonify({'error': 'No enemy types available'}), 404
    return jsonify(serialize_encounter(encounter)), 201


@dungeon_bp.route('/dungeon/encounters/<int:encounter_id>', methods=['GET'])
def get_encounter_by_id(encounter_id: int):
    encounter = Encounter.query.get(encounter_id)
    if not encounter:
        return jsonify({'error': 'Encounter not found'}), 404
    return jsonify(serialize_encounter(encounter))


@dungeon_bp.route('/dungeon/encounters/<int:encounter_id>', methods=['DELETE'])
def delete_encounter(encounter_id: int):
    encounter = Encounter.query.get(encounter_id)
    if not encounter:
        return jsonify({'error': 'Encounter not found'}), 404
    db.session.delete(encounter)
    db.session.commit()
    return jsonify({'message': 'Encounter deleted'})


@dungeon_bp.route('/dungeon/encounters/<int:character_id>/current', methods=['GET'])
def get_current_character_encounter(character_id: int):
    encounter = _get_or_create_encounter(get_character(character_id))
    return jsonify(serialize_encounter(encounter))


@dungeon_bp.route('/dungeon/attack', methods=['POST'])
def attack_monster() -> Any:
    character = get_character()
    encounter = _get_or_create_encounter(character)
    if not encounter:
        return jsonify({'error': 'No enemy available'}), 404
    outcome = _resolve_attack_turn(character, encounter)
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
    character = get_character()
    encounter = _get_or_create_encounter(character)
    if not encounter:
        return jsonify({'error': 'No enemy available'}), 404
    outcome = _resolve_run_turn(character, encounter)
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