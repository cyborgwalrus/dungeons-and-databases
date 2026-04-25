"""Combat resources for resolving dungeon encounters."""

from flask import jsonify
from flask_restful import Resource

from backend.db.models import Combat
from backend.db.session import db
from backend.utils.api_response_cache import (
    invalidate_user_characters_cache,
    invalidate_user_inventory_cache,
)
from backend.utils.route_helpers import json_error, require_current_character

from backend.resources.combat_engine import (
    build_combat_response,
    create_new_combat,
    resolve_combat_action,
)


class CombatResource(Resource):
    """Resolve a single combat action."""

    def post(self, combat: Combat | None = None, action: str | None = None):
        """Create a new combat row for the current character.

        Args:
            combat: Optional combat route parameter; must be absent for this
                endpoint variant.
            action: Optional action route parameter; must be absent for this
                endpoint variant.

        Returns:
            The newly created combat state and character snapshot, or a JSON
            error response when combat creation is not possible.
        """
        if combat is not None or action is not None:
            return json_error('Invalid combat action', 400)

        character, error_response = require_current_character()
        if error_response:
            return error_response

        assert character is not None
        character.health = character.max_health

        combat = create_new_combat(character)
        if not combat:
            return json_error('No enemy types available', 404)

        db.session.commit()
        return {
            'combat': combat.to_response().model_dump(),
            'character': character.to_response().model_dump(),
        }, 201

    def get(self, combat: Combat, action: str | None = None):
        """Return combat state or resolve a combat action for the requested row.

        Args:
            combat: The combat row to inspect or mutate.
            action: Optional combat action name to resolve.

        Returns:
            The current combat snapshot, the resolved action payload, or a JSON
            error response when the action is invalid.
        """
        if action is None:
            return combat.to_response().model_dump()

        character = combat.character
        if not character:
            return json_error('Character not found', 404)

        outcome = resolve_combat_action(character, combat, action)
        if outcome is None:
            return json_error('Invalid combat action', 400)
        if outcome.get('status'):
            return json_error(outcome['error'], outcome['status'])

        if 'character' in outcome and outcome['character']:
            character.health = outcome['character']['health']

        if outcome['player_died']:
            db.session.delete(combat)

        db.session.commit()
        character_ids = [character.id] if character.id is not None else None
        invalidate_user_characters_cache(character.user_id, character_ids)
        if outcome['victory']:
            invalidate_user_inventory_cache(character.user_id)

        return jsonify(build_combat_response(outcome))


def register_combat_resources(api):
    """Register combat routes on the provided API instance."""
    api.add_resource(
        CombatResource,
        '/combats',
        '/combats/<combat:combat>',
        '/combats/<combat:combat>/<string:action>',
    )
