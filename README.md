# ⚽ FIFA World Cup 2026 Predictor & Office Pool

An interactive prediction system built with Python and Streamlit for office World Cup pools.

## Features

- **Group Stage Predictions**: Enter exact scores for all 72 group matches
- **Live Group Tables**: Real-time standings calculated as you enter scores (FIFA rules: 3pts win, 1pt draw, GD, GF tiebreakers)
- **Automated Knockout Bracket**: R32 auto-populated from your group predictions (top 2 + 8 best 3rd-place teams)
- **Click-through Bracket**: Pick winners from R32 through to the Final
- **Scoring System**: Exact score = 3pts, Correct outcome = 1pt, Wrong = 0pts
- **Leaderboard**: Live rankings of all participants
- **Admin Panel**: Enter official results, lock/unlock predictions

## Installation

```bash
# Clone or navigate to the project directory
cd "FIFA World Cup 2026 Predictor"

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## Usage

### For Participants
1. Register an account
2. Navigate to **Group Predictions** — enter scores for each group
3. Navigate to **Knockout Bracket** — your R32 is auto-filled, pick winners through the Final
4. Save predictions before the admin locks them

### For Admin
1. Register with the "Admin" checkbox
2. Use **Admin Panel** to:
   - Enter official match results as games are played
   - Lock predictions before the tournament starts
   - View registered users

### Scoring Rules
| Result | Points |
|--------|--------|
| Exact score match (e.g., predicted 2-1, actual 2-1) | 3 |
| Correct outcome only (e.g., predicted 2-1, actual 1-0) | 1 |
| Wrong outcome | 0 |

## Project Structure

```
├── app.py              # Main Streamlit UI
├── logic.py            # Scoring engine, group table calculator, DB operations
├── data.py             # Tournament data (groups, matches, bracket structure)
├── requirements.txt    # Python dependencies
├── worldcup2026.db     # SQLite database (auto-created on first run)
└── README.md           # This file
```

## Notes

- The database (`worldcup2026.db`) is created automatically on first launch
- Group teams in `data.py` use placeholder names for unconfirmed slots — update as the draw is finalized
- The 2026 format: 48 teams, 12 groups of 4, top 2 + 8 best 3rd-place advance to Round of 32
