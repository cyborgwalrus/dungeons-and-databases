"""Tests for backend application bootstrap and CLI helpers."""

import importlib.util
from pathlib import Path
import sys

import pytest

from backend import app as app_module


def test_app_module_cli_commands_and_missing_secret_guard(app, monkeypatch):
    """Exercise the backend CLI commands and missing secret guard."""
    missing_secret_path = Path(__file__).resolve().parents[2] / 'backend' / 'app.py'
    monkeypatch.delenv('SECRET_KEY', raising=False)
    spec = importlib.util.spec_from_file_location('backend.app', missing_secret_path)
    assert spec is not None
    assert spec.loader is not None
    missing_secret_module = importlib.util.module_from_spec(spec)
    original_backend_app = sys.modules.get('backend.app')

    with pytest.raises(RuntimeError, match='SECRET_KEY must be set'):
        sys.modules['backend.app'] = missing_secret_module
        try:
            spec.loader.exec_module(missing_secret_module)
        finally:
            if original_backend_app is not None:
                sys.modules['backend.app'] = original_backend_app

    runner = app.test_cli_runner()
    init_result = runner.invoke(app_module.init_db)
    clear_result = runner.invoke(app_module.clear_db)

    assert init_result.exit_code == 0
    assert clear_result.exit_code == 0