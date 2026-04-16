from flask import Flask
from flask_cors import CORS
import os

from models import db
from models import Character, EnemyType, Item, ItemType, User
from game_utils import add_inventory_item, clear_player_equipment, clear_player_inventory, get_player
from sqlalchemy.exc import SQLAlchemyError
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

ENEMY_SEEDS = [
    {'name': 'Goblin', 'base_health': 20, 'base_damage': 5, 'description': 'A small, green creature with sharp teeth'},
    {'name': 'Skeleton', 'base_health': 30, 'base_damage': 7, 'description': 'Bones held together by dark magic'},
    {'name': 'Orc', 'base_health': 40, 'base_damage': 10, 'description': 'A brutal warrior with immense strength'},
    {'name': 'Dark Mage', 'base_health': 25, 'base_damage': 12, 'description': 'A sorcerer wielding forbidden magic'},
    {'name': 'Troll', 'base_health': 60, 'base_damage': 8, 'description': 'A massive creature with regenerating flesh'},
    {'name': 'Dragon Whelp', 'base_health': 50, 'base_damage': 15, 'description': 'A young dragon with fiery breath'},
]

ITEM_TYPE_SEEDS = [
    {'name': 'Steel Sword', 'description': 'A strong steel sword', 'bonus_health': 0, 'bonus_attack': 10},
    {'name': 'Leather Armor', 'description': 'Basic leather protection', 'bonus_health': 15, 'bonus_attack': 0},
    {'name': 'Steel Armor', 'description': 'Strong steel protection', 'bonus_health': 25, 'bonus_attack': 0},
    {'name': 'Iron Helmet', 'description': 'A sturdy helmet', 'bonus_health': 8, 'bonus_attack': 0},
    {'name': 'Silver Necklace', 'description': 'A mystical necklace', 'bonus_health': 5, 'bonus_attack': 2},
    {'name': 'Enchanted Ring', 'description': 'Increases damage by 3', 'bonus_health': 10, 'bonus_attack': 3},
    {'name': 'Iron Shield', 'description': 'Defensive shield', 'bonus_health': 20, 'bonus_attack': 0},
]


def ensure_player_exists():
    player = get_player()
    if not player:
        user = User.query.first()
        if not user:
            user = User(username='player', password='password')
            db.session.add(user)
            db.session.flush()

        player = Character(user_id=user.id, name='Hero')
        db.session.add(player)
        db.session.commit()


def seed_initial_data():
    if EnemyType.query.count() == 0:
        db.session.add_all([EnemyType(**seed) for seed in ENEMY_SEEDS])
        db.session.commit()

    if ItemType.query.count() == 0:
        db.session.add_all([ItemType(**seed) for seed in ITEM_TYPE_SEEDS])
        db.session.commit()


# Ensure player exists before each request
@app.before_request
def ensure_player():
    ensure_player_exists()

@app.cli.command('init-db')
def init_db():
    """Create DB tables and seed initial data (enemies + items)."""
    with app.app_context():
        db.create_all()
        seed_initial_data()
    print('Database initialized (tables created and seed data loaded)')


@app.cli.command('delete-db')
def delete_db():
    """Drop all tables and remove the SQLite DB file."""
    with app.app_context():
        try:
            # remove active session and drop tables
            db.session.remove()
            db.drop_all()
            # remove DB file if exists
            db_path = os.path.join(basedir, 'game.db')
            if os.path.exists(db_path):
                os.remove(db_path)
            print('Database dropped and file removed')
        except (OSError, SQLAlchemyError) as e:
            print('Failed to delete database:', e)


@app.cli.command('seed-full-loadout')
def seed_full_loadout():
    """Seed the player's inventory with a full loadout and equip primary items."""
    with app.app_context():
        ensure_player_exists()
        player = get_player()

        # Clear existing inventory and equipped items
        clear_player_inventory(player)
        clear_player_equipment(player)
        db.session.commit()

        # Helper to add inventory
        def add_item_by_name(name):
            itm = ItemType.query.filter_by(name=name).first()
            if itm:
                add_inventory_item(player, itm.id)

        # Add a sensible loadout (no Iron Sword)
        add_item_by_name('Steel Sword')
        add_item_by_name('Steel Sword')
        add_item_by_name('Leather Armor')
        add_item_by_name('Steel Armor')
        add_item_by_name('Iron Shield')
        add_item_by_name('Iron Helmet')
        add_item_by_name('Silver Necklace')
        add_item_by_name('Enchanted Ring')
        db.session.commit()

        print('Seeded full loadout for player')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
