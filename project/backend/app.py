import os

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from .utils import cache, init_cache
from backend.db.init_db import seed_initial_data
from backend.db.models import db
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp
from backend.routes.character_routes import character_bp
from backend.routes.dungeon_routes import dungeon_bp
from backend.routes.inventory_routes import inventory_bp


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['AUTH_TOKEN_MAX_AGE_SECONDS'] = int(os.environ.get('AUTH_TOKEN_MAX_AGE_SECONDS', 60 * 60 * 24 * 30))

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "game.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
init_cache(app)

# Register blueprints under the /api prefix.
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(character_bp, url_prefix='/api')
app.register_blueprint(dungeon_bp, url_prefix='/api')
app.register_blueprint(inventory_bp, url_prefix='/api')

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
