"""
FIFA World Cup 2026 tournament data.
48 teams, 12 groups of 4, top 2 + 8 best 3rd-place teams advance to Round of 32.
"""

GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Qatar", "Switzerland", "Bosnia and Herzegovina"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Ivory Coast", "Ecuador", "Curacao"],
    "F": ["Netherlands", "Japan", "Tunisia", "Sweden"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Saudi Arabia", "Uruguay", "Cape Verde"],
    "I": ["France", "Senegal", "Norway", "Iraq"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Colombia", "Uzbekistan", "DR Congo"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}


def generate_group_matches():
    """All 72 group stage matches in chronological order with date, time, and venue."""
    return [
        # Matchday 1
        {"group": "A", "home": "Mexico", "away": "South Africa", "match_id": "A_Mexico_vs_South Africa", "date": "Thu Jun 11", "time": "3:00 PM ET", "venue": "Estadio Azteca, Mexico City"},
        {"group": "A", "home": "South Korea", "away": "Czech Republic", "match_id": "A_South Korea_vs_Czech Republic", "date": "Thu Jun 11", "time": "10:00 PM ET", "venue": "Estadio Akron, Zapopan"},
        {"group": "B", "home": "Canada", "away": "Bosnia and Herzegovina", "match_id": "B_Canada_vs_Bosnia and Herzegovina", "date": "Fri Jun 12", "time": "3:00 PM ET", "venue": "BMO Field, Toronto"},
        {"group": "D", "home": "United States", "away": "Paraguay", "match_id": "D_United States_vs_Paraguay", "date": "Fri Jun 12", "time": "9:00 PM ET", "venue": "SoFi Stadium, Inglewood"},
        {"group": "B", "home": "Qatar", "away": "Switzerland", "match_id": "B_Qatar_vs_Switzerland", "date": "Sat Jun 13", "time": "3:00 PM ET", "venue": "Levi's Stadium, Santa Clara"},
        {"group": "C", "home": "Brazil", "away": "Morocco", "match_id": "C_Brazil_vs_Morocco", "date": "Sat Jun 13", "time": "6:00 PM ET", "venue": "MetLife Stadium, East Rutherford"},
        {"group": "C", "home": "Haiti", "away": "Scotland", "match_id": "C_Haiti_vs_Scotland", "date": "Sat Jun 13", "time": "9:00 PM ET", "venue": "Gillette Stadium, Foxborough"},
        {"group": "D", "home": "Australia", "away": "Turkey", "match_id": "D_Australia_vs_Turkey", "date": "Sat Jun 13", "time": "11:59 PM ET", "venue": "BC Place, Vancouver"},
        {"group": "E", "home": "Germany", "away": "Curacao", "match_id": "E_Germany_vs_Curacao", "date": "Sun Jun 14", "time": "1:00 PM ET", "venue": "NRG Stadium, Houston"},
        {"group": "F", "home": "Netherlands", "away": "Japan", "match_id": "F_Netherlands_vs_Japan", "date": "Sun Jun 14", "time": "4:00 PM ET", "venue": "AT&T Stadium, Arlington"},
        {"group": "E", "home": "Ivory Coast", "away": "Ecuador", "match_id": "E_Ivory Coast_vs_Ecuador", "date": "Sun Jun 14", "time": "7:00 PM ET", "venue": "Lincoln Financial Field, Philadelphia"},
        {"group": "F", "home": "Sweden", "away": "Tunisia", "match_id": "F_Sweden_vs_Tunisia", "date": "Sun Jun 14", "time": "10:00 PM ET", "venue": "Estadio BBVA, Guadalupe"},
        {"group": "H", "home": "Spain", "away": "Cape Verde", "match_id": "H_Spain_vs_Cape Verde", "date": "Mon Jun 15", "time": "12:00 PM ET", "venue": "Mercedes-Benz Stadium, Atlanta"},
        {"group": "G", "home": "Belgium", "away": "Egypt", "match_id": "G_Belgium_vs_Egypt", "date": "Mon Jun 15", "time": "3:00 PM ET", "venue": "Lumen Field, Seattle"},
        {"group": "H", "home": "Saudi Arabia", "away": "Uruguay", "match_id": "H_Saudi Arabia_vs_Uruguay", "date": "Mon Jun 15", "time": "6:00 PM ET", "venue": "Hard Rock Stadium, Miami Gardens"},
        {"group": "G", "home": "Iran", "away": "New Zealand", "match_id": "G_Iran_vs_New Zealand", "date": "Mon Jun 15", "time": "9:00 PM ET", "venue": "SoFi Stadium, Inglewood"},
        {"group": "I", "home": "France", "away": "Senegal", "match_id": "I_France_vs_Senegal", "date": "Tue Jun 16", "time": "3:00 PM ET", "venue": "MetLife Stadium, East Rutherford"},
        {"group": "I", "home": "Iraq", "away": "Norway", "match_id": "I_Iraq_vs_Norway", "date": "Tue Jun 16", "time": "6:00 PM ET", "venue": "Gillette Stadium, Foxborough"},
        {"group": "J", "home": "Argentina", "away": "Algeria", "match_id": "J_Argentina_vs_Algeria", "date": "Tue Jun 16", "time": "9:00 PM ET", "venue": "Arrowhead Stadium, Kansas City"},
        {"group": "J", "home": "Austria", "away": "Jordan", "match_id": "J_Austria_vs_Jordan", "date": "Tue Jun 16", "time": "11:59 PM ET", "venue": "Levi's Stadium, Santa Clara"},
        {"group": "K", "home": "Portugal", "away": "DR Congo", "match_id": "K_Portugal_vs_DR Congo", "date": "Wed Jun 17", "time": "1:00 PM ET", "venue": "NRG Stadium, Houston"},
        {"group": "L", "home": "England", "away": "Croatia", "match_id": "L_England_vs_Croatia", "date": "Wed Jun 17", "time": "4:00 PM ET", "venue": "AT&T Stadium, Arlington"},
        {"group": "L", "home": "Ghana", "away": "Panama", "match_id": "L_Ghana_vs_Panama", "date": "Wed Jun 17", "time": "7:00 PM ET", "venue": "BMO Field, Toronto"},
        {"group": "K", "home": "Uzbekistan", "away": "Colombia", "match_id": "K_Uzbekistan_vs_Colombia", "date": "Wed Jun 17", "time": "10:00 PM ET", "venue": "Estadio Azteca, Mexico City"},
        # Matchday 2
        {"group": "A", "home": "Czech Republic", "away": "South Africa", "match_id": "A_Czech Republic_vs_South Africa", "date": "Thu Jun 18", "time": "12:00 PM ET", "venue": "Mercedes-Benz Stadium, Atlanta"},
        {"group": "B", "home": "Switzerland", "away": "Bosnia and Herzegovina", "match_id": "B_Switzerland_vs_Bosnia and Herzegovina", "date": "Thu Jun 18", "time": "3:00 PM ET", "venue": "SoFi Stadium, Inglewood"},
        {"group": "B", "home": "Canada", "away": "Qatar", "match_id": "B_Canada_vs_Qatar", "date": "Thu Jun 18", "time": "6:00 PM ET", "venue": "BC Place, Vancouver"},
        {"group": "A", "home": "Mexico", "away": "South Korea", "match_id": "A_Mexico_vs_South Korea", "date": "Thu Jun 18", "time": "9:00 PM ET", "venue": "Estadio Akron, Zapopan"},
        {"group": "D", "home": "United States", "away": "Australia", "match_id": "D_United States_vs_Australia", "date": "Fri Jun 19", "time": "3:00 PM ET", "venue": "Lumen Field, Seattle"},
        {"group": "C", "home": "Scotland", "away": "Morocco", "match_id": "C_Scotland_vs_Morocco", "date": "Fri Jun 19", "time": "6:00 PM ET", "venue": "Gillette Stadium, Foxborough"},
        {"group": "C", "home": "Brazil", "away": "Haiti", "match_id": "C_Brazil_vs_Haiti", "date": "Fri Jun 19", "time": "9:00 PM ET", "venue": "Lincoln Financial Field, Philadelphia"},
        {"group": "D", "home": "Turkey", "away": "Paraguay", "match_id": "D_Turkey_vs_Paraguay", "date": "Fri Jun 19", "time": "11:59 PM ET", "venue": "Levi's Stadium, Santa Clara"},
        {"group": "F", "home": "Netherlands", "away": "Sweden", "match_id": "F_Netherlands_vs_Sweden", "date": "Sat Jun 20", "time": "1:00 PM ET", "venue": "NRG Stadium, Houston"},
        {"group": "E", "home": "Germany", "away": "Ivory Coast", "match_id": "E_Germany_vs_Ivory Coast", "date": "Sat Jun 20", "time": "4:00 PM ET", "venue": "BMO Field, Toronto"},
        {"group": "E", "home": "Ecuador", "away": "Curacao", "match_id": "E_Ecuador_vs_Curacao", "date": "Sat Jun 20", "time": "8:00 PM ET", "venue": "Arrowhead Stadium, Kansas City"},
        {"group": "F", "home": "Tunisia", "away": "Japan", "match_id": "F_Tunisia_vs_Japan", "date": "Sat Jun 20", "time": "11:59 PM ET", "venue": "Estadio BBVA, Guadalupe"},
        {"group": "H", "home": "Spain", "away": "Saudi Arabia", "match_id": "H_Spain_vs_Saudi Arabia", "date": "Sun Jun 21", "time": "12:00 PM ET", "venue": "Mercedes-Benz Stadium, Atlanta"},
        {"group": "G", "home": "Belgium", "away": "Iran", "match_id": "G_Belgium_vs_Iran", "date": "Sun Jun 21", "time": "3:00 PM ET", "venue": "SoFi Stadium, Inglewood"},
        {"group": "H", "home": "Uruguay", "away": "Cape Verde", "match_id": "H_Uruguay_vs_Cape Verde", "date": "Sun Jun 21", "time": "6:00 PM ET", "venue": "Hard Rock Stadium, Miami Gardens"},
        {"group": "G", "home": "New Zealand", "away": "Egypt", "match_id": "G_New Zealand_vs_Egypt", "date": "Sun Jun 21", "time": "9:00 PM ET", "venue": "BC Place, Vancouver"},
        {"group": "J", "home": "Argentina", "away": "Austria", "match_id": "J_Argentina_vs_Austria", "date": "Mon Jun 22", "time": "1:00 PM ET", "venue": "AT&T Stadium, Arlington"},
        {"group": "I", "home": "France", "away": "Iraq", "match_id": "I_France_vs_Iraq", "date": "Mon Jun 22", "time": "5:00 PM ET", "venue": "Lincoln Financial Field, Philadelphia"},
        {"group": "I", "home": "Norway", "away": "Senegal", "match_id": "I_Norway_vs_Senegal", "date": "Mon Jun 22", "time": "8:00 PM ET", "venue": "MetLife Stadium, East Rutherford"},
        {"group": "J", "home": "Jordan", "away": "Algeria", "match_id": "J_Jordan_vs_Algeria", "date": "Mon Jun 22", "time": "11:00 PM ET", "venue": "Levi's Stadium, Santa Clara"},
        {"group": "K", "home": "Portugal", "away": "Uzbekistan", "match_id": "K_Portugal_vs_Uzbekistan", "date": "Tue Jun 23", "time": "1:00 PM ET", "venue": "NRG Stadium, Houston"},
        {"group": "L", "home": "England", "away": "Ghana", "match_id": "L_England_vs_Ghana", "date": "Tue Jun 23", "time": "4:00 PM ET", "venue": "Gillette Stadium, Foxborough"},
        {"group": "L", "home": "Panama", "away": "Croatia", "match_id": "L_Panama_vs_Croatia", "date": "Tue Jun 23", "time": "7:00 PM ET", "venue": "BMO Field, Toronto"},
        {"group": "K", "home": "Colombia", "away": "DR Congo", "match_id": "K_Colombia_vs_DR Congo", "date": "Tue Jun 23", "time": "10:00 PM ET", "venue": "Estadio Akron, Zapopan"},
        # Matchday 3
        {"group": "B", "home": "Switzerland", "away": "Canada", "match_id": "B_Switzerland_vs_Canada", "date": "Wed Jun 24", "time": "3:00 PM ET", "venue": "BC Place, Vancouver"},
        {"group": "B", "home": "Bosnia and Herzegovina", "away": "Qatar", "match_id": "B_Bosnia and Herzegovina_vs_Qatar", "date": "Wed Jun 24", "time": "3:00 PM ET", "venue": "Lumen Field, Seattle"},
        {"group": "C", "home": "Scotland", "away": "Brazil", "match_id": "C_Scotland_vs_Brazil", "date": "Wed Jun 24", "time": "6:00 PM ET", "venue": "Hard Rock Stadium, Miami Gardens"},
        {"group": "C", "home": "Morocco", "away": "Haiti", "match_id": "C_Morocco_vs_Haiti", "date": "Wed Jun 24", "time": "6:00 PM ET", "venue": "Mercedes-Benz Stadium, Atlanta"},
        {"group": "A", "home": "Czech Republic", "away": "Mexico", "match_id": "A_Czech Republic_vs_Mexico", "date": "Wed Jun 24", "time": "9:00 PM ET", "venue": "Estadio Azteca, Mexico City"},
        {"group": "A", "home": "South Africa", "away": "South Korea", "match_id": "A_South Africa_vs_South Korea", "date": "Wed Jun 24", "time": "9:00 PM ET", "venue": "Estadio BBVA, Guadalupe"},
        {"group": "E", "home": "Curacao", "away": "Ivory Coast", "match_id": "E_Curacao_vs_Ivory Coast", "date": "Thu Jun 25", "time": "4:00 PM ET", "venue": "Lincoln Financial Field, Philadelphia"},
        {"group": "E", "home": "Ecuador", "away": "Germany", "match_id": "E_Ecuador_vs_Germany", "date": "Thu Jun 25", "time": "4:00 PM ET", "venue": "MetLife Stadium, East Rutherford"},
        {"group": "F", "home": "Japan", "away": "Sweden", "match_id": "F_Japan_vs_Sweden", "date": "Thu Jun 25", "time": "7:00 PM ET", "venue": "AT&T Stadium, Arlington"},
        {"group": "F", "home": "Tunisia", "away": "Netherlands", "match_id": "F_Tunisia_vs_Netherlands", "date": "Thu Jun 25", "time": "7:00 PM ET", "venue": "Arrowhead Stadium, Kansas City"},
        {"group": "D", "home": "Turkey", "away": "United States", "match_id": "D_Turkey_vs_United States", "date": "Thu Jun 25", "time": "10:00 PM ET", "venue": "SoFi Stadium, Inglewood"},
        {"group": "D", "home": "Paraguay", "away": "Australia", "match_id": "D_Paraguay_vs_Australia", "date": "Thu Jun 25", "time": "10:00 PM ET", "venue": "Levi's Stadium, Santa Clara"},
        {"group": "I", "home": "Norway", "away": "France", "match_id": "I_Norway_vs_France", "date": "Fri Jun 26", "time": "3:00 PM ET", "venue": "Gillette Stadium, Foxborough"},
        {"group": "I", "home": "Senegal", "away": "Iraq", "match_id": "I_Senegal_vs_Iraq", "date": "Fri Jun 26", "time": "3:00 PM ET", "venue": "BMO Field, Toronto"},
        {"group": "H", "home": "Cape Verde", "away": "Saudi Arabia", "match_id": "H_Cape Verde_vs_Saudi Arabia", "date": "Fri Jun 26", "time": "8:00 PM ET", "venue": "NRG Stadium, Houston"},
        {"group": "H", "home": "Uruguay", "away": "Spain", "match_id": "H_Uruguay_vs_Spain", "date": "Fri Jun 26", "time": "8:00 PM ET", "venue": "Estadio Akron, Zapopan"},
        {"group": "G", "home": "Egypt", "away": "Iran", "match_id": "G_Egypt_vs_Iran", "date": "Fri Jun 26", "time": "11:00 PM ET", "venue": "Lumen Field, Seattle"},
        {"group": "G", "home": "New Zealand", "away": "Belgium", "match_id": "G_New Zealand_vs_Belgium", "date": "Fri Jun 26", "time": "11:00 PM ET", "venue": "BC Place, Vancouver"},
        {"group": "L", "home": "Panama", "away": "England", "match_id": "L_Panama_vs_England", "date": "Sat Jun 27", "time": "5:00 PM ET", "venue": "MetLife Stadium, East Rutherford"},
        {"group": "L", "home": "Croatia", "away": "Ghana", "match_id": "L_Croatia_vs_Ghana", "date": "Sat Jun 27", "time": "5:00 PM ET", "venue": "Lincoln Financial Field, Philadelphia"},
        {"group": "K", "home": "Colombia", "away": "Portugal", "match_id": "K_Colombia_vs_Portugal", "date": "Sat Jun 27", "time": "7:30 PM ET", "venue": "Hard Rock Stadium, Miami Gardens"},
        {"group": "K", "home": "DR Congo", "away": "Uzbekistan", "match_id": "K_DR Congo_vs_Uzbekistan", "date": "Sat Jun 27", "time": "7:30 PM ET", "venue": "Mercedes-Benz Stadium, Atlanta"},
        {"group": "J", "home": "Algeria", "away": "Austria", "match_id": "J_Algeria_vs_Austria", "date": "Sat Jun 27", "time": "10:00 PM ET", "venue": "Arrowhead Stadium, Kansas City"},
        {"group": "J", "home": "Jordan", "away": "Argentina", "match_id": "J_Jordan_vs_Argentina", "date": "Sat Jun 27", "time": "10:00 PM ET", "venue": "AT&T Stadium, Arlington"},
    ]


GROUP_MATCHES = generate_group_matches()

# Knockout bracket structure for Round of 32 (16 matches)
# Format: (slot_label, source_description)
# 1st = group winner, 2nd = group runner-up, 3rd = best 3rd place from pool
# Round of 32 matchups based on official FIFA bracket
# Format: (slot_label, source_a, source_b)
# Match 73: 2A vs 2B
# Match 74: 1E vs 3ABCDF
# Match 75: 1F vs 2C
# Match 76: 1C vs 2F
# Match 77: 1I vs 3CDFGH
# Match 78: 2E vs 2I
# Match 79: 1A vs 3CEFHI
# Match 80: 1L vs 3EHIJK
# Match 81: 1D vs 3BEFIJ
# Match 82: 1G vs 3AEHIJ
# Match 83: 2K vs 2L
# Match 84: 1H vs 2J
# Match 85: 2B vs 3EFGIJ  (Note: this is 2nd place B, not a typo from source_a)
# Match 86: 1J vs 2H
# Match 87: 1K vs 3DEIJL
# Match 88: 2D vs 2G
KNOCKOUT_R32_SLOTS = [
    ("R32_73", "2A", "2B"),
    ("R32_74", "1E", "3A/B/C/D/F"),
    ("R32_75", "1F", "2C"),
    ("R32_76", "1C", "2F"),
    ("R32_77", "1I", "3C/D/F/G/H"),
    ("R32_78", "2E", "2I"),
    ("R32_79", "1A", "3C/E/F/H/I"),
    ("R32_80", "1L", "3E/H/I/J/K"),
    ("R32_81", "1D", "3B/E/F/I/J"),
    ("R32_82", "1G", "3A/E/H/I/J"),
    ("R32_83", "2K", "2L"),
    ("R32_84", "1H", "2J"),
    ("R32_85", "2B", "3E/F/G/I/J"),
    ("R32_86", "1J", "2H"),
    ("R32_87", "1K", "3D/E/I/J/L"),
    ("R32_88", "2D", "2G"),
]

KNOCKOUT_ROUNDS = ["Round of 32", "Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]
