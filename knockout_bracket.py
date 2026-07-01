"""
Bracket-style knockout page with auto-advancing rounds.
- Bracket built from official results
- Auto-detects which round is active based on completed official results
- Users can only predict the current active round
- Bracket visualization shows all rounds with past/future state
"""
import streamlit as st
import pandas as pd
from data import R16_OVERRIDES, R16_PAIRINGS

# Knockout round schedule (first and last game times)
KNOCKOUT_SCHEDULE = {
    "Round of 32": {"first": "Sun Jun 28, 3:00 PM ET", "last": "Fri Jul 3, 9:30 PM ET", "matches": 16},
    "Round of 16": {"first": "Sat Jul 4, 1:00 PM ET", "last": "Tue Jul 7, 4:00 PM ET", "matches": 8},
    "Quarter-Finals": {"first": "Thu Jul 9, 4:00 PM ET", "last": "Sat Jul 11, 9:00 PM ET", "matches": 4},
    "Semi-Finals": {"first": "Tue Jul 14, 3:00 PM ET", "last": "Wed Jul 15, 3:00 PM ET", "matches": 2},
    "Final": {"first": "Sun Jul 19, 3:00 PM ET", "last": "Sun Jul 19, 3:00 PM ET", "matches": 1},
}

ROUND_ORDER = ["Round of 32", "Round of 16", "Quarter-Finals", "Semi-Finals", "Final"]


def get_active_round(ko_official_results):
    """Determine which round is currently active (first incomplete round)."""
    for round_name in ROUND_ORDER:
        expected = KNOCKOUT_SCHEDULE[round_name]["matches"]
        completed = sum(1 for (rnd, _) in ko_official_results if rnd == round_name)
        if completed < expected:
            return round_name
    return None  # All rounds complete


def get_round_matchups(round_name, r32_matchups, ko_official_results):
    """Build matchups for a given round based on official results from prior rounds."""
    if round_name == "Round of 32":
        return [(ta, tb) for (_, ta, tb) in r32_matchups]

    # Get winners from previous round
    prev_round_idx = ROUND_ORDER.index(round_name) - 1
    prev_round = ROUND_ORDER[prev_round_idx]
    prev_matchups = get_round_matchups(prev_round, r32_matchups, ko_official_results)

    winners = []
    for i, (ta, tb) in enumerate(prev_matchups):
        result = ko_official_results.get((prev_round, i))
        if result:
            h_score, a_score, winner = result
            winners.append(winner)
        else:
            winners.append("TBD")

    # Use custom pairings for R16, default adjacent pairing for other rounds
    if round_name == "Round of 16":
        matchups = []
        for idx in range(len(winners) // 2):
            a_idx, b_idx = R16_PAIRINGS.get(idx, (idx * 2, idx * 2 + 1))
            matchups.append((winners[a_idx], winners[b_idx]))
    else:
        matchups = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]

    # Apply R16 overrides if applicable
    if round_name == "Round of 16":
        for idx, (team_a, team_b) in R16_OVERRIDES.items():
            if idx < len(matchups):
                matchups[idx] = (team_a, team_b)

    return matchups


