"""Tests for the CLI interface."""

import pytest
from typer.testing import CliRunner
from slipdeck.cli import app

runner = CliRunner()


def test_app():
    """Test that the CLI runs without error."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_main_command():
    """Test the main command."""
    result = runner.invoke(app, ["World"])
    assert result.exit_code == 0
    assert "Hello, World" in result.stdout
