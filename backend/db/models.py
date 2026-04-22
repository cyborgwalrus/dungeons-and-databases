from enum import Enum

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, relationship

db = SQLAlchemy()

class User(db.Model):
    """Authenticated account that owns characters and items."""
    __tablename__ = 'user'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    username: Mapped[str] = db.Column(db.String(80), nullable=False, unique=True)
    password: Mapped[str] = db.Column(db.String(255), nullable=False)

    characters: Mapped[list['Character']] = relationship('Character', back_populates='user', cascade='all, delete-orphan')
    items: Mapped[list['Item']] = relationship('Item', back_populates='user', cascade='all, delete-orphan')

    def to_dict(self):
        """Serialize the user together with their owned characters."""
        return {
            'id': self.id,
            'username': self.username,
        }


class Character(db.Model):
    """Playable character tied to a user and combat progression state."""
    __tablename__ = 'character'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(80), nullable=False)
    level: Mapped[int] = db.Column(db.Integer, nullable=False, default=1)
    experience: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    health: Mapped[int] = db.Column(db.Integer, nullable=False, default=100)
    damage: Mapped[int] = db.Column(db.Integer, nullable=False, default=10)

    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    user: Mapped['User'] = relationship('User', back_populates='characters')
    equipment: Mapped[list['CharacterEquipment']] = relationship('CharacterEquipment', back_populates='character', cascade='all, delete-orphan')
    encounters: Mapped[list['Encounter']] = relationship('Encounter', back_populates='character', cascade='all, delete-orphan')

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

    def to_dict(self):
        """Serialize the character into a lean API payload."""
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
        return data


class Encounter(db.Model):
    """Active dungeon encounter tied to a character and enemy template."""
    __tablename__ = 'encounter'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)

    character_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False, index=True)
    character: Mapped['Character'] = relationship('Character', back_populates='encounters')

    combat: Mapped['Combat'] = relationship('Combat', back_populates='encounter', cascade='all, delete-orphan', uselist=False, single_parent=True)

    enemy_template_id: Mapped[str] = db.Column(db.String(80), nullable=False, index=True)
    enemy_name: Mapped[str] = db.Column(db.String(80), nullable=False)
    enemy_description: Mapped[str | None] = db.Column(db.String(255))
    enemy_base_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    enemy_base_damage: Mapped[int] = db.Column(db.Integer, nullable=False)
    enemy_level: Mapped[int] = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self):
        """Serialize the static encounter data for the client."""
        return {
            'id': self.id,
            'character_id': self.character_id,
            'enemy_template_id': self.enemy_template_id,
            'enemy_name': self.enemy_name,
            'enemy_description': self.enemy_description,
            'enemy_base_health': self.enemy_base_health,
            'enemy_base_damage': self.enemy_base_damage,
            'level': self.enemy_level,
        }


class Combat(db.Model):
    """Volatile player combat state attached to a single encounter."""
    __tablename__ = 'combat'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    encounter_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('encounter.id'), nullable=False, unique=True, index=True)
    character_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False, index=True)
    character_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    enemy_current_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    enemy_max_health: Mapped[int] = db.Column(db.Integer, nullable=False)
    enemy_damage: Mapped[int] = db.Column(db.Integer, nullable=False)

    encounter: Mapped['Encounter'] = relationship('Encounter', back_populates='combat')
    character: Mapped['Character'] = relationship('Character')

    def to_dict(self):
        """Serialize the live combat state for the client."""
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'character_id': self.character_id,
            'character_health': self.character_health,
            'enemy_current_health': self.enemy_current_health,
            'enemy_max_health': self.enemy_max_health,
            'enemy_damage': self.enemy_damage,
        }

    def to_character_dict(self, character: 'Character'):
        """Return a combat snapshot using the persisted character plus the live encounter health."""
        data = character.to_dict()
        data['health'] = self.character_health
        return data


class ItemSlot(Enum):
    """Equipment slot categories used by items and character gear."""
    WEAPON = 'weapon'
    SHIELD = 'shield'
    ARMOR = 'armor'
    HELMET = 'helmet'
    RING = 'ring'
    NECKLACE = 'necklace'

class Item(db.Model):
    """Concrete item instance held in inventory or equipped by a character."""
    __tablename__ = 'item'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(80), nullable=False)
    item_type_id: Mapped[str] = db.Column(db.String(80), nullable=False, index=True)
    slot: Mapped[ItemSlot] = db.Column(
        db.Enum(
            ItemSlot,
            native_enum=False,
            validate_strings=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    level: Mapped[int] = db.Column(db.Integer, nullable=False, default=1)
    health: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    damage: Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    is_loot: Mapped[bool] = db.Column(db.Boolean, nullable=False, default=True)

    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    user: Mapped['User'] = relationship('User', back_populates='items')

    equipment: Mapped['CharacterEquipment'] = relationship('CharacterEquipment', back_populates='item', uselist=False, cascade='all, delete-orphan', single_parent=True)

    @property
    def is_equipped(self):
        """Return whether the item is currently equipped."""
        return self.equipment is not None

    def to_dict(self):
        """Serialize the item for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'item_type_id': self.item_type_id,
            'level': self.level,
            'slot': self.slot.value if self.slot else None,
            'is_loot': self.is_loot,
            'health': self.health,
            'damage': self.damage,
        }


class CharacterEquipment(db.Model):
    """Join model linking a character to a single equipped item slot."""
    __tablename__ = 'character_equipment'

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    character_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False, index=True)
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