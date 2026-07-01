"""File and settings persistence for the Incremental Query Filter."""
import json
import os


def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def write_lines(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(f"{it}\n")


def append_lines(path, items):
    with open(path, "a", encoding="utf-8") as f:
        for it in items:
            f.write(f"{it}\n")


def clear_file(path):
    open(path, "w", encoding="utf-8").close()


def load_settings(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
