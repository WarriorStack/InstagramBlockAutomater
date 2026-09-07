from pathlib import Path
import json

from importer import extract_usernames


def test_txt_import(tmp_path: Path):
    p = tmp_path / "users.txt"
    p.write_text("@Alice\nalice\nBob\n", encoding="utf-8")
    assert extract_usernames(str(p)) == ["alice", "bob"]


def test_csv_import(tmp_path: Path):
    p = tmp_path / "users.csv"
    p.write_text("username\n@Alice\nBob\n", encoding="utf-8")
    assert extract_usernames(str(p)) == ["alice", "bob"]


def test_nested_json_import(tmp_path: Path):
    p = tmp_path / "users.json"
    data = {
        "followers": [
            {"string_list_data": [{"value": "Alice"}]},
            {"profile": {"username": "@Bob"}},
            {"href": "https://www.instagram.com/Charlie/"},
        ]
    }
    p.write_text(json.dumps(data), encoding="utf-8")
    assert extract_usernames(str(p)) == ["alice", "bob", "charlie"]
