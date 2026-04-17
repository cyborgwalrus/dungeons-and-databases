from flask import Blueprint, jsonify, request, session

from ..game_utils import add_inventory_item, get_player as get_current_character, seed_character_loadout, set_player
from ..db.models import Character, ItemType, User, db
from ..serializers import serialize_character
from .common import get_character as get_character_by_id, get_current_user, json_error

character_bp = Blueprint('character', __name__)


def _get_character(character_id: int | None = None) -> tuple[Character | None, tuple[dict[str, str], int] | None]:
    if character_id is not None:
        character = get_character_by_id(character_id)
        if character:
            return character, None
        return None, json_error('Character not found', 404)

    character = get_current_character()
    if character is not None:
        return character, None

    return None, json_error('No active character selected', 400)


@character_bp.route('/characters/', methods=['GET'])
def list_characters():
    user = get_current_user()
    characters = user.characters if user else []
    return jsonify([serialize_character(character, include_inventory=True) for character in characters])


@character_bp.route('/characters/', methods=['POST'])
def create_character():
    data = request.get_json(silent=True) or {}
    user = get_current_user()

    user_id = data.get('user_id', user.id if user else None)
    if user_id is None:
        return jsonify({'error': 'user_id is required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    character = Character(
        user_id=user.id,
        name=(data.get('name') or 'Hero').strip(),
        level=int(data.get('level', 1)),
        health=int(data.get('health', 100)),
        damage=int(data.get('damage', 10)),
    )
    db.session.add(character)
    db.session.flush()
    seed_character_loadout(character)
    db.session.commit()
    return jsonify(serialize_character(character, include_inventory=True)), 201


@character_bp.route('/characters/<int:character_id>', methods=['GET'])
def get_character(character_id):
    character = Character.query.get(character_id)
    if not character:
        return jsonify({'error': 'Character not found'}), 404
    return jsonify(serialize_character(character, include_inventory=True))


@character_bp.route('/characters/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    character = Character.query.get(character_id)
    if not character:
        return jsonify({'error': 'Character not found'}), 404

    if session.get('character_id') == character.id:
        set_player(None)

    db.session.delete(character)
    db.session.commit()
    return jsonify({'message': 'Character deleted'})


@character_bp.route('/characters/<int:character_id>/select', methods=['POST'])
def select_character(character_id):
    character = Character.query.get(character_id)
    if not character:
        return jsonify({'error': 'Character not found'}), 404

    user = get_current_user()
    if not user or character.user_id != user.id:
        return jsonify({'error': 'Character not found'}), 404

    set_player(character.id)
    return jsonify({'message': 'Character selected', 'player': serialize_character(character, include_inventory=True)})


@character_bp.route('/player', methods=['GET'])
def get_player():
    character, error_response = _get_character()
    if error_response:
        return error_response
    assert character is not None
    return jsonify(serialize_character(character))


@character_bp.route('/player', methods=['PUT'])
def update_player():
    data = request.get_json(silent=True) or {}
    character, error_response = _get_character()
    if error_response:
        return error_response
    assert character is not None

    if 'health' in data:
        character.health = int(data['health'])
    if 'damage' in data:
        character.damage = int(data['damage'])
    if 'level' in data:
        character.level = int(data['level'])

    db.session.commit()
    return jsonify(serialize_character(character))


@character_bp.route('/player/level-up', methods=['POST'])
def level_up():
    character, error_response = _get_character()
    if error_response:
        return error_response
    assert character is not None

    character.level += 1
    character.damage += 5
    character.health += 10

    db.session.commit()
    return jsonify(serialize_character(character))


@character_bp.route('/health', methods=['POST'])
def take_damage():
    data = request.get_json(silent=True) or {}
    damage_amount = int(data.get('damage', 0))

    character, error_response = _get_character()
    if error_response:
        return error_response
    assert character is not None
    character.health = max(0, character.health - damage_amount)
    db.session.commit()

    return jsonify(serialize_character(character))


@character_bp.route('/player/full', methods=['GET'])
def get_player_with_inventory():
    character, error_response = _get_character()
    if error_response:
        return error_response
    assert character is not None
    return jsonify(serialize_character(character, include_inventory=True))