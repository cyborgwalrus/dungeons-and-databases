"""Werkzeug URL converters that resolve owned ORM objects."""

from __future__ import annotations

from typing import Any

from werkzeug.exceptions import NotFound, Unauthorized
from werkzeug.routing import BaseConverter

from backend.db.models import Combat, Character, Item, User
from backend.db.session import db
from backend.utils.game_utils import get_current_user, get_player


class OwnedModelConverter(BaseConverter):
    """Base converter for resolving a model instance by ID."""

    model_name = 'object'

    def to_url(self, value: Any) -> str:
        """Serialize model instances back into route segments."""
        if hasattr(value, 'id'):
            return str(getattr(value, 'id'))
        return str(value)

    def _parse_int(self, value: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError) as error:
            raise NotFound(description=f'{self.model_name.title()} not found') from error

    def _not_found(self) -> NotFound:
        return NotFound(description=f'{self.model_name.title()} not found')


class UserConverter(OwnedModelConverter):
    """Resolve the authenticated user and enforce ownership."""

    model_name = 'user'

    def to_python(self, value: str) -> User:
        """Resolve a user ID from the route and enforce authentication.

        Args:
            value: The raw route segment containing the user ID.

        Returns:
            The authenticated user row that matches the route parameter.

        Raises:
            NotFound: If the user ID does not exist.
            Unauthorized: If the request is not authenticated or the route ID
                does not belong to the current user.
        """
        user_id = self._parse_int(value)
        user = db.session.get(User, user_id)
        current_user = get_current_user()
        if not current_user:
            raise Unauthorized(description='Unauthorized')
        if not user:
            raise self._not_found()
        if current_user.id != user.id:
            raise Unauthorized(description='Unauthorized')
        return user


class CharacterConverter(OwnedModelConverter):
    """Resolve a character owned by the authenticated user."""

    model_name = 'character'

    def to_python(self, value: str) -> Character:
        """Resolve a character ID from the route and enforce ownership.

        Args:
            value: The raw route segment containing the character ID.

        Returns:
            The character row owned by the authenticated user.

        Raises:
            NotFound: If the character ID does not exist.
            Unauthorized: If the request is not authenticated or the character
                does not belong to the current user.
        """
        character_id = self._parse_int(value)
        character = db.session.get(Character, character_id)
        current_user = get_current_user()
        if not current_user:
            raise Unauthorized(description='Unauthorized')
        if not character:
            raise self._not_found()
        if character.user_id != current_user.id:
            raise Unauthorized(description='Unauthorized')
        return character


class ItemConverter(OwnedModelConverter):
    """Resolve an inventory item owned by the authenticated user."""

    model_name = 'item'

    def to_python(self, value: str) -> Item:
        """Resolve an inventory item ID from the route and enforce ownership.

        Args:
            value: The raw route segment containing the item ID.

        Returns:
            The inventory item row owned by the authenticated user.

        Raises:
            NotFound: If the item ID does not exist.
            Unauthorized: If the request is not authenticated or the item does
                not belong to the current user.
        """
        item_id = self._parse_int(value)
        item = db.session.get(Item, item_id)
        current_user = get_current_user()
        if not current_user:
            raise Unauthorized(description='Unauthorized')
        if not item:
            raise self._not_found()
        if item.user_id != current_user.id:
            raise Unauthorized(description='Unauthorized')
        return item


class CombatConverter(OwnedModelConverter):
    """Resolve combat for the active character in the auth token."""

    model_name = 'combat'

    def to_python(self, value: str) -> Combat:
        """Resolve a combat ID from the route and enforce character ownership.

        Args:
            value: The raw route segment containing the combat ID.

        Returns:
            The combat row attached to the active character.

        Raises:
            NotFound: If the combat or active character does not exist.
            Unauthorized: If the combat does not belong to the active
                character.
        """
        combat_id = self._parse_int(value)
        combat = db.session.get(Combat, combat_id)
        current_user = get_current_user()
        if not current_user:
            raise Unauthorized(description='Unauthorized')
        character = get_player()
        if not combat or not character:
            raise self._not_found()
        if combat.character_id != character.id:
            raise Unauthorized(description='Unauthorized')
        return combat