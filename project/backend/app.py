import os
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from backend.db.init_db import seed_initial_data
from backend.db.models import db
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp
from backend.routes.character_routes import character_bp
from backend.routes.item_routes import item_bp
from backend.routes.dungeon_routes import dungeon_bp
from .utils import cache, init_cache


app = Flask(__name__)
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError('SECRET_KEY must be set')
app.config['SECRET_KEY'] = secret_key
app.config['AUTH_TOKEN_MAX_AGE_SECONDS'] = int(os.environ.get('AUTH_TOKEN_MAX_AGE_SECONDS', 60 * 60 * 24 * 30))
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes', 'on'}

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
app.register_blueprint(item_bp, url_prefix='/api')
app.register_blueprint(dungeon_bp, url_prefix='/api')

@app.cli.command('init-db')
def init_db():
    # Create DB tables, seed reference data, and clear cached lookups.
    with app.app_context():
        db.create_all()
        seed_initial_data()
        cache.clear()
    print('Database initialized (tables created and seed data loaded)')


@app.cli.command('delete-db')
def delete_db():
    # Drop all tables, clear cache state, and remove the SQLite database file.
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
    app.run(debug=app.config['DEBUG'], port=5000)
