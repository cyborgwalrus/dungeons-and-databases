from database import db


class Player(db.Model):
    __allow_unmapped__ = True

    id = db.Column(db.Integer, primary_key=True)
    health = db.Column(db.Integer, default=100)
    damage = db.Column(db.Integer, default=10)
    level = db.Column(db.Integer, default=1)
    
    inventory_items: list['InventoryItem'] = db.relationship('InventoryItem', back_populates='player', cascade='all, delete-orphan')  # type: ignore[assignment]
    equipped_items: list['EquippedItem'] = db.relationship('EquippedItem', back_populates='player', cascade='all, delete-orphan')  # type: ignore[assignment]

    def to_dict(self, include_inventory=False):
        data = {
            'id': self.id,
            'health': self.health,
            'damage': self.damage,
            'level': self.level,
            'bonus_health': self.get_total_bonus_health(),
            'bonus_damage': self.get_total_bonus_attack(),
        }
        if include_inventory:
            data['inventory'] = [item.to_dict() for item in self.inventory_items]
            data['equipped'] = [eq.to_dict() for eq in self.equipped_items]
        return data
    
    def get_inventory(self):
        return [item.to_dict() for item in self.inventory_items]
    
    def get_equipped(self):
        return [eq.to_dict() for eq in self.equipped_items]
    
    def get_total_bonus_health(self):
        return sum(eq.item.bonus_health for eq in self.equipped_items)
    
    def get_total_bonus_attack(self):
        return sum(eq.item.bonus_attack for eq in self.equipped_items)


class EnemyType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    base_health = db.Column(db.Integer, nullable=False)
    base_damage = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    
    encounters = db.relationship('CurrentEncounter', back_populates='enemy_type')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'base_health': self.base_health,
            'base_damage': self.base_damage,
            'description': self.description
        }


class CurrentEncounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enemy_type_id = db.Column(db.Integer, db.ForeignKey('enemy_type.id'), nullable=False)
    current_health = db.Column(db.Integer, nullable=False)
    max_health = db.Column(db.Integer, nullable=False)
    damage = db.Column(db.Integer, nullable=False)
    level = db.Column(db.Integer, default=1, nullable=False)

    enemy_type = db.relationship('EnemyType', back_populates='encounters')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.enemy_type.name,
            'health': self.current_health,
            'max_health': self.max_health,
            'damage': self.damage,
            'level': self.level,
            'description': self.enemy_type.description
        }

class Item(db.Model):
    """Defines item types that can be found in the dungeon"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    
    bonus_health = db.Column(db.Integer, nullable=False)
    bonus_attack = db.Column(db.Integer, nullable=False)
    

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'bonus_health': self.bonus_health,
            'bonus_attack': self.bonus_attack
        }


class InventoryItem(db.Model):
    """Tracks items in player inventory."""
    __tablename__ = "inventory_item"
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    
    player = db.relationship('Player', back_populates='inventory_items')
    item = db.relationship('Item')
    
    def to_dict(self):
        return {
            'id': self.id,
            'item': self.item.to_dict()
        }


class EquippedItem(db.Model):
    """Tracks equipped items (max 6 slots)"""
    __tablename__ = "equipped_item"
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    slot = db.Column(db.Integer, default=0, nullable=False)  # 0-5 for 6 slots
    
    player = db.relationship('Player', back_populates='equipped_items')
    item = db.relationship('Item')
    
    def to_dict(self):
        return {
            'id': self.id,
            'item': self.item.to_dict(),
            'slot': self.slot
        }
