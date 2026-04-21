from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import Sequence

from .models import EnemyType, ItemSlot, ItemType, db


@dataclass(frozen=True, slots=True)
class SeedRecord(ABC):
    """Base type for database seed definitions."""

    @abstractmethod
    def model_kwargs(self) -> dict[str, object]:
        """Return keyword arguments for constructing a model instance."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class EnemyTypeSeed(SeedRecord):
    """Seed data for an enemy type row."""
    name: str
    health: int
    damage: int
    description: str

    def model_kwargs(self) -> dict[str, object]:
        """Return keyword arguments for the enemy type model."""
        return {
            'name': self.name,
            'health': self.health,
            'damage': self.damage,
            'description': self.description,
        }


@dataclass(frozen=True, slots=True)
class ItemTypeSeed(SeedRecord):
    """Seed data for an item type row."""
    name: str
    slot: ItemSlot
    health: int
    damage: int

    def model_kwargs(self) -> dict[str, object]:
        """Return keyword arguments for the item type model."""
        return {
            'name': self.name,
            'slot': self.slot.value,
            'health': self.health,
            'damage': self.damage,
        }


ENEMY_TYPES = [
    EnemyTypeSeed('Goblin', 20, 5, 'A weak goblin'),
    EnemyTypeSeed('Slime', 14, 4, 'A sticky slime'),
    EnemyTypeSeed('Skeleton', 18, 6, 'A rattling skeleton'),
    EnemyTypeSeed('Wolf', 22, 7, 'A hungry wolf'),
    EnemyTypeSeed('Orc', 35, 8, 'A brutish orc'),
    EnemyTypeSeed('Bandit', 28, 9, 'A road bandit'),
    EnemyTypeSeed('Mage', 24, 11, 'A rogue mage'),
]

ITEM_TYPES = [
    ItemTypeSeed('Steel Sword', ItemSlot.WEAPON, 0, 10),
    ItemTypeSeed('Steel Armor', ItemSlot.ARMOR, 10, 0),
    ItemTypeSeed('Iron Helmet', ItemSlot.HELMET, 8, 0),
    ItemTypeSeed('Silver Necklace', ItemSlot.NECKLACE, 5, 4),
    ItemTypeSeed('Enchanted Ring', ItemSlot.RING, 4, 5),
    ItemTypeSeed('Iron Shield', ItemSlot.SHIELD, 9, 0),
]


def _seed_table(model_cls, seeds: Sequence[SeedRecord]) -> None:
    """Insert seed rows only when the target table is empty."""
    if model_cls.query.count() != 0:
        return

    db.session.add_all([model_cls(**seed.model_kwargs()) for seed in seeds])
    db.session.commit()


def seed_initial_data():
    """Seed the database with the default enemy and item reference data."""
    _seed_table(EnemyType, ENEMY_TYPES)
    _seed_table(ItemType, ITEM_TYPES)