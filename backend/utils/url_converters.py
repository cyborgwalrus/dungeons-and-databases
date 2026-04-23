"""Werkzeug URL converters that resolve owned ORM objects."""

from __future__ import annotations

from typing import Any

from werkzeug.exceptions import NotFound, Unauthorized
from werkzeug.routing import BaseConverter

from backend.db.models import Combat, Character, Item, User
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
        user_id = self._parse_int(value)
        user = User.query.get(user_id)
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
        character_id = self._parse_int(value)
        character = Character.query.get(character_id)
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
        item_id = self._parse_int(value)
        item = Item.query.get(item_id)
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
        combat_id = self._parse_int(value)
        combat = Combat.query.get(combat_id)
        current_user = get_current_user()
        if not current_user:
            raise Unauthorized(description='Unauthorized')
        character = get_player()
        if not combat or not character:
            raise self._not_found()
        if combat.character_id != character.id:
            raise Unauthorized(description='Unauthorized')
        return combat