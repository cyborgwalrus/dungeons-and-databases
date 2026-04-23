"""Dungeon entry resources for creating combat rows."""

import random
from typing import Any

from backend.db.models import Combat, db
from backend.utils.game_utils import get_enemy_types, get_player


def _scaled_enemy_stats(base_health: int, base_damage: int, level: int) -> tuple[int, int]:
    """Return the live health and damage values for a seeded enemy."""
    return base_health + (level * 10), base_damage + (level * 2)


def create_new_combat(
    character=None,
    *,
    level: int = 1,
) -> Combat | None:
    """Create a fresh combat row for the current player."""
    character = character or get_player()
    if character is None:
        return None

    assert character.id is not None

    Combat.query.filter_by(character_id=character.id).delete(synchronize_session=False)
    db.session.flush()

    enemy_types_data = get_enemy_types()
    enemy_type = random.choice(enemy_types_data) if enemy_types_data else None
    if not enemy_type:
        db.session.rollback()
        return None

    level = max(1, int(level))
    enemy_health, enemy_damage = _scaled_enemy_stats(
        enemy_type['base_health'],
        enemy_type['base_damage'],
        level,
    )

    combat = Combat(
        character_id=character.id,
        enemy_type_id=enemy_type['id'],
        enemy_level=level,
        character_health=character.health,
        enemy_current_health=enemy_health,
        enemy_max_health=enemy_health,
        enemy_damage=enemy_damage,
    )
    db.session.add(combat)
    db.session.commit()
    return combat


def create_combat_payload(character=None) -> dict[str, Any] | None:
    """Create a new combat row and return the API payload."""
    character = character or get_player()
    if character is None:
        return None

    combat = create_new_combat(character)
    if not combat:
        return None

    return {
        'combat': combat.to_response().model_dump(),
        'character': character.to_response().model_dump(),
    }
