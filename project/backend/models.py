from database import db


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    health = db.Column(db.Integer, default=100)
    damage = db.Column(db.Integer, default=10)
    level = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id': self.id,
            'health': self.health,
            'damage': self.damage,
            'level': self.level
        }


class EnemyType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    base_health = db.Column(db.Integer, nullable=False)
    base_damage = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))

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

    enemy_type = db.relationship('EnemyType', backref='encounters')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.enemy_type.name,
            'health': self.current_health,
            'max_health': self.max_health,
            'damage': self.damage,
            'description': self.enemy_type.description
        }
