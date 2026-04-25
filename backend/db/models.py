"""SQLModel table models for users, characters, combat, and items."""

from typing import Any, ClassVar, Optional, cast

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from backend.db.schemas import (
    EquipmentSlotResponse,
    CharacterResponse,
    CombatResponse,
    ItemResponse,
    UserResponse,
)
from backend.db.enums import CharacterState, ItemSlot, UserState

class ModelBase(SQLModel):
    """Common base model with a compatibility query property."""
    model_config: ClassVar[Any] = {
        'arbitrary_types_allowed': True,
        'from_attributes': True,
        'use_enum_values': True,
    }


class User(ModelBase, table=True):
    """Authenticated account that owns characters and items."""

    __tablename__: ClassVar[str] = 'user'

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=80)
    password: str = Field(max_length=255)
    state: UserState = Field(default=UserState.LOGGED_OUT)

    characters: list['Character'] = Relationship(
        back_populates='user',
        sa_relationship_kwargs={'cascade': 'all, delete-orphan'},
    )
    items: list['Item'] = Relationship(
        back_populates='user',
        sa_relationship_kwargs={'cascade': 'all, delete-orphan'},
    )

    def to_response(self) -> UserResponse:
        """Return the user response representation."""
        return UserResponse.model_validate(self)

    def owns_character(self, character_id: int) -> bool:
        """Return whether the user owns the requested character."""
        return any(character.id == character_id for character in self.characters)


