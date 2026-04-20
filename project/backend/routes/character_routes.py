from flask import Blueprint, jsonify, request

from ..utils.game_utils import get_player as get_current_character, seed_character_loadout, issue_auth_token
from ..db.models import Character, db
from ..utils.serializers import serialize_character
from .common import require_character_owner, require_current_user

character_bp = Blueprint('character', __name__)


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
    return jsonify({'message': 'Character selected', 'character': serialize_character(character, include_inventory=True), 'token': token})


@character_bp.route('/characters/<int:character_id>', methods=['PUT'])
def update_character(character_id):
    data = request.get_json(silent=True) or {}
    character, error_response = require_character_owner(character_id)
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
    return jsonify(serialize_character(character, include_inventory=True))


@character_bp.route('/characters/<int:character_id>/level_up', methods=['POST'])
def level_up_character(character_id):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None

    character.level += 1
    character.damage += 5
    character.health += 10

    db.session.commit()
    return jsonify(serialize_character(character, include_inventory=True))


@character_bp.route('/characters/<int:character_id>/full_heal', methods=['POST'])
def full_heal_character(character_id):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None

    character.health = 100 + (max(0, character.level - 1) * 10) + character.bonus_health
    db.session.commit()

    return jsonify(serialize_character(character, include_inventory=True))