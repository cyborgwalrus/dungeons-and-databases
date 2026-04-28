"""Character management resources for the backend API."""

from flask import request
from flask_restful import Resource

from backend.db.models import Character
from backend.db.session import db
from backend.db.schemas import CharacterCreateRequest, CharacterUpdateRequest
from backend.db.enums import CharacterState, UserState
from backend.utils.game_utils import (
    get_player as get_current_character,
    issue_auth_token,
    seed_character_loadout,
)
from backend.utils.hypermedia import inject_collection_links, inject_response_links
from backend.utils.route_helpers import (
    equip_item,
    unequip_item,
    validate_payload,
)
from backend.utils.api_response_cache import (
    get_cached_character_data,
    get_cached_character_equipment_data,
    get_cached_user_characters_data,
    invalidate_user_characters_cache,
    invalidate_user_inventory_cache,
    invalidate_user_profile_cache,
)


class CharacterListResource(Resource):
    """List or create characters for a user."""

    def get(self, user):
        """List characters for the specified user."""
        return inject_collection_links(get_cached_user_characters_data(user.id))

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
        return inject_response_links(character.to_response().model_dump()), 201


class CharacterResource(Resource):
    """Retrieve, update, or delete a single character."""

    def get(self, character):
        """Retrieve a single character."""
        return inject_response_links(get_cached_character_data(character.id, character.user_id))

    def delete(self, character):
        """Delete a character and clear the active token if needed.

        Args:
            character: The character resolved from the route.

        Returns:
            A confirmation message, and a new token when the deleted character
            was the active one.
        """
        active_character = get_current_character()
        user = character.user
        if active_character and active_character.id == character.id and user is not None:
            user.state = UserState.LOGGED_IN

        db.session.delete(character)
        db.session.commit()
        invalidate_user_characters_cache(character.user_id, [character.id])
        invalidate_user_inventory_cache(character.user_id)
        response: dict[str, object] = {'message': 'Character deleted'}
        if active_character and active_character.id == character.id:
            response['token'] = issue_auth_token(character.user_id)
            invalidate_user_profile_cache(character.user_id)
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
        return inject_response_links(character.to_response().model_dump())


class CharacterSelectResource(Resource):
    """Set the active character in the auth token."""

    def post(self, character):
        """Set the active character in the auth token.

        Args:
            character: The character resolved from the route.

        Returns:
            The selected character payload and an updated token.
        """
        character.state = CharacterState.HOME
        user = character.user
        if user is not None:
            user.state = UserState.CHARACTER_SELECTED
        db.session.commit()
        invalidate_user_characters_cache(character.user_id, [character.id])
        invalidate_user_profile_cache(character.user_id)

        token = issue_auth_token(character.user_id, character.id)
        return {
            'message': 'Character selected',
            'character': inject_response_links(character.to_response().model_dump()),
            'token': token,
        }


class CharacterEquipmentResource(Resource):
    """Inspect and manage a character's equipment."""

    def get(self, character):
        """Inspect a character's equipment."""
        return inject_collection_links(
            get_cached_character_equipment_data(character.id, character.user_id),
            user_id=character.user_id,
            character_id=character.id,
            character_state=character.state,
            equipped=True,
        )


class CharacterEquipmentItemResource(Resource):
    """Remove a single equipped item from a character."""

    def post(self, character, item):
        """Equip a specific item from the character's inventory.

        Args:
            character: The character resolved from the route.
            item: The inventory item resolved from the route.

        Returns:
            The equipped item payload and updated character snapshot, or a
            JSON error response when the item cannot be equipped.
        """
        if character.state != CharacterState.HOME:
            return {'error': 'Equipment can only be changed in home state'}, 409

        if item.is_equipped:
            return {'error': 'Item not found in inventory'}, 404

        error_response = equip_item(character, item)
        if error_response:
            return error_response

        db.session.commit()
        db.session.expire(character)
        invalidate_user_characters_cache(character.user_id)
        invalidate_user_inventory_cache(character.user_id)
        return {
            'message': 'Item equipped',
            'item': inject_response_links(
                item.to_response().model_dump(),
                user_id=item.user_id,
                character_id=character.id,
                character_state=character.state,
                equipped=True,
            ),
            'character': inject_response_links(character.to_response().model_dump()),
        }

    def delete(self, character, item):
        """Unequip a worn item and return it to the inventory.

        Args:
            character: The character resolved from the route.
            item: The equipped item resolved from the route.

        Returns:
            A confirmation message and updated character snapshot, or a JSON
            error response when the item cannot be unequipped.
        """
        if character.state != CharacterState.HOME:
            return {'error': 'Equipment can only be changed in home state'}, 409

        error_response = unequip_item(character, item.id)
        if error_response:
            return error_response

        db.session.commit()
        db.session.expire(character)
        invalidate_user_characters_cache(character.user_id)
        invalidate_user_inventory_cache(character.user_id)
        return {
            'message': 'Item unequipped',
            'character': inject_response_links(character.to_response().model_dump()),
        }


def register_character_resources(api):
    """Register character routes on the provided API instance."""
    api.add_resource(
        CharacterListResource,
        '/users/<user:user>/characters',
        endpoint='character_list',
    )
    api.add_resource(
        CharacterResource,
        '/characters/<character:character>',
        endpoint='character_detail',
    )
    api.add_resource(
        CharacterSelectResource,
        '/characters/<character:character>/select',
        endpoint='character_select',
    )
    api.add_resource(
        CharacterEquipmentResource,
        '/characters/<character:character>/equipment',
        endpoint='character_equipment',
    )
    api.add_resource(
        CharacterEquipmentItemResource,
        '/characters/<character:character>/equipment/<item:item>',
        endpoint='character_equipment_item',
    )