class Character(ModelBase, table=True):
    """Playable character tied to a user and combat progression state."""

    __tablename__: ClassVar[str] = 'character'

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id', index=True)
    name: str = Field(max_length=80)
    level: int = Field(default=1, ge=1)
    experience: int = Field(default=0, ge=0)
    health: int = Field(default=100, ge=0)
    damage: int = Field(default=10, ge=0)
    state: CharacterState = Field(default=CharacterState.HOME)

    user: User = Relationship(back_populates='characters')
    equipment: list['EquipmentSlot'] = Relationship(
        back_populates='character',
        sa_relationship_kwargs={'cascade': 'all, delete-orphan'},
    )

    @property
    def equipped_items(self):
        """Return the items currently equipped by this character."""
        return [equipment.item for equipment in self.equipment if equipment.item]

    @property
    def bonus_health(self):
        """Return the total health bonus from equipped items."""
        return sum(item.health or 0 for item in self.equipped_items)

    @property
    def bonus_damage(self):
        """Return the total damage bonus from equipped items."""
        return sum(item.damage or 0 for item in self.equipped_items)

    @staticmethod
    def _max_health_for_level(level: int) -> int:
        """Return the base max health value for a given character level."""
        return 100 + (max(0, level - 1) * 10)

    @property
    def max_health(self):
        """Return the current max health including gear bonuses."""
        return self._max_health_for_level(self.level) + self.bonus_health

    @property
    def experience_to_next_level(self):
        """Return the XP threshold for the next level."""
        return 100 + (max(0, self.level - 1) * 50)

    def to_response(self, *, health: int | None = None) -> CharacterResponse:
        """Return the character response representation."""
        response_character = CharacterResponse.model_validate(self)
        if health is not None:
            response_character = response_character.model_copy(update={'health': health})
        return response_character

    def gain_experience(self, amount: int) -> int:
        """Add positive XP to the character and return the applied amount."""
        if amount <= 0:
            return 0
        self.experience += amount
        return amount

    def can_level_up(self):
        """Return whether the character has enough XP to level up."""
        return self.experience >= self.experience_to_next_level

    def level_up(self):
        """Spend XP to raise the character level and improve core stats."""
        if not self.can_level_up():
            return False

        self.experience -= self.experience_to_next_level
        next_level = self.level + 1
        next_max_health = self._max_health_for_level(next_level) + self.bonus_health
        damage_gain = 3 + max(0, (next_level - 1) // 6)
        health_gain = 6 + (max(0, (next_level - 1) // 4) * 2)

        self.level = next_level
        self.damage += damage_gain
        self.health = min(self.health + health_gain, next_max_health)
        return True


class ItemType(ModelBase, table=True):
    """Static item template stored in the database."""

    __tablename__: ClassVar[str] = 'item_type'

    id: str = Field(primary_key=True, max_length=80)
    name: str = Field(max_length=80)
    slot_type: ItemSlot
    health: int = Field(default=0, ge=0)
    damage: int = Field(default=0, ge=0)


class EnemyType(ModelBase, table=True):
    """Static enemy template stored in the database."""

    __tablename__: ClassVar[str] = 'enemy_type'

    id: str = Field(primary_key=True, max_length=80)
    name: str = Field(max_length=80)
    description: str | None = Field(default=None, max_length=255)
    base_health: int = Field(default=0, ge=0)
    base_damage: int = Field(default=0, ge=0)


class Combat(ModelBase, table=True):
    """Volatile player combat state for a dungeon run."""

    __tablename__: ClassVar[str] = 'combat'
    __table_args__ = {'sqlite_autoincrement': True}

    id: int | None = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key='character.id', index=True, unique=True)
    enemy_type_id: str = Field(foreign_key='enemy_type.id', max_length=80, index=True)
    enemy_level: int = Field(default=1, ge=1)
    character_health: int = Field(ge=0)
    enemy_current_health: int = Field(ge=0)
    enemy_max_health: int = Field(ge=0)
    enemy_damage: int = Field(ge=0)

    character: Character = Relationship()
    enemy_type: EnemyType = Relationship()

    def to_response(self) -> CombatResponse:
        """Return the combat response representation."""
        return CombatResponse.model_validate(self)

    @property
    def enemy(self) -> dict[str, Any]:
        """Return a presentation-friendly snapshot of the current enemy."""
        enemy_type = cast(EnemyType | None, getattr(self, 'enemy_type', None))
        return {
            'type_id': self.enemy_type_id,
            'name': enemy_type.name if enemy_type else '',
            'description': enemy_type.description if enemy_type else None,
            'level': self.enemy_level,
            'health': self.enemy_current_health,
            'max_health': self.enemy_max_health,
            'damage': self.enemy_damage,
            'base_health': enemy_type.base_health if enemy_type else 0,
            'base_damage': enemy_type.base_damage if enemy_type else 0,
        }


class Item(ModelBase, table=True):
    """Concrete item instance held in inventory or equipped by a character."""

    __tablename__: ClassVar[str] = 'item'

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id', index=True)
    name: str = Field(max_length=80)
    item_type_id: str = Field(foreign_key='item_type.id', max_length=80, index=True)
    slot_type: ItemSlot
    level: int = Field(default=1, ge=1)
    health: int = Field(default=0, ge=0)
    damage: int = Field(default=0, ge=0)

    user: User = Relationship(back_populates='items')
    equipment: Optional['EquipmentSlot'] = Relationship(
        back_populates='item',
        sa_relationship_kwargs={
            'uselist': False,
            'cascade': 'all, delete-orphan',
            'single_parent': True,
        },
    )

    @property
    def is_equipped(self):
        """Return whether the item is currently equipped."""
        return self.equipment is not None

    def to_response(self) -> ItemResponse:
        """Return the item response representation."""
        return ItemResponse.model_validate(self)


class EquipmentSlot(ModelBase, table=True):
    """Join model linking a character to a single equipped item slot."""

    __tablename__: ClassVar[str] = 'character_equipment'
    __table_args__ = (
        UniqueConstraint('character_id', 'slot_type', name='uq_character_equipment_character_slot'),
    )

    id: int | None = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key='character.id', index=True)
    item_id: int = Field(foreign_key='item.id', unique=True)
    slot_type: ItemSlot

    character: Character = Relationship(
        back_populates='equipment'
    )
    item: Item = Relationship(
        back_populates='equipment',
        sa_relationship_kwargs={'uselist': False},
    )

    def to_response(self) -> EquipmentSlotResponse:
        """Return the equipment response representation."""
        return EquipmentSlotResponse.model_validate(self)

    def matches_item(self, item_id: int) -> bool:
        """Return whether this record points to the requested item."""
        return self.item_id == item_id
