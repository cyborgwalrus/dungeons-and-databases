from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    characters = db.relationship('Character', back_populates='user', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
        }


class Character(db.Model):
    __tablename__ = 'character'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=1)
    health = db.Column(db.Integer, nullable=False, default=100)
    damage = db.Column(db.Integer, nullable=False, default=10)

    user = db.relationship('User', back_populates='characters')
    items = db.relationship('Item', back_populates='owner', cascade='all, delete-orphan')
    encounters = db.relationship('Encounter', back_populates='character', cascade='all, delete-orphan')

    @property
    def inventory_items(self):
        return [item for item in self.items if not item.is_equipped]

    @property
    def equipped_items(self):
        return [item for item in self.items if item.is_equipped]

    def get_inventory(self):
        return [
            {
                'inventory_id': item.id,
                'item': item.to_dict(),
                'equipped': item.is_equipped,
            }
            for item in self.inventory_items
        ]

    def get_equipped(self):
        equipped_items = sorted(
            self.equipped_items,
            key=lambda item: (item.slot if item.slot is not None else 999, item.id or 0)
        )
        return [
            {
                'slot': item.slot if item.slot is not None else slot,
                'item': item.to_dict(),
            }
            for slot, item in enumerate(equipped_items)
        ]

    def get_total_bonus_health(self):
        return sum(item.item_type.bonus_health if item.item_type else 0 for item in self.equipped_items)

    def get_total_bonus_attack(self):
        return sum(item.item_type.bonus_attack if item.item_type else 0 for item in self.equipped_items)

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
            data['inventory'] = self.get_inventory()
            data['equipped'] = self.get_equipped()
        return data


class EnemyType(db.Model):
    __tablename__ = 'enemy_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=1)
    description = db.Column(db.String(255))
    base_health = db.Column(db.Integer, nullable=False)
    base_damage = db.Column(db.Integer, nullable=False)

    encounters = db.relationship('Encounter', back_populates='enemy_type')

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

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    enemy_type_id = db.Column(db.Integer, db.ForeignKey('enemy_type.id'), nullable=False)
    
    enemy_health = db.Column(db.Integer, nullable=False)
    enemy_damage = db.Column(db.Integer, nullable=False)

    character = db.relationship('Character', back_populates='encounters')
    enemy_type = db.relationship('EnemyType', back_populates='encounters')

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


class ItemType(db.Model):
    __tablename__ = 'item_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    bonus_health = db.Column(db.Integer, nullable=False)
    bonus_attack = db.Column(db.Integer, nullable=False)

    items = db.relationship('Item', back_populates='item_type')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'bonus_health': self.bonus_health,
            'bonus_attack': self.bonus_attack,
        }


class Item(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('character.id'))
    level = db.Column(db.Integer, nullable=False, default=1)
    is_equipped = db.Column(db.Boolean, nullable=False, default=False)
    slot = db.Column(db.Integer)
    is_loot = db.Column(db.Boolean, nullable=False, default=False)

    item_type = db.relationship('ItemType', back_populates='items')
    owner = db.relationship('Character', back_populates='items')

    def to_dict(self):
        return {
            'id': self.id,
            'item_type_id': self.item_type_id,
            'owner_id': self.owner_id,
            'level': self.level,
            'is_equipped': self.is_equipped,
            'slot': self.slot,
            'is_loot': self.is_loot,
            'name': self.item_type.name if self.item_type else None,
            'description': self.item_type.description if self.item_type else None,
            'bonus_health': self.item_type.bonus_health if self.item_type else 0,
            'bonus_attack': self.item_type.bonus_attack if self.item_type else 0,
            'item_type': self.item_type.to_dict() if self.item_type else None,
        }


Player = Character
CurrentEncounter = Encounter
InventoryItem = Item
EquippedItem = Item
