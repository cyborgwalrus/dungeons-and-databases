"""SQLModel request and response schemas for the backend API."""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class ModelSchema(SQLModel):  # pylint: disable=too-few-public-methods
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


class CombatEnemyResponse(ModelSchema):
    type_id: str
    name: str
    description: str | None
    level: int
    health: int
    max_health: int
    damage: int
    base_health: int
    base_damage: int


class CombatResponse(ModelSchema):
    id: int
    character_id: int
    character_health: int
    enemy: CombatEnemyResponse


class ItemResponse(ModelSchema):
    id: int
    name: str
    item_type_id: str
    level: int
    slot_type: str | None
    health: int
    damage: int


class EquipmentSlotResponse(ModelSchema):
    id: int
    character_id: int
    item_id: int
    slot_type: str | None