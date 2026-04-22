"""Pytest fixtures for the backend test suite."""
# pylint: disable=wrong-import-position
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from werkzeug.security import generate_password_hash

os.environ.setdefault('SECRET_KEY', 'test-secret-key')

from backend.app import app as flask_app
from backend.db.models import Character, Item, User, db
from backend.db.reference_data import load_reference_data
from backend.resources.encounters import create_new_encounter
from backend.utils.api_response_cache import cache
from backend.utils.game_utils import add_inventory_item, issue_auth_token, seed_character_loadout


@pytest.fixture(scope='session')
def app(tmp_path_factory):
    """Create the shared Flask app bound to a temporary test database."""
    database_path = tmp_path_factory.mktemp('db') / 'test-game.db'
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{database_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        load_reference_data()
        cache.clear()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        cache.clear()
        db.drop_all()


@pytest.fixture(autouse=True)
def reset_database(request):
    """Reset the database before and after each test."""
    with request.getfixturevalue('app').app_context():
        db.session.remove()
        cache.clear()
        db.drop_all()
        db.create_all()
        load_reference_data()
        yield
        db.session.remove()
        cache.clear()


@pytest.fixture
def client(request):
    """Return a Flask test client bound to the shared app."""
    return request.getfixturevalue('app').test_client()


@pytest.fixture
def entities(request):
    """Factory helpers for creating backend test data."""
    request.getfixturevalue('app')

    def create_user(username: str = 'player', password: str = 'secret') -> User:
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return user

    def create_character(
        user: User,
        *,
        name: str = 'Hero',
        seed_loadout: bool = False,
        **stats: int,
    ) -> Character:
        level = stats.get('level', 1)
        health = stats.get('health', 100)
        damage = stats.get('damage', 10)
        character = Character(
            user_id=user.id,
            name=name,
            level=level,
            health=health,
            damage=damage,
        )
        db.session.add(character)
        db.session.flush()
        if seed_loadout:
            seed_character_loadout(character)
        db.session.commit()
        return character

    def create_inventory_item(
        character: Character,
        item_type_id: str = 'steel_sword',
        *,
        level: int = 1,
        is_loot: bool = False,
    ) -> Item:
        item = add_inventory_item(character, item_type_id, level=level, is_loot=is_loot)
        if item is None:
            raise AssertionError(f'Failed to create inventory item {item_type_id!r}')
        db.session.commit()
        return item

    def auth_headers(token: str) -> dict[str, str]:
        """Build an Authorization header for the supplied token."""
        return {'Authorization': f'Bearer {token}'}

    def token_for(user: User, character: Character | None = None) -> str:
        """Issue a token for a user and optional active character."""
        return issue_auth_token(user.id, None if character is None else character.id)

    def create_encounter(character: Character, *, enemy_level: int = 1):
        """Create a matching encounter and combat record for a character."""
        encounter, combat = create_new_encounter(character, enemy_level=enemy_level)
        if encounter is None or combat is None:
            raise AssertionError('Failed to create encounter')
        return encounter, combat

    return SimpleNamespace(
        create_user=create_user,
        create_character=create_character,
        create_inventory_item=create_inventory_item,
        auth_headers=auth_headers,
        token_for=token_for,
        create_encounter=create_encounter,
    )
