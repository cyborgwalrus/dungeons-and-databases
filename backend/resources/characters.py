"""Character management resources for the backend API."""

from flask import request
from flask_restful import Resource

from backend.db.models import Character
from backend.db.session import db
from backend.db.schemas import CharacterCreateRequest, CharacterUpdateRequest, ItemSelectionRequest
from backend.utils.game_utils import (
    get_player as get_current_character,
    issue_auth_token,
    seed_character_loadout,
)
from backend.utils.route_helpers import (
    equip_item,
    require_item,
    unequip_item,
    validate_payload,
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
        """Create a new character for the specified user.

        Args:
            user: The user resolved from the route.

        Returns:
            The created character payload, or a JSON error response when the
            request payload is invalid.
        """
        data = request.get_json(silent=True) or {}
        payload, error_response = validate_payload(CharacterCreateRequest, data)
        if error_response:
            return error_response
        assert payload is not None

        character = Character(
            user_id=user.id,
            name=payload.name or 'Hero',
            level=payload.level,
            health=payload.health,
            damage=payload.damage,
        )
        db.session.add(character)
        db.session.flush()
        seed_character_loadout(character)
        db.session.commit()
        invalidate_user_characters_cache(user.id)
        invalidate_user_inventory_cache(user.id)
        return character.to_response().model_dump(), 201


class CharacterResource(Resource):
    """Retrieve, update, or delete a single character."""

    def get(self, character):
        """Retrieve a single character."""
        return get_cached_character_data(character.id, character.user_id)

    def delete(self, character):
        """Delete a character and clear the active token if needed.

        Args:
            character: The character resolved from the route.

        Returns:
            A confirmation message, and a new token when the deleted character
            was the active one.
        """
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
        """Update basic character stats from the request payload.

        Args:
            character: The character resolved from the route.

        Returns:
            The updated serialized character, or a JSON error response when
            the payload is invalid.
        """
        data = request.get_json(silent=True) or {}
        payload, error_response = validate_payload(CharacterUpdateRequest, data)
        if error_response:
            return error_response
        assert payload is not None

        for field_name, value in payload.model_dump(exclude_unset=True).items():
            setattr(character, field_name, value)

        db.session.commit()
        invalidate_user_characters_cache(character.user_id, [character.id])
        return character.to_response().model_dump()


class CharacterSelectResource(Resource):
    """Set the active character in the auth token."""

    def post(self, character):
        """Set the active character in the auth token.

        Args:
            character: The character resolved from the route.

        Returns:
            The selected character payload and an updated token.
        """
        token = issue_auth_token(character.user_id, character.id)
        return {
            'message': 'Character selected',
            'character': character.to_response().model_dump(),
            'token': token,
        }


class CharacterFullHealResource(Resource):
    """Restore a character to full health."""

    def post(self, character):
        """Restore a character to full health.

        Args:
            character: The character resolved from the route.

        Returns:
            The healed character payload.
        """
        character.health = character.max_health
        db.session.commit()
        invalidate_user_characters_cache(character.user_id, [character.id])

        return character.to_response().model_dump()


class CharacterEquipmentResource(Resource):
    """Inspect and manage a character's equipment."""

    def get(self, character):
        """Inspect a character's equipment."""
        return get_cached_character_equipment_data(character.id, character.user_id)

    def post(self, character):
        """Equip an item from the character's inventory.

        Args:
            character: The character resolved from the route.

        Returns:
            The equipped item payload and updated character snapshot, or a
            JSON error response when the item cannot be equipped.
        """
        data = request.get_json(silent=True) or {}
        payload, error_response = validate_payload(ItemSelectionRequest, data)
        if error_response:
            return error_response
        assert payload is not None
        item_id = payload.item_id

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
            'item': item.to_response().model_dump(),
            'character': character.to_response().model_dump(),
        }


class CharacterEquipmentItemResource(Resource):
    """Remove a single equipped item from a character."""

    def delete(self, character, item):
        """Unequip a worn item and return it to the inventory.

        Args:
            character: The character resolved from the route.
            item: The equipped item resolved from the route.

        Returns:
            A confirmation message and updated character snapshot, or a JSON
            error response when the item cannot be unequipped.
        """
        error_response = unequip_item(character, item.id)
        if error_response:
            return error_response

        db.session.commit()
        db.session.expire(character)
        invalidate_user_characters_cache(character.user_id)
        invalidate_user_inventory_cache(character.user_id)
        return {
            'message': 'Item unequipped',
            'character': character.to_response().model_dump(),
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
