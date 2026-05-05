"""Tests for envault.export — dotenv and JSON export/import helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import (
    export_dotenv,
    export_json,
    import_dotenv,
    import_json,
    read_file,
    write_file,
)

SAMPLE: dict[str, str] = {
    'DB_HOST': 'localhost',
    'DB_PASS': 'secret123',
    'GREETING': 'hello world',
    'QUOTED': 'has"quote',
}


# ---------------------------------------------------------------------------
# dotenv round-trip
# ---------------------------------------------------------------------------

def test_export_dotenv_plain_values():
    out = export_dotenv({'KEY': 'value'})
    assert 'KEY=value' in out


def test_export_dotenv_quotes_values_with_spaces():
    out = export_dotenv({'MSG': 'hello world'})
    assert 'MSG="hello world"' in out


def test_import_dotenv_round_trip():
    text = export_dotenv(SAMPLE)
    recovered = import_dotenv(text)
    assert recovered == SAMPLE


def test_import_dotenv_ignores_comments_and_blanks():
    text = '# comment\n\nFOO=bar\n'
    assert import_dotenv(text) == {'FOO': 'bar'}


def test_import_dotenv_ignores_lines_without_equals():
    text = 'NOEQUALS\nFOO=bar\n'
    assert import_dotenv(text) == {'FOO': 'bar'}


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------

def test_export_json_is_valid_json():
    text = export_json(SAMPLE)
    data = json.loads(text)
    assert data == SAMPLE


def test_import_json_round_trip():
    text = export_json(SAMPLE)
    assert import_json(text) == SAMPLE


def test_import_json_raises_on_non_object():
    with pytest.raises(ValueError, match='JSON object'):
        import_json('["a", "b"]')


def test_import_json_raises_on_non_string_values():
    with pytest.raises(ValueError, match='strings'):
        import_json(json.dumps({'KEY': 42}))


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def test_write_and_read_file(tmp_path: Path):
    target = tmp_path / 'sub' / 'out.env'
    write_file(target, 'FOO=bar\n')
    assert read_file(target) == 'FOO=bar\n'


def test_write_file_creates_parents(tmp_path: Path):
    deep = tmp_path / 'a' / 'b' / 'c' / 'secrets.env'
    write_file(deep, 'X=1\n')
    assert deep.exists()
