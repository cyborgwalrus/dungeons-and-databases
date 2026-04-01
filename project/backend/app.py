from flask import Flask, jsonify
from flask_cors import CORS
import os

from database import db
from models import EnemyType, Item, Player
from player_routes import player_bp
from dungeon_routes import dungeon_bp
from inventory_routes import inventory_bp

app = Flask(__name__)
CORS(app)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "game.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(player_bp)
app.register_blueprint(dungeon_bp)
app.register_blueprint(inventory_bp)

# Ensure player exists before each request
@app.before_request
def ensure_player():
    player = Player.query.first()
    
    if not player:
        player = Player(health=100, damage=10, level=1)
        db.session.add(player)
        db.session.commit()

# Create tables and seed enemy types
with app.app_context():
    db.create_all()

    if EnemyType.query.count() == 0:
        enemies = [
            EnemyType(name='Goblin', base_health=20, base_damage=5, description='A small, green creature with sharp teeth'),
            EnemyType(name='Skeleton', base_health=30, base_damage=7, description='Bones held together by dark magic'),
            EnemyType(name='Orc', base_health=40, base_damage=10, description='A brutal warrior with immense strength'),
            EnemyType(name='Dark Mage', base_health=25, base_damage=12, description='A sorcerer wielding forbidden magic'),
            EnemyType(name='Troll', base_health=60, base_damage=8, description='A massive creature with regenerating flesh'),
            EnemyType(name='Dragon Whelp', base_health=50, base_damage=15, description='A young dragon with fiery breath')
        ]
        db.session.add_all(enemies)
        db.session.commit()
    
    if Item.query.count() == 0:
        items = [
            Item(name='Iron Sword', description='A basic iron sword', bonus_health=0, bonus_attack=5),
            Item(name='Steel Sword', description='A strong steel sword', bonus_health=0, bonus_attack=10),
            Item(name='Leather Armor', description='Basic leather protection', bonus_health=15, bonus_attack=0),
            Item(name='Steel Armor', description='Strong steel protection', bonus_health=25, bonus_attack=0),
            Item(name='Health Potion', description='Restores 50 health points', bonus_health=50, bonus_attack=0),
            Item(name='Mana Potion', description='Restores mana for spells', bonus_health=30, bonus_attack=5),
            Item(name='Gold Coin', description='A valuable gold coin', bonus_health=0, bonus_attack=0),
            Item(name='Enchanted Ring', description='Increases damage by 3', bonus_health=10, bonus_attack=3),
            Item(name='Shield', description='Defensive shield', bonus_health=20, bonus_attack=0),
        ]
        db.session.add_all(items)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
