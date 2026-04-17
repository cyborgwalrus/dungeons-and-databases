from flask import Flask, request
from flask_cors import CORS
import os
from flask_login import LoginManager, current_user

from .db.init_db import seed_initial_data
from .db.models import Character, ItemType, User, db
from backend.game_utils import add_inventory_item, clear_player_equipment, clear_player_inventory, get_player
from sqlalchemy.exc import SQLAlchemyError
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp
from backend.routes.character_routes import character_bp
from backend.routes.dungeon_routes import dungeon_bp
from backend.routes.inventory_routes import inventory_bp

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
login_manager = LoginManager()

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "game.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) if user_id else None


@login_manager.unauthorized_handler
def unauthorized():
    return {'error': 'Unauthorized'}, 401

# Register blueprints under the /api prefix.
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(character_bp, url_prefix='/api')
app.register_blueprint(dungeon_bp, url_prefix='/api')
app.register_blueprint(inventory_bp, url_prefix='/api')


def ensure_player_exists():
    player = get_player()
    if not player:
        user = User.query.first()
        if not user:
            user = User()
            user.username = 'player'
            user.password = 'password'
            db.session.add(user)
            db.session.flush()

        player = Character(user_id=user.id, name='Hero')
        db.session.add(player)
        db.session.commit()
# Ensure player exists before each request
@app.before_request
def ensure_player():
    if current_user.is_authenticated:
        ensure_player_exists()


@app.before_request
def require_login():
    endpoint = request.endpoint or ''
    if endpoint in {'auth.signup', 'auth.signin'}:
        return None

    if not current_user.is_authenticated:
        return unauthorized()

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
