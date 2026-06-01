"""
Fetch completed World Cup 2026 match results from API-Football
and write them to Supabase — only if a result doesn't already exist.
"""
import os
import requests
from supabase import create_client

# --- Config ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
API_FOOTBALL_KEY = os.environ["API_FOOTBALL_KEY"]

# API-Football league ID for World Cup 2026 (may need updating once tournament is listed)
# Check https://www.api-football.com/documentation-v3 for the correct ID
WORLD_CUP_LEAGUE_ID = 1  # FIFA World Cup
WORLD_CUP_SEASON = 2026

# Team name mapping: API-Football names -> our match_id names
# Update this if API returns different names than what we use in data.py
TEAM_NAME_MAP = {
    "USA": "United States",
    "Korea Republic": "South Korea",
    "Czechia": "Czech Republic",
    "Bosnia And Herzegovina": "Bosnia and Herzegovina",
    "Cote D'Ivoire": "Ivory Coast",
    "Curacao": "Curacao",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "IR Iran": "Iran",
}


def normalize_team_name(name: str) -> str:
    """Convert API team name to our internal name."""
    return TEAM_NAME_MAP.get(name, name)


def build_match_id(group: str, home: str, away: str) -> str:
    """Build match_id in the same format as data.py."""
    return f"{group}_{home}_vs_{away}"


def get_existing_results(sb) -> set:
    """Get all match_ids that already have official results."""
    resp = sb.table("official_results").select("match_id").execute()
    return {r["match_id"] for r in resp.data}


def fetch_completed_matches() -> list:
    """Fetch completed World Cup matches from API-Football (direct)."""
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    params = {
        "league": WORLD_CUP_LEAGUE_ID,
        "season": WORLD_CUP_SEASON,
        "status": "FT"  # Full Time only
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    matches = []
    for fixture in data.get("response", []):
        league_round = fixture.get("league", {}).get("round", "")

        # Only process group stage matches for now
        if "Group" not in league_round:
            continue

        # Extract group letter (e.g., "Group A" -> "A")
        group = league_round.replace("Group ", "").strip()
        if len(group) != 1:
            continue

        home_team = normalize_team_name(fixture["teams"]["home"]["name"])
        away_team = normalize_team_name(fixture["teams"]["away"]["name"])
        home_score = fixture["goals"]["home"]
        away_score = fixture["goals"]["away"]

        if home_score is None or away_score is None:
            continue

        match_id = build_match_id(group, home_team, away_team)
        matches.append({
            "match_id": match_id,
            "home_score": home_score,
            "away_score": away_score,
            "home_team": home_team,
            "away_team": away_team,
        })

    return matches


def main():
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    existing = get_existing_results(sb)

    print(f"Found {len(existing)} existing results in database.")

    completed = fetch_completed_matches()
    print(f"Found {len(completed)} completed matches from API.")

    new_count = 0
    for match in completed:
        mid = match["match_id"]
        if mid in existing:
            print(f"  SKIP (already exists): {mid}")
            continue

        # Also try reversed match_id in case home/away are swapped in our data
        # Our data.py defines specific home/away per match, API might differ
        reversed_mid = build_match_id(
            mid.split("_")[0],  # group letter
            match["away_team"],
            match["home_team"]
        )
        if reversed_mid in existing:
            print(f"  SKIP (reversed exists): {reversed_mid}")
            continue

        # Write new result
        sb.table("official_results").upsert({
            "match_id": mid,
            "home_score": match["home_score"],
            "away_score": match["away_score"]
        }).execute()
        print(f"  NEW: {mid} -> {match['home_score']}-{match['away_score']}")
        new_count += 1

    print(f"\nDone. Added {new_count} new results.")


if __name__ == "__main__":
    main()
