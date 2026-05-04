import json
from pathlib import Path

DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "blue",
    "difficulty": "normal",
}

ALLOWED_COLORS = ("blue", "red", "green")
ALLOWED_DIFFICULTIES = ("easy", "normal", "hard")


def _load_json(path: Path, fallback):
    if not path.exists():
        return fallback

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return fallback


def _save_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def load_settings(base_dir: Path):
    settings_path = base_dir / "settings.json"
    raw = _load_json(settings_path, DEFAULT_SETTINGS.copy())

    settings = DEFAULT_SETTINGS.copy()
    settings["sound"] = bool(raw.get("sound", settings["sound"]))

    car_color = str(raw.get("car_color", settings["car_color"]))
    settings["car_color"] = car_color if car_color in ALLOWED_COLORS else settings["car_color"]

    difficulty = str(raw.get("difficulty", settings["difficulty"]))
    settings["difficulty"] = difficulty if difficulty in ALLOWED_DIFFICULTIES else settings["difficulty"]

    _save_json(settings_path, settings)
    return settings


def save_settings(base_dir: Path, settings):
    settings_path = base_dir / "settings.json"
    clean = DEFAULT_SETTINGS.copy()

    clean["sound"] = bool(settings.get("sound", clean["sound"]))
    color = str(settings.get("car_color", clean["car_color"]))
    clean["car_color"] = color if color in ALLOWED_COLORS else clean["car_color"]

    difficulty = str(settings.get("difficulty", clean["difficulty"]))
    clean["difficulty"] = difficulty if difficulty in ALLOWED_DIFFICULTIES else clean["difficulty"]

    _save_json(settings_path, clean)
    return clean


def load_leaderboard(base_dir: Path):
    board_path = base_dir / "leaderboard.json"
    raw = _load_json(board_path, [])

    if not isinstance(raw, list):
        raw = []

    cleaned = []
    for row in raw:
        if not isinstance(row, dict):
            continue

        name = str(row.get("name", "Player")).strip() or "Player"
        score = int(row.get("score", 0))
        coins = int(row.get("coins", 0))
        distance = int(row.get("distance", 0))

        cleaned.append(
            {
                "name": name[:16],
                "score": max(0, score),
                "coins": max(0, coins),
                "distance": max(0, distance),
            }
        )

    cleaned.sort(key=lambda item: (item["score"], item["distance"]), reverse=True)
    cleaned = cleaned[:10]
    _save_json(board_path, cleaned)
    return cleaned


def add_leaderboard_entry(base_dir: Path, entry):
    board = load_leaderboard(base_dir)
    board.append(
        {
            "name": str(entry.get("name", "Player")).strip()[:16] or "Player",
            "score": max(0, int(entry.get("score", 0))),
            "coins": max(0, int(entry.get("coins", 0))),
            "distance": max(0, int(entry.get("distance", 0))),
        }
    )
    board.sort(key=lambda item: (item["score"], item["distance"]), reverse=True)
    board = board[:10]

    _save_json(base_dir / "leaderboard.json", board)
    return board
