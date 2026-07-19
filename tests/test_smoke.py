"""Smoke tests for public imports."""

from app import __version__
from app.cli import app


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"


def test_cli_app_has_registered_commands() -> None:
    command_names = {command.name for command in app.registered_commands}

    assert "scan-all" in command_names
    assert "demo-report" in command_names
    assert any(command.callback.__name__ == "scan" for command in app.registered_commands)
