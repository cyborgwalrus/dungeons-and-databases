"""Enum constants shared across backend domain models and schemas."""

from enum import Enum


class UserState(str, Enum):
    """Tracked user state values."""

    LOGGED_OUT = 'LOGGED_OUT'
    LOGGED_IN = 'LOGGED_IN'
    CHARACTER_SELECTED = 'CHARACTER_SELECTED'


class CharacterState(str, Enum):
    """Tracked character state values."""

    HOME = 'HOME'
    DUNGEON_COMBAT = 'DUNGEON_COMBAT'
    DUNGEON_VICTORY = 'DUNGEON_VICTORY'


class ItemSlot(str, Enum):
    """Supported equipment and item slot types."""

    WEAPON = 'weapon'
    SHIELD = 'shield'
    ARMOR = 'armor'
    HELMET = 'helmet'
    RING = 'ring'
    NECKLACE = 'necklace'
