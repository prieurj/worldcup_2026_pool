"""
Logic engine: group table calculations, scoring system, and database operations.
Uses Supabase (PostgreSQL) for persistent cloud storage.
"""
import streamlit as st
from supabase import create_client, Client
from data import GROUPS, GROUP_MATCHES, KNOCKOUT_R32_SLOTS


def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def init_db():
    """Tables are created via Supabase dashboard SQL editor. This is a no-op."""
    pass


# --- Group Table Calculation ---

def calculate_group_table(predictions: dict, group_name: str) -> list:
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

    return sorted(table.values(), key=lambda x: (x["pts"], x["gd"], x["gf"]), reverse=True)


def get_knockout_teams_from_predictions(predictions: dict) -> list:
    group_positions = {}
    third_place_teams = []

    for group_name in GROUPS:
        table = calculate_group_table(predictions, group_name)
        group_positions[group_name] = table
        if len(table) >= 3:
            third_place_teams.append((group_name, table[2]))

    third_place_teams.sort(key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]), reverse=True)
    best_third = third_place_teams[:8]

    r32_matchups = []
    for slot_label, source_a, source_b in KNOCKOUT_R32_SLOTS:
        team_a = _resolve_source(source_a, group_positions, best_third)
        team_b = _resolve_source(source_b, group_positions, best_third)
        r32_matchups.append((slot_label, team_a, team_b))

    return r32_matchups


def _resolve_source(source: str, group_positions: dict, best_third: list) -> str:
    if source.startswith("3"):
        pool = source[1:].split("/")
        for group_name, team_data in list(best_third):
            if group_name in pool:
                best_third.remove((group_name, team_data))
                return team_data["team"]
        return "TBD"
    else:
        position = int(source[0]) - 1
        group = source[1]
        table = group_positions.get(group, [])
        if len(table) > position:
            return table[position]["team"]
        return "TBD"


# --- Scoring System ---

def calculate_match_points(predicted_home: int, predicted_away: int, actual_home: int, actual_away: int) -> int:
    if predicted_home == actual_home and predicted_away == actual_away:
        return 3
    if _outcome(predicted_home, predicted_away) == _outcome(actual_home, actual_away):
        return 1
    return 0


def _outcome(home: int, away: int) -> str:
    if home > away:
        return "H"
    elif home < away:
        return "A"
    return "D"


def calculate_user_total(username: str) -> dict:
    """Calculate total points split by group stage and knockout stage."""
    sb = get_supabase()

    # Group stage predictions
    preds_resp = sb.table("predictions").select("match_id, home_score, away_score").eq("username", username).execute()
    user_preds = {r["match_id"]: (r["home_score"], r["away_score"]) for r in preds_resp.data}

    # Knockout predictions
    ko_resp = sb.table("knockout_predictions").select("round, match_index, field, value").eq("username", username).execute()
    ko_preds = {}
    for r in ko_resp.data:
        ko_preds[(r["round"], r["match_index"], r["field"])] = r["value"]

    # Official group results
    official_resp = sb.table("official_results").select("match_id, home_score, away_score").execute()
    official = {r["match_id"]: (r["home_score"], r["away_score"]) for r in official_resp.data}

    # Official knockout results
    ko_official_resp = sb.table("official_knockout_results").select("round, match_index, home_score, away_score").execute()
    ko_official = {(r["round"], r["match_index"]): (r["home_score"], r["away_score"]) for r in ko_official_resp.data}

    # Score group stage
    group_total = group_exact = group_correct = group_wrong = 0
    group_details = []
    for mid, (oh, oa) in official.items():
        if mid in user_preds:
            ph, pa = user_preds[mid]
            pts = calculate_match_points(ph, pa, oh, oa)
            group_total += pts
            if pts == 3:
                group_exact += 1
            elif pts == 1:
                group_correct += 1
            else:
                group_wrong += 1
            group_details.append({"match_id": mid, "predicted": f"{ph}-{pa}", "actual": f"{oh}-{oa}", "points": pts})

    # Score knockout stage
    ko_total = ko_exact = ko_correct = ko_wrong = 0
    ko_details = []
    for (rnd, idx), (oh, oa) in ko_official.items():
        ph_key = (rnd, idx, "home")
        pa_key = (rnd, idx, "away")
        if ph_key in ko_preds and pa_key in ko_preds:
            try:
                ph = int(ko_preds[ph_key])
                pa = int(ko_preds[pa_key])
            except (ValueError, TypeError):
                continue
            pts = calculate_match_points(ph, pa, oh, oa)
            ko_total += pts
            if pts == 3:
                ko_exact += 1
            elif pts == 1:
                ko_correct += 1
            else:
                ko_wrong += 1
            ko_details.append({"match_id": f"{rnd} #{idx+1}", "predicted": f"{ph}-{pa}", "actual": f"{oh}-{oa}", "points": pts})

    return {
        "group_total": group_total, "group_exact": group_exact,
        "group_correct": group_correct, "group_wrong": group_wrong,
        "group_details": group_details,
        "ko_total": ko_total, "ko_exact": ko_exact,
        "ko_correct": ko_correct, "ko_wrong": ko_wrong,
        "ko_details": ko_details,
        "total": group_total + ko_total,
    }


