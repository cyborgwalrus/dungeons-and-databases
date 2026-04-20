from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import Sequence

from .models import EnemyType, ItemSlot, ItemType, db


@dataclass(frozen=True, slots=True)
class SeedRecord(ABC):
    @abstractmethod
    def model_kwargs(self) -> dict[str, object]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class EnemyTypeSeed(SeedRecord):
    name: str
    health: int
    damage: int
    description: str

    def model_kwargs(self) -> dict[str, object]:
        return {
            'name': self.name,
            'health': self.health,
            'damage': self.damage,
            'description': self.description,
        }


@dataclass(frozen=True, slots=True)
class ItemTypeSeed(SeedRecord):
    name: str
    slot: ItemSlot
    health: int
    damage: int

    def model_kwargs(self) -> dict[str, object]:
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
    ItemTypeSeed('Leather Armor', ItemSlot.ARMOR, 15, 0),
    ItemTypeSeed('Steel Armor', ItemSlot.ARMOR, 25, 0),
    ItemTypeSeed('Iron Helmet', ItemSlot.HELMET, 8, 0),
    ItemTypeSeed('Silver Necklace', ItemSlot.NECKLACE, 5, 2),
    ItemTypeSeed('Enchanted Ring', ItemSlot.RING, 10, 3),
    ItemTypeSeed('Iron Shield', ItemSlot.SHIELD, 20, 0),
]


def _seed_table(model_cls, seeds: Sequence[SeedRecord]) -> None:
    if model_cls.query.count() != 0:
        return

    db.session.add_all([model_cls(**seed.model_kwargs()) for seed in seeds])
    db.session.commit()


def seed_initial_data():
    _seed_table(EnemyType, ENEMY_TYPES)
    _seed_table(ItemType, ITEM_TYPES)