def knockout_bracket_page():
    st.title("🏆 Knockout Bracket")

    from logic import (
        get_knockout_teams_from_official, get_user_knockout_predictions,
        save_knockout_prediction, get_supabase
    )

    username = st.session_state.user["username"]
    knockout_preds = get_user_knockout_predictions(username)

    # Get R32 matchups from official group results
    r32_matchups = get_knockout_teams_from_official()

    # Get all official knockout results: {(round, match_index): (home_score, away_score, winner)}
    sb = get_supabase()
    try:
        ko_resp = sb.table("official_knockout_results").select("round, match_index, home_score, away_score, winner").execute()
        ko_official = {}
        for r in ko_resp.data:
            ko_official[(r["round"], r["match_index"])] = (r["home_score"], r["away_score"], r["winner"])
    except Exception:
        # Fallback if winner column doesn't exist yet
        ko_resp = sb.table("official_knockout_results").select("round, match_index, home_score, away_score").execute()
        ko_official = {}
        for r in ko_resp.data:
            # Infer winner from score (home wins ties for now)
            h, a = r["home_score"], r["away_score"]
            ko_official[(r["round"], r["match_index"])] = (h, a, None)

    # Determine active round
    active_round = get_active_round(ko_official)

    if active_round is None:
        st.success("🏆 Tournament complete!")
    else:
        st.info(f"📍 **Active round:** {active_round}")

    # --- Bracket Visualization ---
    st.markdown("---")
    st.subheader("📊 Bracket")

    cols = st.columns(len(ROUND_ORDER))
    for col_idx, round_name in enumerate(ROUND_ORDER):
        with cols[col_idx]:
            schedule = KNOCKOUT_SCHEDULE[round_name]
            st.markdown(f"**{round_name}**")
            if schedule["first"] == schedule["last"]:
                st.caption(f"📅 {schedule['first']}")
            else:
                st.caption(f"📅 {schedule['first']} → {schedule['last']}")

            matchups = get_round_matchups(round_name, r32_matchups, ko_official)

            for i, (ta, tb) in enumerate(matchups):
                result = ko_official.get((round_name, i))
                if result:
                    _, _, winner = result
                    if winner == ta:
                        st.markdown(f"✅ **{ta}**  \n~~{tb}~~")
                    else:
                        st.markdown(f"~~{ta}~~  \n✅ **{tb}**")
                elif "TBD" in [ta, tb]:
                    st.markdown(f"{ta}  \nvs {tb}")
                else:
                    # Check user prediction
                    w = knockout_preds.get((round_name, i, "winner"), None)
                    if w == ta:
                        st.markdown(f"🔮 **{ta}**  \nvs {tb}")
                    elif w == tb:
                        st.markdown(f"{ta}  \n🔮 **{tb}**")
                    else:
                        st.markdown(f"{ta}  \nvs {tb}")
                st.markdown("")

    # --- Prediction Entry for Active Round ---
    if active_round is None:
        return

    st.markdown("---")
    active_matchups = get_round_matchups(active_round, r32_matchups, ko_official)

    # Check if all matchups are known (no TBD)
    has_tbd = any("TBD" in [ta, tb] for ta, tb in active_matchups)
    if has_tbd:
        st.warning(f"⏳ Waiting for previous round results to complete the {active_round} bracket.")
        return

    # Check if this round's predictions are locked
    from logic import is_locked
    locked = is_locked("knockout")

    schedule = KNOCKOUT_SCHEDULE[active_round]
    st.subheader(f"📝 Predict: {active_round}")
    st.caption(f"📅 {schedule['first']} → {schedule['last']}")

    if locked:
        st.warning("🔒 Knockout predictions are locked.")
    editable = not locked

    for i, (team_a, team_b) in enumerate(active_matchups):
        match_key = f"{active_round}_{i}"
        existing_h = knockout_preds.get((active_round, i, "home"), None)
        existing_a = knockout_preds.get((active_round, i, "away"), None)

        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
        with c1:
            st.write(f"**{team_a}**")
        with c2:
            h_score = st.number_input(
                "H", min_value=0, max_value=20,
                value=existing_h if existing_h is not None else None,
                key=f"ko_h_{match_key}", label_visibility="collapsed",
                disabled=not editable, placeholder="-"
            )
        with c3:
            st.write("vs")
        with c4:
            a_score = st.number_input(
                "A", min_value=0, max_value=20,
                value=existing_a if existing_a is not None else None,
                key=f"ko_a_{match_key}", label_visibility="collapsed",
                disabled=not editable, placeholder="-"
            )
        with c5:
            st.write(f"**{team_b}**")

        if h_score is not None and a_score is not None:
            if h_score == a_score:
                existing_winner = knockout_preds.get((active_round, i, "winner"), None)
                options = [team_a, team_b]
                default_idx = options.index(existing_winner) if existing_winner in options else 0
                st.selectbox(
                    "Draw — who advances (ET/Pens)?",
                    options, index=default_idx,
                    key=f"ko_w_{match_key}", disabled=not editable
                )
            else:
                winner = team_a if h_score > a_score else team_b
                st.caption(f"✅ {winner} advances")

        st.divider()

    # Save button
    if editable:
        if st.button("💾 Save Predictions", type="primary"):
            saved = 0
            for i, (team_a, team_b) in enumerate(active_matchups):
                match_key = f"{active_round}_{i}"
                h = st.session_state.get(f"ko_h_{match_key}", None)
                a = st.session_state.get(f"ko_a_{match_key}", None)
                if h is None or a is None:
                    continue
                save_knockout_prediction(username, active_round, i, "home", h)
                save_knockout_prediction(username, active_round, i, "away", a)
                if h == a:
                    w = st.session_state.get(f"ko_w_{match_key}", team_a)
                elif h > a:
                    w = team_a
                else:
                    w = team_b
                save_knockout_prediction(username, active_round, i, "winner", w)
                saved += 1
            st.success(f"Saved {saved} predictions for {active_round}!")
            st.rerun()
