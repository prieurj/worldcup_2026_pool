"""Fetch completed FIFA World Cup 2026 match results from football-data.org
and write them to Supabase. Handles both group stage and knockout matches.
Only inserts results that don't already exist (never overwrites manual entries).
"""
import os
import sys
import requests
from supabase import create_client
from data import R32_OVERRIDES, R16_OVERRIDES

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

# Map API stage names to our round names
STAGE_TO_ROUND = {
    "LAST_32": "Round of 32",
    "LAST_16": "Round of 16",
    "QUARTER_FINALS": "Quarter-Finals",
    "SEMI_FINALS": "Semi-Finals",
    "FINAL": "Final",
}


def get_team_name(api_name):
    return TEAM_MAP.get(api_name, api_name)


def build_match_id(group, home, away):
    return f"{group}_{home}_vs_{away}"


ROUND_ORDER = ["Round of 32", "Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]


def get_round_matchups_standalone(round_name, r32_matchups, ko_official):
    """Build matchups for a given round (no streamlit dependency)."""
    if round_name == "Round of 32":
        return [(ta, tb) for (_, ta, tb) in r32_matchups]

    prev_round_idx = ROUND_ORDER.index(round_name) - 1
    prev_round = ROUND_ORDER[prev_round_idx]
    prev_matchups = get_round_matchups_standalone(prev_round, r32_matchups, ko_official)

    winners = []
    for i, (ta, tb) in enumerate(prev_matchups):
        result = ko_official.get((prev_round, i))
        if result:
            _, _, winner = result
            winners.append(winner)
        else:
            winners.append("TBD")

    matchups = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]

    if round_name == "Round of 16":
        for idx, (team_a, team_b) in R16_OVERRIDES.items():
            if idx < len(matchups):
                matchups[idx] = (team_a, team_b)

    return matchups


def find_knockout_match_index(round_name, home_team, away_team, r32_matchups, ko_official):
    """Find the match_index for a knockout game based on team names."""
    matchups = get_round_matchups_standalone(round_name, r32_matchups, ko_official)
    for i, (ta, tb) in enumerate(matchups):
        if (ta == home_team and tb == away_team) or (ta == away_team and tb == home_team):
            return i, ta, tb
    return None, None, None


