"""Combat message and outcome helpers."""

from typing import Any

from backend.db.models import Character, Combat


def combat_victory_message(enemy_name: str, player_hits: int) -> list[str]:
    """Build the message shown after defeating an enemy."""
    return [
        'Victory!',
        f'You dealt {player_hits} damage and defeated the {enemy_name}!',
    ]


def combat_attack_round_message(enemy_name: str, player_hits: int, monster_hits: int) -> str:
    """Build the message shown after a normal attack exchange."""
    return (
        f'You dealt {player_hits} damage to {enemy_name}!\n'
        f'{enemy_name} dealt {monster_hits} damage to you!'
    )


def combat_defeat_message(enemy_name: str) -> str:
    """Build the message shown when the player is defeated."""
    return (
        'Defeat!\n'
        f'You have been defeated by {enemy_name}!\n'
        'You lost the loot from this dungeon run...'
    )


def combat_escape_success_message(dice_roll: int) -> str:
    """Build the message shown when the player escapes successfully."""
    return (
        f'You rolled a {dice_roll}! '
        'You successfully escaped and returned home!'
    )


def combat_escape_failure_message(
    dice_roll: int,
    enemy_name: str,
    damage_taken: int,
    defeated: bool,
) -> str:
    """Build the message shown when an escape attempt fails."""
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


def _character_snapshot(character: Character, *, health: int | None = None) -> dict[str, Any]:
    """Serialize the character, optionally overriding the reported health."""
    if health is None:
        return character.to_response().model_dump()
    return character.to_response(health=health).model_dump()


def _base_outcome(character: Character, combat: Combat | None) -> dict[str, Any]:
    """Create the shared combat outcome structure."""
    return {
        'message': '',
        'victory': False,
        'items_dropped': [],
        'player_died': False,
        'combat': combat,
        'character': _character_snapshot(character),
        'success': False,
        'damage': 0,
        'dice_roll': None,
    }


def _build_outcome(
    character: Character,
    combat: Combat | None,
    *,
    message: str,
    character_health: int | None = None,
    victory: bool = False,
    items_dropped: list[dict[str, Any]] | None = None,
    player_died: bool = False,
    success: bool = False,
    damage: int = 0,
    dice_roll: int | None = None,
    include_character: bool = False,
    next_combat: Combat | None = None,
) -> dict[str, Any]:
    """Build a combat outcome payload with the requested overrides."""
    outcome = _base_outcome(character, combat)
    outcome['message'] = message
    outcome['victory'] = victory
    outcome['items_dropped'] = items_dropped or []
    outcome['player_died'] = player_died
    outcome['success'] = success
    outcome['damage'] = damage
    outcome['dice_roll'] = dice_roll
    if next_combat is not None:
        outcome['combat'] = next_combat
    if include_character:
        outcome['character'] = _character_snapshot(character)
    elif character_health is not None:
        outcome['character'] = _character_snapshot(character, health=character_health)
    return outcome


def combat_attack_blocked_outcome(character: Character, combat: Combat) -> dict[str, Any]:
    """Build the outcome for an attack while the enemy is already defeated."""
    return _build_outcome(
        character,
        combat,
        message='You need to go deeper to face the next enemy.',
        character_health=combat.character_health,
    )


def combat_attack_defeat_outcome(character: Character, combat: Combat, enemy_name: str) -> dict[str, Any]:
    """Build the outcome for an attack that defeats the player."""
    return _build_outcome(
        character,
        combat,
        message=combat_defeat_message(enemy_name),
        character_health=combat.character_health,
        player_died=True,
    )


def combat_attack_round_outcome(
    character: Character,
    combat: Combat,
    enemy_name: str,
    player_hits: int,
    monster_hits: int,
) -> dict[str, Any]:
    """Build the outcome for a round where both combatants exchange blows."""
    return _build_outcome(
        character,
        combat,
        message=combat_attack_round_message(
            enemy_name,
            player_hits,
            monster_hits,
        ),
        character_health=combat.character_health,
    )


def combat_victory_outcome(
    character: Character,
    combat: Combat,
    message_lines: list[str],
    items_dropped: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the outcome for a victorious combat."""
    return _build_outcome(
        character,
        combat,
        message='\n'.join(message_lines),
        victory=True,
        items_dropped=items_dropped,
        include_character=True,
    )


def combat_deeper_blocked_outcome(character: Character, combat: Combat) -> dict[str, Any]:
    """Build the outcome for trying to go deeper too early."""
    return _build_outcome(
        character,
        combat,
        message='You can only go deeper after defeating the enemy.',
        character_health=combat.character_health,
    )


def combat_deeper_success_outcome(
    character: Character,
    combat: Combat,
    next_combat: Combat,
    enemy_name: str,
) -> dict[str, Any]:
    """Build the outcome for advancing to the next enemy."""
    return _build_outcome(
        character,
        combat,
        message=(
            'Sneaking!\n'
            f'You go deeper past the defeated {enemy_name}!\n'
            'A new enemy emerges from the shadows!'
        ),
        character_health=combat.character_health,
        next_combat=next_combat,
    )


def combat_home_success_outcome(character: Character, combat: Combat) -> dict[str, Any]:
    """Build the outcome for returning home after victory."""
    return _build_outcome(
        character,
        combat,
        message='You returned home with your spoils!',
        success=True,
        include_character=True,
    )


def combat_run_success_outcome(character: Character, combat: Combat, dice_roll: int) -> dict[str, Any]:
    """Build the outcome for a successful escape attempt."""
    return _build_outcome(
        character,
        combat,
        message=combat_escape_success_message(dice_roll),
        success=True,
        dice_roll=dice_roll,
        include_character=True,
    )


def combat_run_failure_outcome(
    character: Character,
    combat: Combat,
    enemy_name: str,
    dice_roll: int,
    damage_taken: int,
    defeated: bool,
) -> dict[str, Any]:
    """Build the outcome for a failed escape attempt."""
    return _build_outcome(
        character,
        combat,
        message=combat_escape_failure_message(dice_roll, enemy_name, damage_taken, defeated),
        character_health=None if defeated else combat.character_health,
        player_died=defeated,
        success=False,
        damage=damage_taken,
        dice_roll=dice_roll,
        include_character=defeated,
    )
