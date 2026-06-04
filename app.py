"""
FIFA World Cup 2026 Predictor & Office Pool System
Main Streamlit application (Supabase cloud version).
"""
import streamlit as st
import pandas as pd
import hashlib
from io import BytesIO
from data import GROUPS, GROUP_MATCHES, KNOCKOUT_R32_SLOTS, KNOCKOUT_ROUNDS
from logic import (
    init_db, get_supabase, calculate_group_table, get_knockout_teams_from_predictions,
    get_knockout_teams_from_official, save_prediction, get_user_predictions,
    save_knockout_prediction, get_user_knockout_predictions, calculate_user_total,
    get_leaderboard, save_official_result, get_official_results, is_locked, set_locked,
    get_knockout_mode, set_knockout_mode, is_knockout_open
)

st.set_page_config(page_title="World Cup 2026 Predictor", page_icon="⚽", layout="wide")
init_db()


# --- Auth Helpers ---

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(password: str, hashed: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == hashed


def register_user(username: str, password: str, is_admin: bool = False) -> bool:
    sb = get_supabase()
    # Check if user exists
    existing = sb.table("users").select("username").eq("username", username).execute()
    if existing.data:
        return False
    sb.table("users").insert({
        "username": username,
        "password_hash": hash_password(password),
        "is_admin": is_admin
    }).execute()
    return True


def authenticate(username: str, password: str):
    sb = get_supabase()
    try:
        resp = sb.table("users").select("password_hash, is_admin").eq("username", username).execute()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None
    if resp.data:
        row = resp.data[0]
        if check_password(password, row["password_hash"]):
            return {"username": username, "is_admin": bool(row["is_admin"])}
    return None


# --- Session State ---

if "user" not in st.session_state:
    st.session_state.user = None


# --- Sidebar Navigation ---

def sidebar():
    st.sidebar.title("⚽ WC 2026 Predictor")
    if st.session_state.user:
        st.sidebar.write(f"Logged in as: **{st.session_state.user['username']}**")
        pages = ["Group Predictions", "Knockout Bracket", "Leaderboard"]
        if st.session_state.user["is_admin"]:
            pages.append("Admin Panel")
        page = st.sidebar.radio("Navigate", pages)
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun()
        return page
    return None


# --- Login / Register Page ---

def login_page():
    st.title("⚽ FIFA World Cup 2026 Predictor")
    st.subheader("Office Pool System")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if not username or not password:
                st.error("Please enter username and password.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with tab2:
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")
        is_admin = st.checkbox("Register as Admin", key="reg_admin")
        if st.button("Register"):
            if not new_user or not new_pass:
                st.error("Username and password required.")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match.")
            else:
                if register_user(new_user, new_pass, is_admin):
                    st.success("Registered! Please login.")
                else:
                    st.error("Username already taken.")


# --- Group Predictions Page ---

def group_predictions_page():
    st.title("📋 Group Stage Predictions")

    locked = is_locked("group")
    if locked:
        st.warning("🔒 Group stage predictions are locked. You can view but not edit.")

    username = st.session_state.user["username"]
    existing_preds = get_user_predictions(username)

    group_names = list(GROUPS.keys())
    selected_group = st.selectbox("Select Group", group_names, format_func=lambda x: f"Group {x}")

    group_matches = [m for m in GROUP_MATCHES if m["group"] == selected_group]

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader(f"Group {selected_group} Matches")
        current_preds = dict(existing_preds)

        for match in group_matches:
            mid = match["match_id"]
            existing_h = existing_preds.get(mid, (None, None))[0]
            existing_a = existing_preds.get(mid, (None, None))[1]

            st.caption(f"📅 {match['date']} · ⏰ {match['time']} · 🏟️ {match['venue']}")
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
            with c1:
                st.write(f"**{match['home']}**")
            with c2:
                h_score = st.number_input(
                    "H", min_value=0, max_value=20, value=existing_h if existing_h is not None else 0,
                    key=f"h_{mid}", label_visibility="collapsed", disabled=locked
                )
            with c3:
                st.write("vs")
            with c4:
                a_score = st.number_input(
                    "A", min_value=0, max_value=20, value=existing_a if existing_a is not None else 0,
                    key=f"a_{mid}", label_visibility="collapsed", disabled=locked
                )
            with c5:
                st.write(f"**{match['away']}**")

            current_preds[mid] = (h_score, a_score)
            st.divider()

        if not locked:
            if st.button(f"💾 Save Group {selected_group} Predictions", type="primary"):
                for match in group_matches:
                    mid = match["match_id"]
                    h, a = current_preds[mid]
                    save_prediction(username, mid, h, a)
                st.success(f"Group {selected_group} predictions saved!")
                st.rerun()

    with col2:
        st.subheader(f"Group {selected_group} Table")
        table = calculate_group_table(current_preds, selected_group)
        df = pd.DataFrame(table)
        df.index = range(1, len(df) + 1)
        df = df[["team", "played", "w", "d", "l", "gf", "ga", "gd", "pts"]]
        df.columns = ["Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]
        st.dataframe(df, use_container_width=True, hide_index=False)
        st.caption("Top 2 qualify automatically. 3rd place may qualify as best 3rd.")


# --- Knockout Bracket Page ---

def knockout_bracket_page():
    st.title("🏆 Knockout Bracket")

    ko_mode = get_knockout_mode()
    username = st.session_state.user["username"]
    user_preds = get_user_predictions(username)
    knockout_preds = get_user_knockout_predictions(username)

    # Determine if knockout is accessible
    if ko_mode == "reset":
        # Option 2: Knockout Reset
        ko_open = is_knockout_open()
        locked = is_locked("knockout")

        if not ko_open and not locked:
            st.info("📅 Knockout predictions will open on **June 27 at 11:30 PM ET** after all group matches are complete. The bracket will be built from official results.")
            st.warning("🔒 Knockout predictions are not yet available.")
            return

        if locked:
            st.warning("🔒 Knockout predictions are locked.")

        # Build bracket from official results
        r32_matchups = get_knockout_teams_from_official()
        editable = ko_open and not locked
        st.caption("Bracket is built from official group stage results. Enter your predicted scores for each knockout match.")
    else:
        # Option 1: Early Knockout
        locked = is_locked("knockout")
        if locked:
            st.warning("🔒 Knockout predictions are locked.")

        r32_matchups = get_knockout_teams_from_predictions(user_preds)
        editable = not locked
        st.caption("Teams are auto-populated from your group predictions. Enter scores for each knockout match (higher score advances; if tied, pick a winner below).")

    def render_knockout_round(round_name, matchups):
        st.subheader(round_name)
        winners = []
        for i, (team_a, team_b) in enumerate(matchups):
            match_key = f"{round_name}_{i}"
            existing_h = knockout_preds.get((round_name, i, "home"), None)
            existing_a = knockout_preds.get((round_name, i, "away"), None)

            st.markdown(f"**{team_a}** vs **{team_b}**")
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
            with c1:
                st.write(f"**{team_a}**")
            with c2:
                h_score = st.number_input(
                    "H", min_value=0, max_value=20,
                    value=existing_h if existing_h is not None else 0,
                    key=f"ko_h_{match_key}", label_visibility="collapsed",
                    disabled=not editable or "TBD" in [team_a, team_b]
                )
            with c3:
                st.write("vs")
            with c4:
                a_score = st.number_input(
                    "A", min_value=0, max_value=20,
                    value=existing_a if existing_a is not None else 0,
                    key=f"ko_a_{match_key}", label_visibility="collapsed",
                    disabled=not editable or "TBD" in [team_a, team_b]
                )
            with c5:
                st.write(f"**{team_b}**")

            if "TBD" in [team_a, team_b]:
                winners.append("TBD")
            elif h_score == a_score:
                existing_winner = knockout_preds.get((round_name, i, "winner"), None)
                options = [team_a, team_b]
                default_idx = options.index(existing_winner) if existing_winner in options else 0
                winner = st.selectbox(
                    "Draw — who advances (ET/Pens)?",
                    options, index=default_idx,
                    key=f"ko_w_{match_key}", disabled=not editable
                )
                winners.append(winner)
            else:
                winner = team_a if h_score > a_score else team_b
                st.caption(f"✅ {winner} advances")
                winners.append(winner)

            st.divider()
        return winners

    r32_teams = [(team_a, team_b) for (_, team_a, team_b) in r32_matchups]
    r32_winners = render_knockout_round("Round of 32", r32_teams)

    r16_teams = [(r32_winners[i], r32_winners[i+1]) for i in range(0, len(r32_winners), 2)]
    r16_winners = render_knockout_round("Round of 16", r16_teams)

    qf_teams = [(r16_winners[i], r16_winners[i+1]) for i in range(0, len(r16_winners), 2)]
    qf_winners = render_knockout_round("Quarter-Finals", qf_teams)

    sf_teams = [(qf_winners[i], qf_winners[i+1]) for i in range(0, len(qf_winners), 2)]
    sf_winners = render_knockout_round("Semi-Finals", sf_teams)

    if len(sf_winners) >= 2:
        final_teams = [(sf_winners[0], sf_winners[1])]
        final_winner = render_knockout_round("🏆 Final", final_teams)
        if final_winner and final_winner[0] != "TBD":
            st.markdown(f"### Your predicted champion: **{final_winner[0]}** 🏆")

    if editable:
        if st.button("💾 Save Knockout Predictions", type="primary"):
            all_rounds = [
                ("Round of 32", r32_teams, r32_winners),
                ("Round of 16", r16_teams, r16_winners),
                ("Quarter-Finals", qf_teams, qf_winners),
                ("Semi-Finals", sf_teams, sf_winners),
            ]
            if len(sf_winners) >= 2:
                all_rounds.append(("🏆 Final", final_teams, final_winner))

            for round_name, teams, winners in all_rounds:
                for i, (team_a, team_b) in enumerate(teams):
                    match_key = f"{round_name}_{i}"
                    h = st.session_state.get(f"ko_h_{match_key}", 0)
                    a = st.session_state.get(f"ko_a_{match_key}", 0)
                    save_knockout_prediction(username, round_name, i, "home", h)
                    save_knockout_prediction(username, round_name, i, "away", a)
                    save_knockout_prediction(username, round_name, i, "winner", winners[i])
            st.success("Knockout predictions saved!")


# --- Leaderboard Page ---

def leaderboard_page():
    st.title("🏅 Leaderboard")

    board = get_leaderboard()
    if not board:
        st.info("No participants yet or no official results entered.")
        return

    # Overall leaderboard
    st.subheader("Overall")
    overall = sorted(board, key=lambda x: x["total"], reverse=True)
    overall_df = pd.DataFrame([{"Player": r["username"], "Total Points": r["total"], "Group Pts": r["group_points"], "Knockout Pts": r["ko_points"]} for r in overall])
    overall_df.index = range(1, len(overall_df) + 1)
    st.dataframe(overall_df, use_container_width=True)

    # Group stage leaderboard
    st.subheader("Phase 1: Group Stage")
    group_board = sorted(board, key=lambda x: x["group_points"], reverse=True)
    group_df = pd.DataFrame([{"Player": r["username"], "Points": r["group_points"], "Exact Scores (3pts)": r["group_exact"], "Correct Outcomes (1pt)": r["group_correct"]} for r in group_board])
    group_df.index = range(1, len(group_df) + 1)
    st.dataframe(group_df, use_container_width=True)

    # Knockout stage leaderboard
    st.subheader("Phase 2: Knockout Stage")
    ko_board = sorted(board, key=lambda x: x["ko_points"], reverse=True)
    ko_df = pd.DataFrame([{"Player": r["username"], "Points": r["ko_points"], "Exact Scores (3pts)": r["ko_exact"], "Correct Outcomes (1pt)": r["ko_correct"]} for r in ko_board])
    ko_df.index = range(1, len(ko_df) + 1)
    st.dataframe(ko_df, use_container_width=True)

    # Current user's breakdown
    username = st.session_state.user["username"]
    if not st.session_state.user["is_admin"]:
        st.subheader("Your Detailed Results")
        result = calculate_user_total(username)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Points", result["total"])
        col2.metric("Group Stage", result["group_total"])
        col3.metric("Knockout Stage", result["ko_total"])

        if result["group_details"]:
            st.caption("Group Stage")
            details_df = pd.DataFrame(result["group_details"])
            details_df.columns = ["Match", "Your Prediction", "Actual Result", "Points"]
            st.dataframe(details_df, use_container_width=True, hide_index=True)

        if result["ko_details"]:
            st.caption("Knockout Stage")
            ko_details_df = pd.DataFrame(result["ko_details"])
            ko_details_df.columns = ["Match", "Your Prediction", "Actual Result", "Points"]
            st.dataframe(ko_details_df, use_container_width=True, hide_index=True)


# --- Admin Panel ---

def admin_page():
    st.title("⚙️ Admin Panel")

    tab1, tab2, tab3, tab4 = st.tabs(["Enter Results", "Lock/Unlock", "Manage Users", "Download Predictions"])

    with tab1:
        st.subheader("Enter Official Match Results")
        official = get_official_results()

        group_names = list(GROUPS.keys())
        selected_group = st.selectbox("Select Group", group_names, format_func=lambda x: f"Group {x}", key="admin_group")
        group_matches = [m for m in GROUP_MATCHES if m["group"] == selected_group]

        for match in group_matches:
            mid = match["match_id"]
            existing_h = official.get(mid, (None, None))[0]
            existing_a = official.get(mid, (None, None))[1]

            st.caption(f"📅 {match['date']} · ⏰ {match['time']} · 🏟️ {match['venue']}")
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
            with c1:
                st.write(f"**{match['home']}**")
            with c2:
                st.number_input(
                    "H", min_value=0, max_value=20,
                    value=existing_h if existing_h is not None else 0,
                    key=f"off_h_{mid}", label_visibility="collapsed"
                )
            with c3:
                st.write("vs")
            with c4:
                st.number_input(
                    "A", min_value=0, max_value=20,
                    value=existing_a if existing_a is not None else 0,
                    key=f"off_a_{mid}", label_visibility="collapsed"
                )
            with c5:
                st.write(f"**{match['away']}**")

        if st.button(f"💾 Save Official Results for Group {selected_group}", type="primary"):
            for match in group_matches:
                mid = match["match_id"]
                h = st.session_state[f"off_h_{mid}"]
                a = st.session_state[f"off_a_{mid}"]
                save_official_result(mid, h, a)
            st.success(f"Official results for Group {selected_group} saved!")

    with tab2:
        st.subheader("Prediction Locks")

        st.markdown("**Group Stage**")
        group_lock = is_locked("group")
        st.write(f"Status: {'🔒 LOCKED' if group_lock else '🔓 UNLOCKED'}")
        if group_lock:
            if st.button("🔓 Unlock Group Stage"):
                set_locked("group", False)
                st.rerun()
        else:
            if st.button("🔒 Lock Group Stage"):
                set_locked("group", True)
                st.rerun()

        st.divider()

        st.markdown("**Knockout Stage**")
        ko_lock = is_locked("knockout")
        st.write(f"Status: {'🔒 LOCKED' if ko_lock else '🔓 UNLOCKED'}")
        if ko_lock:
            if st.button("🔓 Unlock Knockout Stage"):
                set_locked("knockout", False)
                st.rerun()
        else:
            if st.button("🔒 Lock Knockout Stage"):
                set_locked("knockout", True)
                st.rerun()

        st.divider()

        st.markdown("**Knockout Mode**")
        current_mode = get_knockout_mode()
        st.write(f"Current mode: **{'Option 1 — Early Knockout' if current_mode == 'early' else 'Option 2 — Knockout Reset'}**")
        st.caption(
            "**Option 1 (Early):** Users predict the full bracket based on their group predictions before the tournament.\n\n"
            "**Option 2 (Reset):** Knockout bracket is built from official results. Users predict knockout matches only after group stage ends (Jun 27 11:30 PM – Jun 28 2:58 PM ET)."
        )
        if current_mode == "early":
            if st.button("🔄 Switch to Option 2 (Knockout Reset)"):
                set_knockout_mode("reset")
                st.rerun()
        else:
            if st.button("🔄 Switch to Option 1 (Early Knockout)"):
                set_knockout_mode("early")
                st.rerun()

    with tab3:
        st.subheader("Registered Users")
        sb = get_supabase()
        resp = sb.table("users").select("username, is_admin").execute()
        user_df = pd.DataFrame([{"Username": r["username"], "Admin": "Yes" if r["is_admin"] else "No"} for r in resp.data])
        st.dataframe(user_df, use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("Download User Predictions")
        sb = get_supabase()
        resp = sb.table("users").select("username").eq("is_admin", False).execute()
        all_users = [r["username"] for r in resp.data]

        if not all_users:
            st.info("No participants registered yet.")
        else:
            selected_user = st.selectbox("Select User", all_users, key="download_user")
            if st.button("📥 Generate Excel", type="primary"):
                user_preds = get_user_predictions(selected_user)
                ko_preds = get_user_knockout_predictions(selected_user)

                # Build group predictions sheet
                group_rows = []
                for match in GROUP_MATCHES:
                    mid = match["match_id"]
                    h, a = user_preds.get(mid, (None, None))
                    group_rows.append({
                        "Group": match["group"],
                        "Date": match["date"],
                        "Time": match["time"],
                        "Venue": match["venue"],
                        "Home": match["home"],
                        "Home Score": h,
                        "Away Score": a,
                        "Away": match["away"],
                    })
                group_df = pd.DataFrame(group_rows)

                # Build knockout predictions sheet
                # Reconstruct the bracket from the user's group predictions
                r32_matchups = get_knockout_teams_from_predictions(user_preds)
                r32_teams = [(team_a, team_b) for (_, team_a, team_b) in r32_matchups]

                def get_round_winners(round_name, matchups):
                    winners = []
                    for i, (team_a, team_b) in enumerate(matchups):
                        h = ko_preds.get((round_name, i, "home"), 0)
                        a = ko_preds.get((round_name, i, "away"), 0)
                        winner = ko_preds.get((round_name, i, "winner"), "TBD")
                        winners.append(winner)
                    return winners

                ko_rows = []
                all_knockout_rounds = [
                    ("Round of 32", r32_teams),
                ]

                # Build each subsequent round from previous winners
                r32_winners = get_round_winners("Round of 32", r32_teams)
                r16_teams = [(r32_winners[i], r32_winners[i+1]) for i in range(0, len(r32_winners), 2)]
                all_knockout_rounds.append(("Round of 16", r16_teams))

                r16_winners = get_round_winners("Round of 16", r16_teams)
                qf_teams = [(r16_winners[i], r16_winners[i+1]) for i in range(0, len(r16_winners), 2)]
                all_knockout_rounds.append(("Quarter-Finals", qf_teams))

                qf_winners = get_round_winners("Quarter-Finals", qf_teams)
                sf_teams = [(qf_winners[i], qf_winners[i+1]) for i in range(0, len(qf_winners), 2)]
                all_knockout_rounds.append(("Semi-Finals", sf_teams))

                sf_winners = get_round_winners("Semi-Finals", sf_teams)
                if len(sf_winners) >= 2:
                    final_teams = [(sf_winners[0], sf_winners[1])]
                    all_knockout_rounds.append(("🏆 Final", final_teams))

                for round_name, matchups in all_knockout_rounds:
                    for i, (team_a, team_b) in enumerate(matchups):
                        h = ko_preds.get((round_name, i, "home"), "")
                        a = ko_preds.get((round_name, i, "away"), "")
                        winner = ko_preds.get((round_name, i, "winner"), "")
                        ko_rows.append({
                            "Round": round_name,
                            "Match #": i + 1,
                            "Home Team": team_a,
                            "Home Score": h,
                            "Away Score": a,
                            "Away Team": team_b,
                            "Winner": winner,
                        })
                ko_df = pd.DataFrame(ko_rows)

                # Write to Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    group_df.to_excel(writer, sheet_name="Group Predictions", index=False)
                    if not ko_df.empty:
                        ko_df.to_excel(writer, sheet_name="Knockout Predictions", index=False)
                output.seek(0)

                st.download_button(
                    label=f"⬇️ Download {selected_user}'s predictions",
                    data=output,
                    file_name=f"{selected_user}_predictions.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


# --- Main App ---

def main():
    page = sidebar()

    if st.session_state.user is None:
        login_page()
    elif page == "Group Predictions":
        group_predictions_page()
    elif page == "Knockout Bracket":
        knockout_bracket_page()
    elif page == "Leaderboard":
        leaderboard_page()
    elif page == "Admin Panel":
        admin_page()


if __name__ == "__main__":
    main()
