from flask import Blueprint, jsonify, request

from ..utils.game_utils import get_player as get_current_character, seed_character_loadout, issue_auth_token
from ..db.models import Character, db
from ..utils.serializers import serialize_character
from .common import get_character as get_character_by_id, require_character_owner, require_current_user, json_error

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
    user, error_response = require_current_user()
    if error_response:
        return error_response
    assert user is not None

    characters = user.characters

    return jsonify([serialize_character(character, include_inventory=True) for character in characters])


@character_bp.route('/characters/', methods=['POST'])
def create_character():
    data = request.get_json(silent=True) or {}
    user, error_response = require_current_user()
    if error_response:
        return error_response
    assert user is not None

    name = data.get('name', '').strip()
    if not name:
        name = 'Hero'
    
    character = Character(
        user_id=user.id,
        name=name,
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
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    return jsonify(serialize_character(character, include_inventory=True))


@character_bp.route('/characters/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    user, error_response = require_current_user()
    if error_response:
        return error_response
    assert user is not None
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None

    active_character = get_current_character()

    db.session.delete(character)
    db.session.commit()
    response: dict[str, object] = {'message': 'Character deleted'}
    if active_character and active_character.id == character.id:
        response['token'] = issue_auth_token(user.id)
    return jsonify(response)


@character_bp.route('/characters/<int:character_id>/select', methods=['POST'])
def select_character(character_id):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None

    token = issue_auth_token(character.user_id, character.id)
    return jsonify({'message': 'Character selected', 'player': serialize_character(character, include_inventory=True), 'token': token})


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