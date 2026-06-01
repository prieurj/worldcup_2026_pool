# ⚽ FIFA World Cup 2026 Predictor & Office Pool

An interactive prediction system built with Python and Streamlit for office World Cup pools.

## Deployment (Streamlit Community Cloud)

1. Push this folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account and select the repo
4. Set the main file path to `app.py`
5. Deploy!

## Features

- **Group Stage Predictions**: Enter exact scores for all 72 group matches
- **Live Group Tables**: Real-time standings (FIFA rules: 3pts win, 1pt draw, GD, GF tiebreakers)
- **Automated Knockout Bracket**: R32 auto-populated from group predictions (top 2 + 8 best 3rd-place)
- **Score-based Knockout Picks**: Enter scores for each knockout match through the Final
- **Scoring System**: Exact score = 3pts, Correct outcome = 1pt, Wrong = 0pts
- **Leaderboard**: Live rankings of all participants
- **Admin Panel**: Enter official results, lock/unlock predictions, download user predictions

## Notes

- The SQLite database is ephemeral on Streamlit Cloud (resets on reboot)
- For persistent storage, consider migrating to a cloud database
