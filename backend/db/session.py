"""SQLModel engine and session bootstrap for the backend."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlmodel import SQLModel, Session


class _Database:
    """Minimal Flask-friendly SQLModel session wrapper."""

    def __init__(self) -> None:
        self.engine = None
        self.session: Any = None

    def init_app(self, app) -> None:
        """Bind the database engine and session to a Flask application."""
        database_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not database_uri:
            raise RuntimeError('SQLALCHEMY_DATABASE_URI must be set')

        if self.session is not None:
            self.session.remove()
        if self.engine is not None:
            self.engine.dispose()

        connect_args = {'check_same_thread': False} if database_uri.startswith('sqlite') else {}
        self.engine = create_engine(database_uri, connect_args=connect_args)
        self.session = scoped_session(
            sessionmaker(bind=self.engine, class_=Session, expire_on_commit=False)
        )

        @app.teardown_appcontext
        def _remove_session(_exception=None):
            if self.session is not None:
                self.session.remove()

    def create_all(self) -> None:
        """Create all SQLModel tables for the configured engine."""
        if self.engine is None:
            raise RuntimeError('Database engine is not initialized')
        SQLModel.metadata.create_all(self.engine)

    def drop_all(self) -> None:
        """Drop all SQLModel tables for the configured engine."""
        if self.engine is None:
            raise RuntimeError('Database engine is not initialized')
        SQLModel.metadata.drop_all(self.engine)


db = _Database()
