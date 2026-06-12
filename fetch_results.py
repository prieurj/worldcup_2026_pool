"""
Fetch completed FIFA World Cup 2026 match results from football-data.org
and write them to Supabase. Only inserts results that don't already exist
(never overwrites manual entries).
"""
import os
import sys
import requests
from supabase import create_client

FOOTBALL_DATA_URL = "https://api.football-data.org/v4/competitions/WC/matches"
API_TOKEN = os.environ.get("FOOTBALL_DATA_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Team name mapping: football-data.org name -> our app's name
TEAM_MAP = {
    "Korea Republic": "South Korea",
    "Czechia": "Czech Republic",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Côte d'Ivoire": "Ivory Coast",
    "Curaçao": "Curacao",
    "Cabo Verde": "Cape Verde",
    "Congo DR": "DR Congo",
    "IR Iran": "Iran",
}


def get_team_name(api_name):
    """Map API team name to our internal name."""
    return TEAM_MAP.get(api_name, api_name)


def build_match_id(group, home, away):
    """Build match_id matching our data.py format: GROUP_HOME_vs_AWAY"""
    return f"{group}_{home}_vs_{away}"


def main():
    if not all([API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        print("ERROR: Missing environment variables (FOOTBALL_DATA_KEY, SUPABASE_URL, SUPABASE_KEY)")
        sys.exit(1)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get existing official results to avoid overwriting
    existing = sb.table("official_results").select("match_id").execute()
    existing_ids = {r["match_id"] for r in existing.data}

    # Fetch matches from football-data.org
    headers = {"X-Auth-Token": API_TOKEN}
    params = {"status": "FINISHED"}
    resp = requests.get(FOOTBALL_DATA_URL, headers=headers, params=params)

    if resp.status_code == 429:
        print("Rate limited. Will retry next run.")
        sys.exit(0)

    if resp.status_code != 200:
        print(f"API error: {resp.status_code} - {resp.text}")
        sys.exit(1)

    data = resp.json()
    matches = data.get("matches", [])

    inserted = 0
    skipped = 0

    for match in matches:
        # Only process group stage matches
        stage = match.get("stage", "")
        if stage != "GROUP_STAGE":
            continue

        group = match.get("group", "")
        if not group:
            continue
        # Convert "GROUP_A" -> "A"
        group_letter = group.replace("GROUP_", "")

        home_team = get_team_name(match["homeTeam"]["name"])
        away_team = get_team_name(match["awayTeam"]["name"])
        home_score = match["score"]["fullTime"]["home"]
        away_score = match["score"]["fullTime"]["away"]

        if home_score is None or away_score is None:
            continue

        match_id = build_match_id(group_letter, home_team, away_team)

        # Skip if already exists (don't overwrite manual entries)
        if match_id in existing_ids:
            skipped += 1
            continue

        # Insert into Supabase
        sb.table("official_results").upsert({
            "match_id": match_id,
            "home_score": home_score,
            "away_score": away_score
        }).execute()
        existing_ids.add(match_id)
        inserted += 1
        print(f"  ✓ {home_team} {home_score}-{away_score} {away_team}")

    print(f"\nDone: {inserted} new results inserted, {skipped} already existed")


if __name__ == "__main__":
    main()
