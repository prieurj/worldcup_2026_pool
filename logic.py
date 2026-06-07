"""
Logic engine: group table calculations, scoring system, and knockout bracket routing.
"""
import sqlite3
import json
import os
from data import GROUPS, GROUP_MATCHES, KNOCKOUT_R32_SLOTS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worldcup2026.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    # Migrate old knockout_predictions table if it exists with old schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knockout_predictions'")
    if c.fetchone():
        c.execute("PRAGMA table_info(knockout_predictions)")
        columns = [row["name"] for row in c.fetchall()]
        if "field" not in columns:
            c.execute("DROP TABLE knockout_predictions")
            conn.commit()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS predictions (
            user_id INTEGER,
            match_id TEXT,
            home_score INTEGER,
            away_score INTEGER,
            PRIMARY KEY (user_id, match_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS knockout_predictions (
            user_id INTEGER,
            round TEXT,
            match_index INTEGER,
            field TEXT,
            value TEXT,
            PRIMARY KEY (user_id, round, match_index, field),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS official_results (
            match_id TEXT PRIMARY KEY,
            home_score INTEGER,
            away_score INTEGER
        );
        CREATE TABLE IF NOT EXISTS official_knockout_results (
            round TEXT,
            match_index INTEGER,
            winner TEXT,
            PRIMARY KEY (round, match_index)
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS payment_status (
            user_id INTEGER PRIMARY KEY,
            paid INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)
    # Migrate legacy schema: if users table exists but lacks user_id column
    c.execute("PRAGMA table_info(users)")
    cols = [row["name"] for row in c.fetchall()]
    if "user_id" not in cols:
        c.executescript("""
            ALTER TABLE users RENAME TO users_old;
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0
            );
            INSERT INTO users (username, password_hash, is_admin)
                SELECT username, password_hash, is_admin FROM users_old;
            DROP TABLE users_old;

            CREATE TABLE predictions_new (
                user_id INTEGER,
                match_id TEXT,
                home_score INTEGER,
                away_score INTEGER,
                PRIMARY KEY (user_id, match_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            INSERT INTO predictions_new (user_id, match_id, home_score, away_score)
                SELECT u.user_id, p.match_id, p.home_score, p.away_score
                FROM predictions p JOIN users u ON p.username = u.username;
            DROP TABLE predictions;
            ALTER TABLE predictions_new RENAME TO predictions;

            CREATE TABLE knockout_predictions_new (
                user_id INTEGER,
                round TEXT,
                match_index INTEGER,
                field TEXT,
                value TEXT,
                PRIMARY KEY (user_id, round, match_index, field),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            INSERT INTO knockout_predictions_new (user_id, round, match_index, field, value)
                SELECT u.user_id, k.round, k.match_index, k.field, k.value
                FROM knockout_predictions k JOIN users u ON k.username = u.username;
            DROP TABLE knockout_predictions;
            ALTER TABLE knockout_predictions_new RENAME TO knockout_predictions;
        """)
    conn.commit()
    conn.close()


# --- Group Table Calculation ---

def calculate_group_table(predictions: dict, group_name: str) -> list:
    """
    Calculate group standings from a dict of predictions {match_id: (home_score, away_score)}.
    Returns sorted list of dicts: [{team, pts, gd, gf, ga, w, d, l, played}]
    """
    teams = GROUPS[group_name]
    table = {t: {"team": t, "pts": 0, "gd": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0, "played": 0} for t in teams}

    for match in GROUP_MATCHES:
        if match["group"] != group_name:
            continue
        mid = match["match_id"]
        if mid not in predictions:
            continue
        hs, aws = predictions[mid]
        if hs is None or aws is None:
            continue

        home, away = match["home"], match["away"]
        table[home]["gf"] += hs
        table[home]["ga"] += aws
        table[away]["gf"] += aws
        table[away]["ga"] += hs
        table[home]["gd"] += hs - aws
        table[away]["gd"] += aws - hs
        table[home]["played"] += 1
        table[away]["played"] += 1

        if hs > aws:
            table[home]["pts"] += 3
            table[home]["w"] += 1
            table[away]["l"] += 1
        elif hs < aws:
            table[away]["pts"] += 3
            table[away]["w"] += 1
            table[home]["l"] += 1
        else:
            table[home]["pts"] += 1
            table[away]["pts"] += 1
            table[home]["d"] += 1
            table[away]["d"] += 1

    sorted_table = sorted(
        table.values(),
        key=lambda x: (x["pts"], x["gd"], x["gf"]),
        reverse=True
    )
    return sorted_table


def get_knockout_teams_from_predictions(predictions: dict) -> dict:
    """
    From group predictions, determine 1st, 2nd, 3rd place for each group,
    then pick the 8 best 3rd-place teams.
    Returns dict mapping slot labels to team names for R32.
    """
    group_positions = {}  # {group: [1st, 2nd, 3rd, 4th]}
    third_place_teams = []

    for group_name in GROUPS:
        table = calculate_group_table(predictions, group_name)
        group_positions[group_name] = table
        if len(table) >= 3:
            third_place_teams.append((group_name, table[2]))

    # Sort 3rd place teams by pts, gd, gf
    third_place_teams.sort(key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]), reverse=True)
    best_third = third_place_teams[:8]

    # Build R32 matchups
    r32_matchups = []
    for slot_label, source_a, source_b in KNOCKOUT_R32_SLOTS:
        team_a = _resolve_source(source_a, group_positions, best_third)
        team_b = _resolve_source(source_b, group_positions, best_third)
        r32_matchups.append((slot_label, team_a, team_b))

    return r32_matchups


def _resolve_source(source: str, group_positions: dict, best_third: list) -> str:
    """Resolve a bracket source like '1A', '2B', '3A/B/C/D/F' to a team name."""
    if source.startswith("3"):
        # Best 3rd place from a pool of groups
        pool = source[1:].split("/")
        for group_name, team_data in list(best_third):
            if group_name in pool:
                best_third.remove((group_name, team_data))
                return team_data["team"]
        return "TBD"
    else:
        position = int(source[0]) - 1  # 0-indexed
        group = source[1]
        table = group_positions.get(group, [])
        if len(table) > position:
            return table[position]["team"]
        return "TBD"


# --- Scoring System ---

def calculate_match_points(predicted_home: int, predicted_away: int, actual_home: int, actual_away: int) -> int:
    """
    Exact Score = 3 pts
    Correct Outcome = 1 pt
    Wrong = 0 pts
    """
    if predicted_home == actual_home and predicted_away == actual_away:
        return 3
    # Check outcome
    pred_outcome = _outcome(predicted_home, predicted_away)
    actual_outcome = _outcome(actual_home, actual_away)
    if pred_outcome == actual_outcome:
        return 1
    return 0


def _outcome(home: int, away: int) -> str:
    if home > away:
        return "H"
    elif home < away:
        return "A"
    return "D"


def calculate_user_total(user_id: int) -> dict:
    """Calculate total points for a user based on official results."""
    conn = get_db()
    c = conn.cursor()

    # Get user predictions
    c.execute("SELECT match_id, home_score, away_score FROM predictions WHERE user_id = ?", (user_id,))
    user_preds = {row["match_id"]: (row["home_score"], row["away_score"]) for row in c.fetchall()}

    # Get official results
    c.execute("SELECT match_id, home_score, away_score FROM official_results")
    official = {row["match_id"]: (row["home_score"], row["away_score"]) for row in c.fetchall()}

    total = 0
    exact = 0
    correct_outcome = 0
    wrong = 0
    details = []

    for mid, (oh, oa) in official.items():
        if mid in user_preds:
            ph, pa = user_preds[mid]
            pts = calculate_match_points(ph, pa, oh, oa)
            total += pts
            if pts == 3:
                exact += 1
            elif pts == 1:
                correct_outcome += 1
            else:
                wrong += 1
            details.append({"match_id": mid, "predicted": f"{ph}-{pa}", "actual": f"{oh}-{oa}", "points": pts})

    conn.close()
    return {"total": total, "exact": exact, "correct_outcome": correct_outcome, "wrong": wrong, "details": details}


def get_leaderboard() -> list:
    """Get sorted leaderboard of all users."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, username FROM users WHERE is_admin = 0")
    users = [(row["user_id"], row["username"]) for row in c.fetchall()]
    conn.close()

    board = []
    for uid, uname in users:
        result = calculate_user_total(uid)
        board.append({"username": uname, "points": result["total"], "exact": result["exact"], "correct": result["correct_outcome"]})

    board.sort(key=lambda x: x["points"], reverse=True)
    return board


# --- DB Helpers ---

def save_prediction(user_id: int, match_id: str, home_score: int, away_score: int):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO predictions (user_id, match_id, home_score, away_score) VALUES (?, ?, ?, ?)",
        (user_id, match_id, home_score, away_score)
    )
    conn.commit()
    conn.close()


def save_knockout_prediction(user_id: int, round_name: str, match_index: int, field: str, value):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO knockout_predictions (user_id, round, match_index, field, value) VALUES (?, ?, ?, ?, ?)",
        (user_id, round_name, match_index, field, str(value))
    )
    conn.commit()
    conn.close()


def get_user_predictions(user_id: int) -> dict:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT match_id, home_score, away_score FROM predictions WHERE user_id = ?", (user_id,))
    preds = {row["match_id"]: (row["home_score"], row["away_score"]) for row in c.fetchall()}
    conn.close()
    return preds


def get_user_knockout_predictions(user_id: int) -> dict:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT round, match_index, field, value FROM knockout_predictions WHERE user_id = ?", (user_id,))
    preds = {}
    for row in c.fetchall():
        key = (row["round"], row["match_index"], row["field"])
        val = row["value"]
        if row["field"] in ("home", "away"):
            try:
                val = int(val)
            except (ValueError, TypeError):
                val = 0
        preds[key] = val
    conn.close()
    return preds


def update_username(user_id: int, new_username: str) -> bool:
    """Update a user's username. Returns False if the name is taken."""
    conn = get_db()
    try:
        conn.execute("UPDATE users SET username = ? WHERE user_id = ?", (new_username, user_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def save_official_result(match_id: str, home_score: int, away_score: int):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO official_results (match_id, home_score, away_score) VALUES (?, ?, ?)",
        (match_id, home_score, away_score)
    )
    conn.commit()
    conn.close()


def get_official_results() -> dict:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT match_id, home_score, away_score FROM official_results")
    results = {row["match_id"]: (row["home_score"], row["away_score"]) for row in c.fetchall()}
    conn.close()
    return results


def is_locked() -> bool:
    """Check if predictions are locked."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'locked'")
    row = c.fetchone()
    conn.close()
    return row is not None and row["value"] == "1"


def set_locked(locked: bool):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('locked', ?)", ("1" if locked else "0",))
    conn.commit()
    conn.close()


def get_payment_status() -> dict:
    """Return {user_id: bool} for paid status."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, paid FROM payment_status")
    result = {row["user_id"]: bool(row["paid"]) for row in c.fetchall()}
    conn.close()
    return result


def set_payment_status(user_id: int, paid: bool):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO payment_status (user_id, paid) VALUES (?, ?)", (user_id, 1 if paid else 0))
    conn.commit()
    conn.close()
