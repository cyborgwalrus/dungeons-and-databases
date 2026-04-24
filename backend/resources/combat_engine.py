"""Combat state machine and combat response helpers."""

import random
from typing import Any, cast

from sqlalchemy import delete

from backend.db.models import Character, Combat
from backend.db.session import db
from backend.resources.combat_builders import (
    combat_attack_blocked_outcome,
    combat_attack_defeat_outcome,
    combat_attack_round_outcome,
    combat_deeper_blocked_outcome,
    combat_deeper_success_outcome,
    combat_home_success_outcome,
    combat_run_failure_outcome,
    combat_run_success_outcome,
    combat_victory_message,
    combat_victory_outcome,
)
from backend.utils.game_utils import add_inventory_item, get_enemy_types, get_item_types, get_player


def _scaled_enemy_stats(base_health: int, base_damage: int, level: int) -> tuple[int, int]:
    return base_health + (level * 10), base_damage + (level * 2)


def create_new_combat(
    character: Character | None = None,
    *,
    level: int = 1,
) -> Combat | None:
    character = character or get_player()
    if character is None:
        return None

    assert character.id is not None
    character_id = int(character.id)

    db.session.execute(delete(Combat).where(cast(Any, Combat.character_id) == character_id))
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


def _combat_damage_roll(max_damage: int) -> int:
    return random.randint(max(1, max_damage // 2), max(1, max_damage))


def _victory_outcome(character, combat: Combat, player_hits: int) -> tuple[list[str], list[dict[str, Any]]]:
    enemy_name = combat.enemy['name']
    message_lines = combat_victory_message(enemy_name, player_hits)

    items_dropped = drop_loot(combat)
    if items_dropped:
        item_names = ', '.join(item['name'] for item in items_dropped)
        message_lines.append(f'You found {item_names}!')
        for item in items_dropped:
            add_inventory_item(character, item['id'], level=item['level'])

    _apply_victory_experience(character, combat, message_lines)
    return message_lines, items_dropped


def check_character_death(health: int) -> bool:
    return health <= 0


def _resolve_attack_turn(character, combat: Combat) -> dict[str, Any]:
    enemy_name = combat.enemy['name']

    if combat.enemy_current_health <= 0:
        return combat_attack_blocked_outcome(character, combat)

    effective_damage = character.damage + character.bonus_damage
    player_hits = _combat_damage_roll(effective_damage)
    monster_hits = _combat_damage_roll(combat.enemy_damage)

    combat.enemy_current_health = max(0, combat.enemy_current_health - player_hits)

    if combat.enemy_current_health > 0:
        combat.character_health = max(0, combat.character_health - monster_hits)
        if check_character_death(combat.character_health):
            character.health = combat.character_health
            return combat_attack_defeat_outcome(character, combat, enemy_name)

        return combat_attack_round_outcome(character, combat, enemy_name, player_hits, monster_hits)

    character.health = combat.character_health
    message_lines, items_dropped = _victory_outcome(character, combat, player_hits)

    return combat_victory_outcome(character, combat, message_lines, items_dropped)


def _resolve_deeper_turn(character, combat: Combat) -> dict[str, Any]:
    enemy_name = combat.enemy['name']
    if combat.enemy_current_health > 0:
        return combat_deeper_blocked_outcome(character, combat)

    character.health = combat.character_health
    next_level = max(1, combat.enemy_level + 1)
    db.session.delete(combat)
    next_combat = create_new_combat(character, level=next_level)
    if not next_combat:
        return {'error': 'No enemy types available', 'status': 404}

    return combat_deeper_success_outcome(character, combat, next_combat, enemy_name)


def _resolve_home_turn(character, combat: Combat) -> dict[str, Any]:
    character.health = combat.character_health
    db.session.delete(combat)

    return combat_home_success_outcome(character, combat)


def _resolve_run_turn(character, combat: Combat) -> dict[str, Any]:
    enemy_name = combat.enemy['name']
    dice_roll = random.randint(1, 6)

    if dice_roll >= 4:
        character.health = combat.character_health
        db.session.delete(combat)
        return combat_run_success_outcome(character, combat, dice_roll)

    damage_taken = _combat_damage_roll(combat.enemy_damage)
    combat.character_health = max(0, combat.character_health - damage_taken)
    if check_character_death(combat.character_health):
        character.health = combat.character_health
        return combat_run_failure_outcome(character, combat, enemy_name, dice_roll, damage_taken, True)

    return combat_run_failure_outcome(character, combat, enemy_name, dice_roll, damage_taken, False)


def _apply_victory_experience(character, combat: Combat, message_lines: list[str]) -> None:
    experience_gained = 20 + (max(1, combat.enemy_level) * 10)
    character.gain_experience(experience_gained)
    message_lines.append(f'You gained {experience_gained} XP!')

    leveled_up = False
    while character.level_up():
        leveled_up = True
        message_lines.append(f'You reached level {character.level}!')

    if leveled_up:
        message_lines.append(f'Next level at {character.experience_to_next_level} XP.')


def drop_loot(combat: Combat) -> list[dict[str, Any]]:
    items_dropped: list[dict[str, Any]] = []
    all_items = get_item_types()
    if not all_items:
        return items_dropped

    monster_level = max(1, combat.enemy_level or 1)
    num_items = min(3, 1 + max(0, (monster_level - 1) // 4))
    for _ in range(num_items):
        item_type = random.choice(all_items)
        items_dropped.append(
            {
                **item_type,
                'level': max(1, monster_level + random.choice([-1, 0, 0, 1])),
            }
        )

    return items_dropped


def build_combat_response(outcome: dict[str, Any]) -> dict[str, Any]:
    character = outcome['character']
    combat = outcome['combat']
    payload: dict[str, Any] = {
        'character': character,
        'combat': (
            None
            if outcome['player_died']
            or outcome.get('success', False)
            or combat is None
            else combat.to_response().model_dump()
        ),
        'message': outcome['message'],
        'victory': outcome['victory'],
        'items_dropped': outcome['items_dropped'],
        'player_died': outcome['player_died'],
        'success': outcome.get('success', False),
    }

    if outcome.get('dice_roll') is not None:
        payload['dice_roll'] = outcome['dice_roll']
    if outcome.get('success', False):
        payload['damage'] = outcome.get('damage', 0)

    return payload


def resolve_combat_action(character, combat: Combat, action_name: str) -> dict[str, Any] | None:
    action = (action_name or '').lower().strip()
    if action == 'attack':
        return _resolve_attack_turn(character, combat)
    if action == 'deeper':
        return _resolve_deeper_turn(character, combat)
    if action == 'run':
        return _resolve_run_turn(character, combat)
    if action == 'home':
        if combat.enemy_current_health > 0:
            return {'error': 'You can only go home after defeating the enemy', 'status': 400}
        return _resolve_home_turn(character, combat)
    return None
