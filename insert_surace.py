"""One-time script to insert Surace's R32 knockout predictions."""
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

USERNAME = "Surace"
ROUND = "Round of 32"

# Match index maps to KNOCKOUT_R32_SLOTS order (0-indexed):
# 0: R32_73, 1: R32_74, 2: R32_75, 3: R32_76, 4: R32_77, 5: R32_78,
# 6: R32_79, 7: R32_80, 8: R32_81, 9: R32_82, 10: R32_83, 11: R32_84,
# 12: R32_85, 13: R32_86, 14: R32_87, 15: R32_88
# Format: (match_index, home_score, away_score, winner)
predictions = [
    (1, 3, 1, "Germany"),        # Game 74: Germany vs Paraguay
    (2, 2, 1, "Netherlands"),    # Game 75: Netherlands vs Morocco
    (3, 2, 1, "Brazil"),         # Game 76: Brazil vs Japan
    (4, 3, 0, "France"),         # Game 77: France vs Sweden
    (5, 1, 3, "Norway"),         # Game 78: Ivory Coast vs Norway
    (6, 1, 0, "Mexico"),         # Game 79: Mexico vs Ecuador
    (7, 2, 0, "England"),        # Game 80: England vs DR Congo
    (8, 2, 0, "United States"),  # Game 81: United States vs Bosnia and Herzegovina
    (9, 2, 1, "Belgium"),        # Game 82: Belgium vs Senegal
    (10, 2, 1, "Portugal"),      # Game 83: Portugal vs Croatia
    (11, 3, 0, "Spain"),         # Game 84: Spain vs Austria
    (12, 1, 0, "Switzerland"),   # Game 85: Switzerland vs Algeria
    (13, 2, 1, "Argentina"),     # Game 86: Argentina vs Cape Verde
    (14, 2, 0, "Colombia"),      # Game 87: Colombia vs Ghana
    (15, 1, 1, "Egypt"),         # Game 88: Australia vs Egypt (draw, Egypt advances)
]

for match_index, home_score, away_score, winner in predictions:
    sb.table("knockout_predictions").upsert({
        "username": USERNAME, "round": ROUND,
        "match_index": match_index, "field": "home", "value": str(home_score)
    }).execute()
    sb.table("knockout_predictions").upsert({
        "username": USERNAME, "round": ROUND,
        "match_index": match_index, "field": "away", "value": str(away_score)
    }).execute()
    sb.table("knockout_predictions").upsert({
        "username": USERNAME, "round": ROUND,
        "match_index": match_index, "field": "winner", "value": winner
    }).execute()
    print(f"  ✓ Match index {match_index}: {home_score}-{away_score}, winner: {winner}")

print(f"\nDone! Inserted {len(predictions)} predictions for {USERNAME}")
