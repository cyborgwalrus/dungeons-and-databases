from flask_sqlalchemy import SQLAlchemy
from enum import Enum
from sqlalchemy.orm import relationship, Mapped

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    username: Mapped[str] = db.Column(db.String(80), nullable=False, unique=True)
    password: Mapped[str] = db.Column(db.String(255), nullable=False)

    characters: Mapped[list['Character']] = relationship('Character', back_populates='user', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'characters': [character.to_dict() for character in self.characters],
        }


class Character(db.Model):
    __tablename__ = 'character'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(80), nullable=False)
    level: Mapped[int] = db.Column(db.Integer, nullable=False, default=1)
    health: Mapped[int] = db.Column(db.Integer, nullable=False, default=100)
    damage: Mapped[int] = db.Column(db.Integer, nullable=False, default=10)

    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user: Mapped['User'] = relationship('User', back_populates='characters')
    inventory: Mapped[list['Item']] = relationship('Item', back_populates='owner', cascade='all, delete-orphan')
    encounters: Mapped[list['Encounter']] = relationship('Encounter', back_populates='character', cascade='all, delete-orphan')

    @property
    def inventory_items(self):
        return [item for item in self.inventory if not item.is_equipped]

    @property
    def equipped_items(self):
        return [item for item in self.inventory if item.is_equipped]

    def inventory_to_dict(self):
        return [item.to_dict() for item in self.inventory_items]

    def equipment_to_dict(self):
        equipped_items = sorted(
            self.equipped_items,
            key=lambda item: (_slot_sort_key(item.slot), item.id or 0)
        )
        return [item.to_dict() for item in equipped_items]

    def get_total_bonus_health(self):
        return sum(item.current_health_bonus for item in self.equipped_items)

    def get_total_bonus_attack(self):
        return sum(item.current_damage_bonus for item in self.equipped_items)

    def to_dict(self, include_inventory=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'level': self.level,
            'health': self.health,
            'damage': self.damage,
            'bonus_health': self.get_total_bonus_health(),
            'bonus_damage': self.get_total_bonus_attack(),
        }
        if include_inventory:
            data['inventory'] = self.inventory_to_dict()
            data['equipped'] = self.equipment_to_dict()
        return data


class EnemyType(db.Model):
    __tablename__ = 'enemy_type'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(80), nullable=False)
    level: Mapped[int] = db.Column(db.Integer, nullable=False, default=1)
    description: Mapped[str | None] = db.Column(db.String(255))
    base_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    base_damage: Mapped[int] = db.Column(db.Integer, nullable=False)

    encounters: Mapped[list['Encounter']] = relationship('Encounter', back_populates='enemy_type')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'description': self.description,
            'base_health': self.base_health,
            'base_damage': self.base_damage,
        }


class Encounter(db.Model):
    __tablename__ = 'encounter'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    
    character_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    character: Mapped['Character'] = relationship('Character', back_populates='encounters')
    
    enemy_type_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('enemy_type.id'), nullable=False)
    enemy_type: Mapped['EnemyType'] = relationship('EnemyType', back_populates='encounters')
    enemy_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    enemy_damage: Mapped[int] = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'character_id': self.character_id,
            'enemy_type_id': self.enemy_type_id,
            'name': self.enemy_type.name,
            'health': self.enemy_health,
            'max_health': self.enemy_health,
            'damage': self.enemy_damage,
            'level': self.character.level,
            'description': self.enemy_type.description
        }


class ItemSlot(Enum):
    WEAPON = 'weapon'
    SHIELD = 'shield'
    ARMOR = 'armor'
    HELMET = 'helmet'
    RING = 'ring'
    NECKLACE = 'necklace'


ITEM_SLOT_ORDER = {
    ItemSlot.HELMET: 0,
    ItemSlot.ARMOR: 1,
    ItemSlot.WEAPON: 2,
    ItemSlot.SHIELD: 3,
    ItemSlot.RING: 4,
    ItemSlot.NECKLACE: 5,
}


def _slot_sort_key(slot):
    if slot is None:
        return 999
    return ITEM_SLOT_ORDER[slot]

class ItemType(db.Model):
    __tablename__ = 'item_type'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(80), nullable=False)
    description: Mapped[str] = db.Column(db.String(255), nullable=False)
    slot: Mapped[ItemSlot] = db.Column(db.Enum(ItemSlot, native_enum=False, validate_strings=True), nullable=False)
    base_health_bonus: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    base_damage_bonus: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)

    items: Mapped[list['Item']] = relationship('Item', back_populates='item_type')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'slot': self.slot.value if self.slot else None,
            'base_health_bonus': self.base_health_bonus,
            'base_damage_bonus': self.base_damage_bonus,
        }


class Item(db.Model):
    __tablename__ = 'item'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(80), nullable=False)
    level: Mapped[int] = db.Column(db.Integer, nullable=False, default=1)
    health_bonus: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    damage_bonus: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    is_equipped: Mapped[bool] = db.Column(db.Boolean, nullable=False, default=False)
    is_loot: Mapped[bool] = db.Column(db.Boolean, nullable=False, default=True)
    
    owner_id: Mapped[int | None] = db.Column(db.Integer, db.ForeignKey('character.id'))
    owner: Mapped['Character'] = relationship('Character', back_populates='inventory')
    
    item_type_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    item_type: Mapped['ItemType'] = relationship('ItemType', back_populates='items')

    @property
    def slot(self):
        return self.item_type.slot if self.item_type else None

    def to_dict(self):
        return {
            'id': self.id,
            'item_type_id': self.item_type_id,
            'owner_id': self.owner_id,
            'name': self.name,
            'level': self.level,
            'is_equipped': self.is_equipped,
            'slot': self.slot.value if self.slot else None,
            'is_loot': self.is_loot,
            'health_bonus': self.health_bonus,
            'damage_bonus': self.damage_bonus,
            'description': self.item_type.description if self.item_type else None,
            'item_type': self.item_type.to_dict() if self.item_type else None,
        }
