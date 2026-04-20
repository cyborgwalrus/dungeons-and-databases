from flask import Blueprint, jsonify, request

from ..utils.game_utils import get_player as get_current_character, seed_character_loadout, issue_auth_token
from ..db.models import Character, db
from ..utils.serializers import serialize_character
from ..utils.serializers import serialize_item
from .common import equip_item, get_item, json_error, require_character_owner, require_current_user, unequip_item

character_bp = Blueprint('character', __name__)


@character_bp.route('/characters', methods=['GET'])
def list_characters():
    user, error_response = require_current_user()
    if error_response:
        return error_response
    assert user is not None

    characters = user.characters

    return jsonify([serialize_character(character, include_inventory=True) for character in characters])


@character_bp.route('/characters', methods=['POST'])
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


@character_bp.route('/characters/<int:character_id>/full_heal', methods=['POST'])
def full_heal_character(character_id):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None

    character.health = character.max_health
    db.session.commit()

    return jsonify(serialize_character(character, include_inventory=True))


@character_bp.route('/characters/<int:character_id>/equipment', methods=['GET'])
def list_character_equipment(character_id):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    return jsonify([equipment.to_dict() for equipment in character.equipment])


@character_bp.route('/characters/<int:character_id>/equipment', methods=['POST'])
def equip_character_item(character_id):
    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id')
    if item_id is None:
        return json_error('item_id is required')

    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    if not character.user or not character.user.inventory:
        return json_error('No inventory found', 404)

    item = get_item(character, int(item_id))
    if not item:
        return json_error('Item not found in inventory', 404)

    error_response = equip_item(character, item)
    if error_response:
        return error_response

    db.session.commit()
    db.session.expire(character)
    return jsonify({'message': 'Item equipped', 'item': serialize_item(item), 'character': serialize_character(character, include_inventory=True)})


@character_bp.route('/characters/<int:character_id>/equipment/<int:item_id>', methods=['DELETE'])
def unequip_character_item(character_id, item_id):
    character, error_response = require_character_owner(character_id)
    if error_response:
        return error_response
    assert character is not None
    error_response = unequip_item(character, item_id)
    if error_response:
        return error_response

    db.session.commit()
    db.session.expire(character)
    return jsonify({'message': 'Item unequipped', 'character': serialize_character(character, include_inventory=True)})