def main():
    if not all([API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        print("ERROR: Missing environment variables (FOOTBALL_DATA_KEY, SUPABASE_URL, SUPABASE_KEY)")
        sys.exit(1)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get existing official results to avoid overwriting
    existing = sb.table("official_results").select("match_id").execute()
    existing_ids = {r["match_id"] for r in existing.data}

    # Get existing knockout results
    ko_existing_resp = sb.table("official_knockout_results").select("round, match_index").execute()
    ko_existing = {(r["round"], r["match_index"]) for r in ko_existing_resp.data}

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
    print(f"API returned {len(matches)} finished matches")

    # Debug: print all team names from API
    api_teams = set()
    for match in matches:
        api_teams.add(match["homeTeam"]["name"])
        api_teams.add(match["awayTeam"]["name"])
    if api_teams:
        print(f"Teams seen in API: {sorted(api_teams)}")

    inserted = 0
    skipped = 0
    ko_inserted = 0
    ko_skipped = 0

    # Separate group and knockout matches
    group_matches = []
    knockout_matches = []

    for match in matches:
        stage = match.get("stage", "")
        if stage == "GROUP_STAGE":
            group_matches.append(match)
        elif stage in STAGE_TO_ROUND:
            knockout_matches.append(match)

    # Process group stage
    for match in group_matches:
        group = match.get("group", "")
        if not group:
            continue
        group_letter = group.replace("GROUP_", "")

        home_team = get_team_name(match["homeTeam"]["name"])
        away_team = get_team_name(match["awayTeam"]["name"])
        home_score = match["score"]["fullTime"]["home"]
        away_score = match["score"]["fullTime"]["away"]

        if home_score is None or away_score is None:
            continue

        match_id = build_match_id(group_letter, home_team, away_team)

        if match_id in existing_ids:
            skipped += 1
            continue

        sb.table("official_results").upsert({
            "match_id": match_id,
            "home_score": home_score,
            "away_score": away_score
        }).execute()
        existing_ids.add(match_id)
        inserted += 1
        print(f"  ✓ [Group] {home_team} {home_score}-{away_score} {away_team}")

    # Process knockout matches
    # Build R32 matchups from overrides for index lookup
    from data import KNOCKOUT_R32_SLOTS
    r32_matchups = []
    for slot_label, source_a, source_b in KNOCKOUT_R32_SLOTS:
        if slot_label in R32_OVERRIDES:
            team_a, team_b = R32_OVERRIDES[slot_label]
        else:
            team_a, team_b = "TBD", "TBD"
        r32_matchups.append((slot_label, team_a, team_b))

    # Load current ko_official for round advancement
    ko_off_resp = sb.table("official_knockout_results").select("round, match_index, home_score, away_score, winner").execute()
    ko_official = {}
    for r in ko_off_resp.data:
        ko_official[(r["round"], r["match_index"])] = (r["home_score"], r["away_score"], r["winner"])

    for match in knockout_matches:
        stage = match.get("stage", "")
        round_name = STAGE_TO_ROUND[stage]

        home_team = get_team_name(match["homeTeam"]["name"])
        away_team = get_team_name(match["awayTeam"]["name"])

        # Build score after 120 min (regularTime + extraTime), excluding penalties
        reg = match["score"].get("regularTime", {})
        et = match["score"].get("extraTime", {})
        reg_home = reg.get("home")
        reg_away = reg.get("away")
        et_home = et.get("home", 0) or 0
        et_away = et.get("away", 0) or 0

        if reg_home is not None and reg_away is not None:
            # Regular time + extra time = score after 120 min
            home_score = reg_home + et_home
            away_score = reg_away + et_away
        else:
            # Fallback: if no regularTime breakdown, use fullTime minus penalties
            home_score = match["score"]["fullTime"]["home"]
            away_score = match["score"]["fullTime"]["away"]
            # If penalties exist, fullTime might include them — subtract
            pen = match["score"].get("penalties", {})
            if pen.get("home") is not None:
                # fullTime includes pens on this API, fall back to regulation + ET
                home_score = None
                away_score = None

        if home_score is None or away_score is None:
            continue

        # Determine winner (who actually advanced)
        if home_score != away_score:
            winner = home_team if home_score > away_score else away_team
        else:
            # Score tied after 120 min — decided by penalties
            pen = match["score"].get("penalties", {})
            pen_home = pen.get("home")
            pen_away = pen.get("away")
            if pen_home is not None and pen_away is not None:
                winner = home_team if pen_home > pen_away else away_team
            else:
                winner = home_team  # Shouldn't happen, fallback

        # Find match index
        match_index, bracket_a, bracket_b = find_knockout_match_index(
            round_name, home_team, away_team, r32_matchups, ko_official
        )

        if match_index is None:
            print(f"  ⚠ Could not find match index for {round_name}: {home_team} vs {away_team}")
            continue

        if (round_name, match_index) in ko_existing:
            ko_skipped += 1
            continue

        sb.table("official_knockout_results").upsert({
            "round": round_name,
            "match_index": match_index,
            "home_score": home_score,
            "away_score": away_score,
            "winner": winner
        }).execute()
        ko_existing.add((round_name, match_index))
        ko_official[(round_name, match_index)] = (home_score, away_score, winner)
        ko_inserted += 1
        print(f"  ✓ [KO {round_name}] {home_team} {home_score}-{away_score} {away_team} → {winner}")

    print(f"\nDone: Group: {inserted} inserted, {skipped} skipped | Knockout: {ko_inserted} inserted, {ko_skipped} skipped")


if __name__ == "__main__":
    main()
