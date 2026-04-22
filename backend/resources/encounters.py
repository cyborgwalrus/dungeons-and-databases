import random
from typing import Any

from flask_restful import Resource

from backend.db.models import Combat, Encounter, db
from backend.db.reference_data import get_all_enemy_type_data
from backend.utils.game_utils import get_player
from backend.utils.route_helpers import json_error, require_current_character


def _scaled_enemy_stats(base_health: int, base_damage: int, enemy_level: int) -> tuple[int, int]:
    """Return the live health and damage values for a seeded enemy."""
    return base_health + (enemy_level * 10), base_damage + (enemy_level * 2)


def create_new_encounter(character=None, *, enemy_level: int = 1) -> tuple[Encounter | None, Combat | None]:
    """Create a fresh encounter and combat row for the current player."""
    character = character or get_player()
    if character is None:
        return None, None

    existing_encounter = Encounter.query.filter_by(character_id=character.id).first()
    if existing_encounter:
        db.session.delete(existing_encounter)

    enemy_types = get_all_enemy_type_data()
    enemy_type = random.choice(enemy_types) if enemy_types else None
    if not enemy_type:
        return None, None

    enemy_level = max(1, int(enemy_level))
    enemy_health, enemy_damage = _scaled_enemy_stats(enemy_type['health'], enemy_type['damage'], enemy_level)

    encounter = Encounter(
        character_id=character.id,
        enemy_template_id=enemy_type['id'],
        enemy_name=enemy_type['name'],
        enemy_description=enemy_type['description'],
        enemy_base_health=enemy_type['health'],
        enemy_base_damage=enemy_type['damage'],
        enemy_level=enemy_level,
    )
    db.session.add(encounter)
    db.session.flush()
    combat = Combat(
        encounter=encounter,
        character_id=character.id,
        character_health=character.health,
        enemy_current_health=enemy_health,
        enemy_max_health=enemy_health,
        enemy_damage=enemy_damage,
    )
    db.session.add(combat)
    db.session.commit()
    return encounter, combat


def create_encounter_payload(character=None) -> dict[str, Any] | None:
    """Create a new encounter/combat pair and return the API payload."""
    character = character or get_player()
    if character is None:
        return None

    encounter, combat = create_new_encounter(character)
    if not encounter or not combat:
        return None

    return {
        'encounter': encounter.to_dict(),
        'combat': combat.to_dict(),
        'character': character.to_dict(),
    }


class EncounterResource(Resource):
    def post(self):
        """Create a new encounter and matching combat state for the active character."""
        character, error_response = require_current_character()
        if error_response:
            return error_response
        assert character is not None

        payload = create_encounter_payload(character)
        if not payload:
            return json_error('No enemy types available', 404)
        return payload, 201


def register_encounter_resources(api):
    api.add_resource(EncounterResource, '/api/encounters')