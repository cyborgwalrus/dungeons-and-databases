"""Combat resources for resolving dungeon encounters."""

import random
from typing import Any

from flask import jsonify
from flask_restful import Resource
from sqlalchemy import delete

from backend.db.models import Combat
from backend.db.session import db
from backend.utils.game_utils import get_enemy_types, get_player
from backend.utils.api_response_cache import (
    invalidate_user_characters_cache,
    invalidate_user_inventory_cache,
)
from backend.utils.game_utils import add_inventory_item, get_item_types
from backend.utils.route_helpers import json_error, require_current_character


def _scaled_enemy_stats(base_health: int, base_damage: int, level: int) -> tuple[int, int]:
    """Scale a seeded enemy's health and damage for the requested level.

    Args:
        base_health: The enemy's base health value from reference data.
        base_damage: The enemy's base damage value from reference data.
        level: The combat level used to scale the enemy.

    Returns:
        A ``(health, damage)`` tuple with level-adjusted values.
    """
    return base_health + (level * 10), base_damage + (level * 2)


def create_new_combat(
    character=None,
    *,
    level: int = 1,
) -> Combat | None:
    """Create a fresh combat row for the current player.

    Args:
        character: The character that will enter combat. When omitted, the
            current player is resolved from the request token.
        level: The encounter level to generate.

    Returns:
        The newly created combat row, or ``None`` when no enemy types are
        available or no current player exists.
    """
    character = character or get_player()
    if character is None:
        return None

    assert character.id is not None

    db.session.execute(delete(Combat).where(Combat.character_id == character.id))
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
    """Roll a bounded combat damage value for one turn.

    Args:
        max_damage: The upper bound for the damage roll.

    Returns:
        A randomized damage value between half damage and full damage.
    """
    return random.randint(max(1, max_damage // 2), max(1, max_damage))


class MessageBuilder:
    """Build combat outcome messages."""

    @staticmethod
    def victory(enemy_name: str, player_hits: int) -> list[str]:
        """Build the opening victory message for a defeated enemy."""
        return [
            'Victory!',
            f'You dealt {player_hits} damage and defeated the {enemy_name}!',
        ]

    @staticmethod
    def attack_round(enemy_name: str, player_hits: int, monster_hits: int) -> str:
        """Build the message for an attack round where combat continues."""
        return (
            f'You dealt {player_hits} damage to {enemy_name}!\n'
            f'{enemy_name} dealt {monster_hits} damage to you!'
        )

    @staticmethod
    def defeat(enemy_name: str) -> str:
        """Build the message for a defeated attack round."""
        return (
            'Defeat!\n'
            f'You have been defeated by {enemy_name}!\n'
            'You lost the loot from this dungeon run...'
        )

    @staticmethod
    def escape_success(dice_roll: int) -> str:
        """Build the message for a successful escape."""
        return f'You rolled a {dice_roll}! You successfully escaped and returned home!'

    @staticmethod
    def escape_failure(dice_roll: int, enemy_name: str, damage_taken: int, defeated: bool) -> str:
        """Build the message for a failed escape attempt."""
        if defeated:
            return (
                f'You rolled a {dice_roll} and failed to escape!\n'
                f'{enemy_name} dealt {damage_taken} damage! '
                'You lost the loot from this dungeon run and returned to the start...'
            )

        return (
            f'You rolled a {dice_roll} and failed to escape!\n'
            f'{enemy_name} caught you and dealt {damage_taken} damage!'
        )


class OutcomeBuilder:
    """Build structured combat outcomes with shared defaults."""

    def __init__(self, character, combat: Combat | None):
        self._character = character
        self._combat = combat
        self._outcome: dict[str, Any] = {
            'message': '',
            'victory': False,
            'items_dropped': [],
            'player_died': False,
            'combat': combat,
            'character': self._character_snapshot(),
            'success': False,
            'damage': 0,
            'dice_roll': None,
        }

    def _character_snapshot(self, *, health: int | None = None) -> dict[str, Any]:
        if health is None:
            return self._character.to_response().model_dump()

        return self._character.to_response(health=health).model_dump()

    def with_message(self, message: str):
        self._outcome['message'] = message
        return self

    def with_victory(self):
        self._outcome['victory'] = True
        return self

    def with_defeat(self):
        self._outcome['player_died'] = True
        return self

    def with_items_dropped(self, items_dropped: list[dict[str, Any]]):
        self._outcome['items_dropped'] = items_dropped
        return self

    def with_combat(self, combat: Combat | None):
        self._outcome['combat'] = combat
        return self

    def with_character(self):
        self._outcome['character'] = self._character_snapshot()
        return self

    def with_character_health(self, health: int):
        self._outcome['character'] = self._character_snapshot(health=health)
        return self

    def with_success(self, damage: int = 0):
        self._outcome['success'] = True
        self._outcome['damage'] = damage
        return self

    def with_failure(self, damage: int):
        self._outcome['success'] = False
        self._outcome['damage'] = damage
        return self

    def with_dice_roll(self, dice_roll: int):
        self._outcome['dice_roll'] = dice_roll
        return self

    def build(self) -> dict[str, Any]:
        return self._outcome

    @classmethod
    def attack_blocked(cls, character, combat: Combat):
        return (
            cls(character, combat)
            .with_message('You need to go deeper to face the next enemy.')
            .with_character_health(combat.character_health)
            .build()
        )

    @classmethod
    def attack_defeat(cls, character, combat: Combat, enemy_name: str):
        return (
            cls(character, combat)
            .with_message(MessageBuilder.defeat(enemy_name))
            .with_defeat()
            .with_character_health(combat.character_health)
            .build()
        )

    @classmethod
    def attack_round(cls, character, combat: Combat, enemy_name: str, player_hits: int, monster_hits: int):
        return (
            cls(character, combat)
            .with_message(MessageBuilder.attack_round(enemy_name, player_hits, monster_hits))
            .with_character_health(combat.character_health)
            .build()
        )

    @classmethod
    def victory_outcome(
        cls,
        character,
        combat: Combat,
        message_lines: list[str],
        items_dropped: list[dict[str, Any]],
    ):
        return (
            cls(character, combat)
            .with_message('\n'.join(message_lines))
            .with_victory()
            .with_items_dropped(items_dropped)
            .with_character()
            .build()
        )

    @classmethod
    def deeper_blocked(cls, character, combat: Combat):
        return (
            cls(character, combat)
            .with_message('You can only go deeper after defeating the enemy.')
            .with_character_health(combat.character_health)
            .build()
        )

    @classmethod
    def deeper_no_enemy(cls, character):
        return (
            cls(character, None)
            .with_message('No enemy types available')
            .with_combat(None)
            .with_character()
            .build()
        )

    @classmethod
    def deeper_success(cls, character, combat: Combat, next_combat: Combat, enemy_name: str):
        return (
            cls(character, next_combat)
            .with_message(
                'Sneaking!\n'
                f'You go deeper past the defeated {enemy_name}!\n'
                'A new enemy emerges from the shadows!'
            )
            .with_combat(next_combat)
            .with_character_health(combat.character_health)
            .build()
        )

    @classmethod
    def home_success(cls, character, combat: Combat):
        return (
            cls(character, combat)
            .with_message('You returned home with your spoils!')
            .with_success()
            .with_character()
            .build()
        )

    @classmethod
    def run_success(cls, character, combat: Combat, dice_roll: int):
        return (
            cls(character, combat)
            .with_message(MessageBuilder.escape_success(dice_roll))
            .with_success()
            .with_dice_roll(dice_roll)
            .with_character()
            .build()
        )

    @classmethod
    def run_failure(
        cls,
        character,
        combat: Combat,
        enemy_name: str,
        dice_roll: int,
        damage_taken: int,
        defeated: bool,
    ):
        builder = (
            cls(character, combat)
            .with_message(MessageBuilder.escape_failure(dice_roll, enemy_name, damage_taken, defeated))
            .with_failure(damage_taken)
            .with_dice_roll(dice_roll)
        )

        if defeated:
            return builder.with_defeat().with_character().build()

        return builder.with_character_health(combat.character_health).build()


def _victory_outcome(character, combat: Combat, player_hits: int) -> tuple[list[str], list[dict[str, Any]]]:
    """Build the victory response details after defeating an enemy.

    Args:
        character: The winning character.
        combat: The combat row that was just resolved.
        player_hits: The damage dealt by the player on the finishing turn.

    Returns:
        A tuple containing the message lines to display and the loot drops
        generated for the victory.
    """
    message_lines = MessageBuilder.victory(combat.enemy_name, player_hits)

    items_dropped = drop_loot(combat)
    if items_dropped:
        item_names = ', '.join(item['name'] for item in items_dropped)
        message_lines.append(f'You found {item_names}!')
        for item in items_dropped:
            add_inventory_item(character, item['id'], level=item['level'])

    _apply_victory_experience(character, combat, message_lines)
    return message_lines, items_dropped


def check_character_death(health: int) -> bool:
    """Return whether the character has died."""
    return health <= 0


def _resolve_attack_turn(character, combat: Combat) -> dict[str, Any]:
    """Resolve a single attack turn and return the resulting combat state.

    Args:
        character: The active character taking the attack action.
        combat: The combat row being updated.

    Returns:
        A structured outcome dictionary containing the updated combat state,
        character snapshot, message text, and outcome flags.
    """
    enemy_name = combat.enemy_name

    if combat.enemy_current_health <= 0:
        return OutcomeBuilder.attack_blocked(character, combat)

    effective_damage = character.damage + character.bonus_damage
    player_hits = _combat_damage_roll(effective_damage)
    monster_hits = _combat_damage_roll(combat.enemy_damage)

    combat.enemy_current_health = max(0, combat.enemy_current_health - player_hits)

    if combat.enemy_current_health > 0:
        combat.character_health = max(0, combat.character_health - monster_hits)
        if check_character_death(combat.character_health):
            character.health = combat.character_health
            return OutcomeBuilder.attack_defeat(character, combat, enemy_name)

        return OutcomeBuilder.attack_round(character, combat, enemy_name, player_hits, monster_hits)

    character.health = combat.character_health
    message_lines, items_dropped = _victory_outcome(character, combat, player_hits)

    return OutcomeBuilder.victory_outcome(character, combat, message_lines, items_dropped)


def _resolve_deeper_turn(character, combat: Combat) -> dict[str, Any]:
    """Advance to the next dungeon fight after defeating the current enemy.

    Args:
        character: The active character taking the action.
        combat: The cleared combat row.

    Returns:
        A structured outcome dictionary for the next combat state or an error
        response when the next enemy cannot be created.
    """
    enemy_name = combat.enemy_name
    if combat.enemy_current_health > 0:
        return OutcomeBuilder.deeper_blocked(character, combat)

    character.health = combat.character_health
    next_level = max(1, combat.enemy_level + 1)
    db.session.delete(combat)
    next_combat = create_new_combat(character, level=next_level)
    if not next_combat:
        return OutcomeBuilder.deeper_no_enemy(character)

    return OutcomeBuilder.deeper_success(character, combat, next_combat, enemy_name)


def _resolve_home_turn(character, combat: Combat) -> dict[str, Any]:
    """Resolve a go-home action after a victory.

    Args:
        character: The active character taking the action.
        combat: The combat row being cleared.

    Returns:
        A structured outcome dictionary that signals the player returned home
        successfully.
    """
    character.health = combat.character_health
    db.session.delete(combat)

    return OutcomeBuilder.home_success(character, combat)


def _resolve_run_turn(character, combat: Combat) -> dict[str, Any]:
    """Resolve a run attempt and return the resulting combat state.

    Args:
        character: The active character taking the run action.
        combat: The combat row being updated.

    Returns:
        A structured outcome dictionary containing the escape roll, damage
        taken when the escape fails, and the updated combat state.
    """
    enemy_name = combat.enemy_name
    dice_roll = random.randint(1, 6)

    if dice_roll >= 4:
        character.health = combat.character_health
        db.session.delete(combat)
        return OutcomeBuilder.run_success(character, combat, dice_roll)

    damage_taken = _combat_damage_roll(combat.enemy_damage)
    combat.character_health = max(0, combat.character_health - damage_taken)
    if check_character_death(combat.character_health):
        character.health = combat.character_health
        return OutcomeBuilder.run_failure(character, combat, enemy_name, dice_roll, damage_taken, True)

    return OutcomeBuilder.run_failure(character, combat, enemy_name, dice_roll, damage_taken, False)


def _apply_victory_experience(character, combat: Combat, message_lines: list[str]) -> None:
    """Grant victory XP and append any level-up messages.

    Args:
        character: The character receiving the experience.
        combat: The combat row that was resolved.
        message_lines: The message buffer to append experience text to.
    """
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
    """Create loot drops for a defeated encounter.

    Args:
        combat: The defeated combat row used to determine drop scaling.

    Returns:
        A list of serialized item templates with level adjustments applied.
    """
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


def build_combat_response(outcome: dict[str, Any]) -> Any:
    """Build the JSON payload returned by combat endpoints.

    Args:
        outcome: The structured combat result returned by the action helpers.

    Returns:
        A Flask JSON response containing the normalized combat payload.
    """
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

    return jsonify(payload)


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

        combat = create_new_combat(character)
        if not combat:
            return json_error('No enemy types available', 404)

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

        action_name = (action or '').lower().strip()
        if action_name == 'attack':
            outcome = _resolve_attack_turn(character, combat)
        elif action_name == 'deeper':
            outcome = _resolve_deeper_turn(character, combat)
        elif action_name == 'run':
            outcome = _resolve_run_turn(character, combat)
        elif action_name == 'home':
            if combat.enemy_current_health > 0:
                return json_error('You can only go home after defeating the enemy', 400)
            outcome = _resolve_home_turn(character, combat)
        else:
            return json_error('Invalid combat action', 400)

        if outcome['player_died']:
            db.session.delete(combat)
        elif outcome['victory']:
            character.health = outcome['character']['health']
        else:
            character.health = outcome['character']['health']

        db.session.commit()
        character_ids = [character.id] if character.id is not None else None
        invalidate_user_characters_cache(character.user_id, character_ids)
        if outcome['victory']:
            invalidate_user_inventory_cache(character.user_id)

        return build_combat_response(outcome)


def register_combat_resources(api):
    """Register combat routes on the provided API instance."""
    api.add_resource(
        CombatResource,
        '/combats',
        '/combats/<combat:combat>',
        '/combats/<combat:combat>/<string:action>',
    )