def get_leaderboard() -> dict:
    """Get leaderboard split by group and knockout stages."""
    sb = get_supabase()
    users_resp = sb.table("users").select("username").eq("is_admin", False).execute()
    users = [r["username"] for r in users_resp.data]

    board = []
    for u in users:
        result = calculate_user_total(u)
        board.append({
            "username": u,
            "group_points": result["group_total"],
            "ko_points": result["ko_total"],
            "total": result["total"],
            "group_exact": result["group_exact"],
            "group_correct": result["group_correct"],
            "ko_exact": result["ko_exact"],
            "ko_correct": result["ko_correct"],
        })

    return board


# --- DB Helpers ---

def save_prediction(username: str, match_id: str, home_score: int, away_score: int):
    sb = get_supabase()
    sb.table("predictions").upsert({
        "username": username, "match_id": match_id,
        "home_score": home_score, "away_score": away_score
    }).execute()


def save_knockout_prediction(username: str, round_name: str, match_index: int, field: str, value):
    sb = get_supabase()
    sb.table("knockout_predictions").upsert({
        "username": username, "round": round_name,
        "match_index": match_index, "field": field, "value": str(value)
    }).execute()


def get_user_predictions(username: str) -> dict:
    sb = get_supabase()
    resp = sb.table("predictions").select("match_id, home_score, away_score").eq("username", username).execute()
    return {r["match_id"]: (r["home_score"], r["away_score"]) for r in resp.data}


def get_user_knockout_predictions(username: str) -> dict:
    sb = get_supabase()
    resp = sb.table("knockout_predictions").select("round, match_index, field, value").eq("username", username).execute()
    preds = {}
    for r in resp.data:
        val = r["value"]
        if r["field"] in ("home", "away"):
            try:
                val = int(val)
            except (ValueError, TypeError):
                val = 0
        preds[(r["round"], r["match_index"], r["field"])] = val
    return preds


def save_official_result(match_id: str, home_score: int, away_score: int):
    sb = get_supabase()
    sb.table("official_results").upsert({
        "match_id": match_id, "home_score": home_score, "away_score": away_score
    }).execute()


def get_official_results() -> dict:
    sb = get_supabase()
    resp = sb.table("official_results").select("match_id, home_score, away_score").execute()
    return {r["match_id"]: (r["home_score"], r["away_score"]) for r in resp.data}


def is_locked(phase: str = "group") -> bool:
    from datetime import datetime, timezone, timedelta
    eastern = timezone(timedelta(hours=-4))  # EDT
    now = datetime.now(eastern)
    # Auto-lock group stage at Jun 11, 2026 2:58 PM ET
    if phase == "group":
        if now >= datetime(2026, 6, 11, 14, 58, tzinfo=eastern):
            return True
    # Auto-lock knockout stage at Jun 28, 2026 2:58 PM ET
    if phase == "knockout":
        if now >= datetime(2026, 6, 28, 14, 58, tzinfo=eastern):
            return True
    sb = get_supabase()
    resp = sb.table("settings").select("value").eq("key", f"locked_{phase}").execute()
    if resp.data:
        return resp.data[0]["value"] == "1"
    return False


def set_locked(phase: str, locked: bool):
    sb = get_supabase()
    sb.table("settings").upsert({"key": f"locked_{phase}", "value": "1" if locked else "0"}).execute()


def get_db():
    """Compatibility helper for admin panel user queries."""
    return get_supabase()
