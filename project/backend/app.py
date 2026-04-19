import os

from flask import Flask, request
from flask import redirect
from flask import has_request_context
from flask_cors import CORS
from flask_login import LoginManager, current_user
from sqlalchemy.exc import SQLAlchemyError

from .utils import cache, init_cache
from backend.db.init_db import seed_initial_data
from backend.db.models import Character, User, db
from backend.utils.game_utils import get_player
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp
from backend.routes.character_routes import character_bp
from backend.routes.dungeon_routes import dungeon_bp
from backend.routes.inventory_routes import inventory_bp


app = Flask(__name__)
CORS(app, supports_credentials=True, origins=['http://localhost:8080', 'http://localhost:3000', 'http://127.0.0.1:8080', 'http://127.0.0.1:3000'])
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
login_manager = LoginManager()

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "game.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
login_manager.init_app(app)
init_cache(app)


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

# Handle OPTIONS preflight globally for all routes
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """Handle CORS preflight requests"""
    _ = path
    return '', 200


def ensure_player_exists():
    if not current_user.is_authenticated:
        if has_request_context():
            return redirect('/')
        return None

    return get_player()

# Ensure player exists before each request
@app.before_request
def ensure_player():
    # Skip OPTIONS preflight requests
    if request.method == 'OPTIONS':
        return None
    
    # Skip auth endpoints and character management endpoints (they don't need an active player)
    endpoint = request.endpoint or ''
    if endpoint in {'auth.signup', 'auth.signin', 'auth.signout', 'auth.me',
                    'character.list_characters', 'character.create_character',
                    'character.select_character', 'character.get_character',
                    'character.delete_character'}:
        return None
    
    # For all other endpoints, ensure player/character is selected
    result = ensure_player_exists()
    if result is not None and not isinstance(result, Character):
        return result


@app.before_request
def require_login():
    # Skip OPTIONS preflight requests
    if request.method == 'OPTIONS':
        return None
    
    endpoint = request.endpoint or ''
    # Only skip auth endpoints - character endpoints still require login
    if endpoint in {'auth.signup', 'auth.signin', 'auth.signout', 'auth.me'}:
        return None

    if not current_user.is_authenticated:
        return unauthorized()

@app.after_request
def after_request(response):
    """Ensure CORS headers are present on all responses"""
    origin = request.headers.get('Origin')
    allowed_origins = ['http://localhost:8080', 'http://localhost:3000', 'http://127.0.0.1:8080', 'http://127.0.0.1:3000']
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response

@app.cli.command('init-db')
def init_db():
    """Create DB tables and seed initial data (enemies + items)."""
    with app.app_context():
        db.create_all()
        seed_initial_data()
        cache.clear()
    print('Database initialized (tables created and seed data loaded)')


@app.cli.command('delete-db')
def delete_db():
    """Drop all tables and remove the SQLite DB file."""
    with app.app_context():
        try:
            # remove active session and drop tables
            db.session.remove()
            db.drop_all()
            cache.clear()
            # remove DB file if exists
            db_path = os.path.join(basedir, 'game.db')
            if os.path.exists(db_path):
                os.remove(db_path)
            print('Database dropped and file removed')
        except (OSError, SQLAlchemyError) as e:
            print('Failed to delete database:', e)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
