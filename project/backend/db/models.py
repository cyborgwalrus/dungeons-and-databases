from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, Mapped

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    username: Mapped[str] = db.Column(db.String(80), nullable=False, unique=True)
    password: Mapped[str] = db.Column(db.String(255), nullable=False)

    characters: Mapped[list['Character']] = relationship('Character', back_populates='user', cascade='all, delete-orphan')
    inventory: Mapped['UserInventory'] = relationship('UserInventory', back_populates='user', uselist=False, cascade='all, delete-orphan')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'characters': [character.to_dict() for character in self.characters],
        }


class UserInventory(db.Model):
    __tablename__ = 'user_inventory'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    user: Mapped['User'] = relationship('User', back_populates='inventory')
    items: Mapped[list['Item']] = relationship('Item', back_populates='inventory', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': [item.to_dict() for item in self.items],
        }


class Character(db.Model):
    __tablename__ = 'character'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(80), nullable=False)
    level: Mapped[int] = db.Column(db.Integer, nullable=False, default=1)
    experience: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    health: Mapped[int] = db.Column(db.Integer, nullable=False, default=100)
    damage: Mapped[int] = db.Column(db.Integer, nullable=False, default=10)

    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user: Mapped['User'] = relationship('User', back_populates='characters')
    equipment: Mapped[list['CharacterEquipment']] = relationship('CharacterEquipment', back_populates='character', cascade='all, delete-orphan')
    encounters: Mapped[list['Encounter']] = relationship('Encounter', back_populates='character', cascade='all, delete-orphan')

    @property
    def inventory_items(self):
        if not self.user or not self.user.inventory:
            return []
        return list(self.user.inventory.items)

    @property
    def equipped_items(self):
        return [equipment.item for equipment in self.equipment if equipment.item]

    @property
    def inventory(self):
        return self.inventory_items

    def inventory_to_dict(self):
        return [item.to_dict() for item in self.inventory_items]

    def equipment_to_dict(self):
        equipped_items = sorted(
            [equipment for equipment in self.equipment if equipment.item],
            key=lambda equipment: (_slot_sort_key(equipment.slot), equipment.item.id or 0)
        )
        return [equipment.item.to_dict() for equipment in equipped_items if equipment.item]

    @property
    def bonus_health(self):
        return sum(item.health_bonus or 0 for item in self.equipped_items)

    @property
    def bonus_damage(self):
        return sum(item.damage_bonus or 0 for item in self.equipped_items)

    @staticmethod
    def _max_health_for_level(level: int) -> int:
        return 100 + (max(0, level - 1) * 10)

    @property
    def max_health(self):
        return self._max_health_for_level(self.level) + self.bonus_health

    @property
    def experience_to_next_level(self):
        return 100 + (max(0, self.level - 1) * 50)

    def gain_experience(self, amount: int) -> int:
        if amount <= 0:
            return 0
        self.experience += amount
        return amount

    def can_level_up(self):
        return self.experience >= self.experience_to_next_level

    def level_up(self):
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

    def to_dict(self, include_inventory=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'level': self.level,
            'experience': self.experience,
            'experience_to_next_level': self.experience_to_next_level,
            'max_health': self.max_health,
            'health': self.health,
            'damage': self.damage,
            'bonus_health': self.bonus_health,
            'bonus_damage': self.bonus_damage,
        }
        if include_inventory:
            data['inventory'] = self.inventory_to_dict()
            data['equipped'] = self.equipment_to_dict()
        return data


class EnemyType(db.Model):
    __tablename__ = 'enemy_type'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(80), nullable=False)
    description: Mapped[str | None] = db.Column(db.String(255))
    base_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    base_damage: Mapped[int] = db.Column(db.Integer, nullable=False)

    encounters: Mapped[list['Encounter']] = relationship('Encounter', back_populates='enemy_type')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
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
    enemy_level: Mapped[int] = db.Column(db.Integer, nullable=False, default=1)
    enemy_max_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    enemy_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    enemy_damage: Mapped[int] = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'character_id': self.character_id,
            'enemy_type_id': self.enemy_type_id,
            'name': self.enemy_type.name,
            'health': self.enemy_health,
            'max_health': self.enemy_max_health,
            'damage': self.enemy_damage,
            'level': self.enemy_level,
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
    slot: Mapped[ItemSlot] = db.Column(
        db.Enum(
            ItemSlot,
            native_enum=False,
            validate_strings=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    base_health_bonus: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    base_damage_bonus: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)

    items: Mapped[list['Item']] = relationship('Item', back_populates='item_type')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
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
    is_loot: Mapped[bool] = db.Column(db.Boolean, nullable=False, default=True)
    
    inventory_id: Mapped[int | None] = db.Column(db.Integer, db.ForeignKey('user_inventory.id'))
    inventory: Mapped['UserInventory'] = relationship('UserInventory', back_populates='items')
    
    item_type_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    item_type: Mapped['ItemType'] = relationship('ItemType', back_populates='items')
    equipment: Mapped['CharacterEquipment'] = relationship('CharacterEquipment', back_populates='item', uselist=False)

    @property
    def slot(self):
        return self.item_type.slot if self.item_type else None

    @property
    def owner_id(self):
        if self.inventory:
            return self.inventory.user_id
        if self.equipment and self.equipment.character:
            return self.equipment.character.user_id
        return None

    @property
    def equipped_slot(self):
        return self.equipment.slot if self.equipment else None

    @property
    def is_equipped(self):
        return self.equipment is not None

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
            'item_type': self.item_type.to_dict() if self.item_type else None,
        }


class CharacterEquipment(db.Model):
    __tablename__ = 'character_equipment'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    character_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    item_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False, unique=True)
    slot: Mapped[ItemSlot] = db.Column(
        db.Enum(
            ItemSlot,
            native_enum=False,
            validate_strings=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    character: Mapped['Character'] = relationship('Character', back_populates='equipment')
    item: Mapped['Item'] = relationship('Item', back_populates='equipment', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'character_id': self.character_id,
            'item_id': self.item_id,
            'slot': self.slot.value if self.slot else None,
            'item': self.item.to_dict() if self.item else None,
        }