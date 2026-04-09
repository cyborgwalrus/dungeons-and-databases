from flask import Flask
from flask_cors import CORS
import os

from database import db
from models import EnemyType, Item, Player, InventoryItem, EquippedItem
from game_utils import adjust_inventory_quantity, clear_player_equipment, clear_player_inventory, get_player
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
    EnemyType(name='Goblin', base_health=20, base_damage=5, description='A small, green creature with sharp teeth'),
    EnemyType(name='Skeleton', base_health=30, base_damage=7, description='Bones held together by dark magic'),
    EnemyType(name='Orc', base_health=40, base_damage=10, description='A brutal warrior with immense strength'),
    EnemyType(name='Dark Mage', base_health=25, base_damage=12, description='A sorcerer wielding forbidden magic'),
    EnemyType(name='Troll', base_health=60, base_damage=8, description='A massive creature with regenerating flesh'),
    EnemyType(name='Dragon Whelp', base_health=50, base_damage=15, description='A young dragon with fiery breath')
]

ITEM_SEEDS = [
    Item(name='Steel Sword', description='A strong steel sword', bonus_health=0, bonus_attack=10),
    Item(name='Leather Armor', description='Basic leather protection', bonus_health=15, bonus_attack=0),
    Item(name='Steel Armor', description='Strong steel protection', bonus_health=25, bonus_attack=0),
    Item(name='Iron Helmet', description='A sturdy helmet', bonus_health=8, bonus_attack=0),
    Item(name='Silver Necklace', description='A mystical necklace', bonus_health=5, bonus_attack=2),
    Item(name='Enchanted Ring', description='Increases damage by 3', bonus_health=10, bonus_attack=3),
    Item(name='Iron Shield', description='Defensive shield', bonus_health=20, bonus_attack=0),
]


def ensure_player_exists():
    player = get_player()
    if not player:
        player = Player(health=100, damage=10, level=1)
        db.session.add(player)
        db.session.commit()


def seed_initial_data():
    if EnemyType.query.count() == 0:
        db.session.add_all(ENEMY_SEEDS)
        db.session.commit()

    if Item.query.count() == 0:
        db.session.add_all(ITEM_SEEDS)
        db.session.commit()


def remove_legacy_items():
    obsolete = Item.query.filter_by(name='Iron Sword').all()
    if not obsolete:
        return

    for old_item in obsolete:
        InventoryItem.query.filter_by(item_id=old_item.id).delete()
        EquippedItem.query.filter_by(item_id=old_item.id).delete()
        db.session.delete(old_item)
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
        remove_legacy_items()
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
        except Exception as e:
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
        def add_item_by_name(name, qty=1):
            itm = Item.query.filter_by(name=name).first()
            if itm:
                adjust_inventory_quantity(player, itm.id, qty)

        # Add a sensible loadout (no Iron Sword)
        add_item_by_name('Steel Sword', 1)
        add_item_by_name('Steel Sword', 1)
        add_item_by_name('Leather Armor', 1)
        add_item_by_name('Steel Armor', 1)
        add_item_by_name('Iron Shield', 1)
        add_item_by_name('Iron Helmet', 1)
        add_item_by_name('Silver Necklace', 1)
        add_item_by_name('Enchanted Ring', 1)
        db.session.commit()

        # Equip primary items into slots 0..2 (weapon, armor, shield)
        def equip_direct(name, slot):
            itm = Item.query.filter_by(name=name).first()
            if not itm:
                return
            ei = EquippedItem(player_id=player.id, item_id=itm.id, slot=slot)
            db.session.add(ei)
            # decrement inventory for that item
            adjust_inventory_quantity(player, itm.id, -1)

        # Equip to new 2x3 layout slots:
        # 0: Helmet, 1: Armor, 2: Weapon, 3: Shield, 4: Ring, 5: Necklace
        equip_direct('Iron Helmet', 0)
        equip_direct('Leather Armor', 1)
        equip_direct('Steel Sword', 2)
        equip_direct('Iron Shield', 3)
        equip_direct('Enchanted Ring', 4)
        equip_direct('Silver Necklace', 5)
        db.session.commit()

        print('Seeded full loadout for player')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
