from flask import request
from flask_restful import Resource
from sqlalchemy.orm import selectinload

from backend.db.models import Character, db
from backend.utils.game_utils import get_player as get_current_character, seed_character_loadout, issue_auth_token
from backend.utils.route_helpers import equip_item, get_item, json_error, require_character_owner, require_current_user, unequip_item
from backend.utils.serializers import serialize_character, serialize_item


class CharacterListResource(Resource):
    def get(self, user_id):
        """List characters for the specified user."""
        user, error_response = require_current_user()
        if error_response:
            return error_response
        assert user is not None

        # Validate that the current user owns these characters
        if user.id != user_id:
            return json_error('Unauthorized', 401)

        # Use eager loading to avoid N+1 queries when accessing inventory
        characters = Character.query.filter_by(user_id=user.id).options(
            selectinload(Character.equipment),
        ).all()

        return [serialize_character(character, include_inventory=True) for character in characters]

    def post(self, user_id):
        """Create a new character for the specified user and seed starter gear."""
        data = request.get_json(silent=True) or {}
        user, error_response = require_current_user()
        if error_response:
            return error_response
        assert user is not None

        # Validate that the current user owns these characters
        if user.id != user_id:
            return json_error('Unauthorized', 401)

        name = data.get('name', '').strip()
        if not name:
            name = 'Hero'

        try:
            level = int(data.get('level', 1))
            health = int(data.get('health', 100))
            damage = int(data.get('damage', 10))
        except (TypeError, ValueError):
            return json_error('level, health, and damage must be valid integers')

        character = Character(
            user_id=user.id,
            name=name,
            level=level,
            health=health,
            damage=damage,
        )
        db.session.add(character)
        db.session.flush()
        seed_character_loadout(character)
        db.session.commit()
        return serialize_character(character, include_inventory=True), 201


class CharacterResource(Resource):
    def get(self, character_id):
        """Return a single character owned by the current user."""
        character, error_response = require_character_owner(character_id)
        if error_response:
            return error_response
        assert character is not None
        return serialize_character(character, include_inventory=True)

    def delete(self, character_id):
        """Delete a character and clear the active token if needed."""
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
        return response

    def put(self, character_id):
        """Update basic character stats from the request payload."""
        data = request.get_json(silent=True) or {}
        character, error_response = require_character_owner(character_id)
        if error_response:
            return error_response
        assert character is not None

        try:
            if 'health' in data:
                health = int(data['health'])
                if health < 0:
                    return json_error('health must be non-negative')
                character.health = health
            if 'damage' in data:
                damage = int(data['damage'])
                if damage < 0:
                    return json_error('damage must be non-negative')
                character.damage = damage
            if 'level' in data:
                level = int(data['level'])
                if level < 1:
                    return json_error('level must be at least 1')
                character.level = level
        except (TypeError, ValueError):
            return json_error('health, damage, and level must be valid integers')

        db.session.commit()
        return serialize_character(character, include_inventory=True)


class CharacterSelectResource(Resource):
    def post(self, character_id):
        """Set the requested character as the active player character."""
        character, error_response = require_character_owner(character_id)
        if error_response:
            return error_response
        assert character is not None

        token = issue_auth_token(character.user_id, character.id)
        return {'message': 'Character selected', 'character': serialize_character(character, include_inventory=True), 'token': token}


class CharacterFullHealResource(Resource):
    def post(self, character_id):
        """Restore the character to full health."""
        character, error_response = require_character_owner(character_id)
        if error_response:
            return error_response
        assert character is not None

        character.health = character.max_health
        db.session.commit()

        return serialize_character(character, include_inventory=True)


class CharacterEquipmentResource(Resource):
    def get(self, character_id):
        """List the equipment currently worn by the character."""
        character, error_response = require_character_owner(character_id)
        if error_response:
            return error_response
        assert character is not None
        return [equipment.to_dict() for equipment in character.equipment]

    def post(self, character_id):
        """Equip an item from the character's inventory."""
        data = request.get_json(silent=True) or {}
        item_id = data.get('item_id')
        if item_id is None:
            return json_error('item_id is required')

        try:
            item_id = int(item_id)
            if item_id <= 0:
                return json_error('item_id must be a positive integer')
        except (TypeError, ValueError):
            return json_error('item_id must be a valid integer')

        character, error_response = require_character_owner(character_id)
        if error_response:
            return error_response
        assert character is not None
        if not character.user or not character.user.inventory:
            return json_error('No inventory found', 404)

        item = get_item(character, item_id)
        if not item:
            return json_error('Item not found in inventory', 404)

        error_response = equip_item(character, item)
        if error_response:
            return error_response

        db.session.commit()
        db.session.expire(character)
        return {'message': 'Item equipped', 'item': serialize_item(item), 'character': serialize_character(character, include_inventory=True)}


class CharacterEquipmentItemResource(Resource):
    def delete(self, character_id, item_id):
        """Unequip a worn item and return it to the inventory."""
        character, error_response = require_character_owner(character_id)
        if error_response:
            return error_response
        assert character is not None
        error_response = unequip_item(character, item_id)
        if error_response:
            return error_response

        db.session.commit()
        db.session.expire(character)
        return {'message': 'Item unequipped', 'character': serialize_character(character, include_inventory=True)}


def register_character_resources(api):
    api.add_resource(CharacterListResource, '/api/users/<int:user_id>/characters')
    api.add_resource(CharacterResource, '/api/characters/<int:character_id>')
    api.add_resource(CharacterSelectResource, '/api/characters/<int:character_id>/select')
    api.add_resource(CharacterFullHealResource, '/api/characters/<int:character_id>/full_heal')
    api.add_resource(CharacterEquipmentResource, '/api/characters/<int:character_id>/equipment')
    api.add_resource(CharacterEquipmentItemResource, '/api/characters/<int:character_id>/equipment/<int:item_id>')
