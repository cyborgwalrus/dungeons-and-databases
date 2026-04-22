"""SQLModel request and response schemas for the backend API."""

from __future__ import annotations

from enum import Enum
from typing import ClassVar

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class ItemSlot(str, Enum):
    """Equipment slot categories used by items and character gear."""

    WEAPON = 'weapon'
    SHIELD = 'shield'
    ARMOR = 'armor'
    HELMET = 'helmet'
    RING = 'ring'
    NECKLACE = 'necklace'


class ModelSchema(SQLModel):
    """Common schema configuration shared by request and response models."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class AuthCredentials(ModelSchema):
    """Validated payload for signup and signin requests."""

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=255)


class UserUpdateRequest(ModelSchema):
    """Validated payload for updating a user profile."""

    username: str | None = Field(default=None, min_length=1, max_length=80)
    password: str | None = Field(default=None, min_length=1, max_length=255)


class CharacterCreateRequest(ModelSchema):
    """Validated payload for creating a character."""

    name: str | None = Field(default=None, min_length=1, max_length=80)
    level: int = Field(default=1, ge=1)
    health: int = Field(default=100, ge=0)
    damage: int = Field(default=10, ge=0)


class CharacterUpdateRequest(ModelSchema):
    """Validated payload for updating a character."""

    health: int | None = Field(default=None, ge=0)
    damage: int | None = Field(default=None, ge=0)
    level: int | None = Field(default=None, ge=1)


class ItemCreateRequest(ModelSchema):
    """Validated payload for creating inventory items from a template ID."""

    item_type_id: str = Field(min_length=1, max_length=80)


class ItemSelectionRequest(ModelSchema):
    """Validated payload for selecting an inventory item."""

    item_id: int = Field(ge=1)


class UserResponse(ModelSchema):
    id: int
    username: str


class CharacterResponse(ModelSchema):
    id: int
    user_id: int
    name: str
    level: int
    experience: int
    experience_to_next_level: int
    max_health: int
    health: int
    damage: int
    bonus_health: int
    bonus_damage: int


class EncounterResponse(ModelSchema):
    id: int
    character_id: int
    enemy_template_id: str
    enemy_name: str
    enemy_description: str | None
    enemy_base_health: int
    enemy_base_damage: int
    level: int


class CombatResponse(ModelSchema):
    id: int
    encounter_id: int
    character_id: int
    character_health: int
    enemy_current_health: int
    enemy_max_health: int
    enemy_damage: int


class ItemResponse(ModelSchema):
    id: int
    name: str
    item_type_id: str
    level: int
    slot: str | None
    is_loot: bool
    health: int
    damage: int


class CharacterEquipmentResponse(ModelSchema):
    id: int
    character_id: int
    item_id: int
    slot: str | None