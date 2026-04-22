"""Character management resources for the backend API."""

from flask import request
from flask_restful import Resource

from backend.db.models import Character, db
from backend.utils.game_utils import (
    get_player as get_current_character,
    issue_auth_token,
    seed_character_loadout,
)
from backend.utils.route_helpers import (
    equip_item,
    json_error,
    parse_int_field,
    require_item,
    unequip_item,
)
from backend.utils.api_response_cache import (
    get_cached_character_data,
    get_cached_character_equipment_data,
    get_cached_user_characters_data,
    invalidate_user_characters_cache,
    invalidate_user_inventory_cache,
)


class CharacterListResource(Resource):
    """List or create characters for a user."""

    def get(self, user):
        """List characters for the specified user."""
        return get_cached_user_characters_data(user.id)

    def post(self, user):
        """List or create characters for a user."""
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip() or 'Hero'

        level, error_response = parse_int_field(data, 'level', minimum=1, default=1)
        if error_response:
            return error_response
        health, error_response = parse_int_field(data, 'health', minimum=0, default=100)
        if error_response:
            return error_response
        damage, error_response = parse_int_field(data, 'damage', minimum=0, default=10)
        if error_response:
            return error_response

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
        invalidate_user_characters_cache(user.id)
        invalidate_user_inventory_cache(user.id)
        return character.to_dict(), 201


class CharacterResource(Resource):
    """Retrieve, update, or delete a single character."""

    def get(self, character):
        """Retrieve, update, or delete a single character."""
        return get_cached_character_data(character.id, character.user_id)

    def delete(self, character):
        """Delete a character and clear the active token if needed."""
        active_character = get_current_character()

        db.session.delete(character)
        db.session.commit()
        invalidate_user_characters_cache(character.user_id, [character.id])
        invalidate_user_inventory_cache(character.user_id)
        response: dict[str, object] = {'message': 'Character deleted'}
        if active_character and active_character.id == character.id:
            response['token'] = issue_auth_token(character.user_id)
        return response

    def put(self, character):
        """Update basic character stats from the request payload."""
        data = request.get_json(silent=True) or {}
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
        invalidate_user_characters_cache(character.user_id, [character.id])
        return character.to_dict()


class CharacterSelectResource(Resource):
    """Set the active character in the auth token."""

    def post(self, character):
        """Set the active character in the auth token."""
        token = issue_auth_token(character.user_id, character.id)
        return {'message': 'Character selected', 'character': character.to_dict(), 'token': token}


class CharacterFullHealResource(Resource):
    """Restore a character to full health."""

    def post(self, character):
        """Restore a character to full health."""
        character.health = character.max_health
        db.session.commit()
        invalidate_user_characters_cache(character.user_id, [character.id])

        return character.to_dict()


class CharacterEquipmentResource(Resource):
    """Inspect and manage a character's equipment."""

    def get(self, character):
        """Inspect and manage a character's equipment."""
        return get_cached_character_equipment_data(character.id, character.user_id)

    def post(self, character):
        """Equip an item from the character's inventory."""
        data = request.get_json(silent=True) or {}
        item_id = data.get('item_id')
        if item_id is None:
            return json_error('item_id is required')
        item_id, error_response = parse_int_field(data, 'item_id', minimum=1)
        if error_response:
            return error_response
        assert item_id is not None

        item, error_response = require_item(
            character,
            item_id,
            message='Item not found in inventory',
        )
        if error_response:
            return error_response
        assert item is not None

        error_response = equip_item(character, item)
        if error_response:
            return error_response

        db.session.commit()
        db.session.expire(character)
        invalidate_user_characters_cache(character.user_id)
        invalidate_user_inventory_cache(character.user_id)
        return {
            'message': 'Item equipped',
            'item': item.to_dict(),
            'character': character.to_dict(),
        }


class CharacterEquipmentItemResource(Resource):
    """Remove a single equipped item from a character."""

    def delete(self, character, item):
        """Unequip a worn item and return it to the inventory."""
        error_response = unequip_item(character, item.id)
        if error_response:
            return error_response

        db.session.commit()
        db.session.expire(character)
        invalidate_user_characters_cache(character.user_id)
        invalidate_user_inventory_cache(character.user_id)
        return {
            'message': 'Item unequipped',
            'character': character.to_dict(),
        }


def register_character_resources(api):
    """Register character routes on the provided API instance."""
    api.add_resource(
        CharacterListResource,
        '/users/<user:user>/characters',
    )
    api.add_resource(
        CharacterResource,
        '/characters/<character:character>',
    )
    api.add_resource(
        CharacterSelectResource,
        '/characters/<character:character>/select',
    )
    api.add_resource(
        CharacterFullHealResource,
        '/characters/<character:character>/full_heal',
    )
    api.add_resource(
        CharacterEquipmentResource,
        '/characters/<character:character>/equipment',
    )
    api.add_resource(
        CharacterEquipmentItemResource,
        '/characters/<character:character>/equipment/<item:item>',
    )
