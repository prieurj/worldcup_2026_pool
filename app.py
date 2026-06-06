"""
FIFA World Cup 2026 Predictor & Office Pool System
Main Streamlit application.
"""
import streamlit as st
import pandas as pd
import bcrypt
from io import BytesIO
from data import GROUPS, GROUP_MATCHES, KNOCKOUT_R32_SLOTS, KNOCKOUT_ROUNDS
from logic import (
    init_db, get_db, calculate_group_table, get_knockout_teams_from_predictions,
    save_prediction, get_user_predictions, save_knockout_prediction,
    get_user_knockout_predictions, calculate_user_total, get_leaderboard,
    save_official_result, get_official_results, is_locked, set_locked,
    update_username, get_payment_status, set_payment_status
)

st.set_page_config(page_title="World Cup 2026 Predictor", page_icon="⚽", layout="wide")
init_db()


# --- Auth Helpers ---

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def register_user(username: str, password: str, is_admin: bool = False) -> bool:
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            (username, hash_password(password), 1 if is_admin else 0)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()



def authenticate(username: str, password: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, password_hash, is_admin FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and check_password(password, row["password_hash"]):
        return {"user_id": row["user_id"], "username": username, "is_admin": bool(row["is_admin"])}
    return None


# --- Session State ---

if "user" not in st.session_state:
    st.session_state.user = None


# --- Sidebar Navigation ---

def sidebar():
    st.sidebar.title("⚽ WC 2026 Predictor")
    if st.session_state.user:
        st.sidebar.write(f"Logged in as: **{st.session_state.user['username']}**")
        pages = ["Group Predictions", "Knockout Bracket", "Leaderboard", "My Profile"]
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

    locked = is_locked()
    if locked:
        st.warning("🔒 Predictions are locked. You can view but not edit.")

    user_id = st.session_state.user["user_id"]
    existing_preds = get_user_predictions(user_id)

    # Group selector
    group_names = list(GROUPS.keys())
    selected_group = st.selectbox("Select Group", group_names, format_func=lambda x: f"Group {x}")

    teams = GROUPS[selected_group]
    group_matches = [m for m in GROUP_MATCHES if m["group"] == selected_group]

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader(f"Group {selected_group} Matches")
        current_preds = dict(existing_preds)  # copy

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
                    save_prediction(user_id, mid, h, a)
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

def _get_knockout_winner(home_score, away_score, home_team, away_team):
    """Determine winner from knockout score (home team wins ties for simplicity)."""
    if home_score > away_score:
        return home_team
    elif away_score > home_score:
        return away_team
    else:
        return home_team  # In case of draw, home team listed first advances (user picks via score)


def knockout_bracket_page():
    st.title("🏆 Knockout Bracket")

    locked = is_locked()
    if locked:
        st.warning("🔒 Predictions are locked.")

    user_id = st.session_state.user["user_id"]
    user_preds = get_user_predictions(user_id)
    knockout_preds = get_user_knockout_predictions(user_id)

    # Get R32 matchups from group predictions
    r32_matchups = get_knockout_teams_from_predictions(user_preds)

    st.caption("Teams are auto-populated from your group predictions. Enter scores for each knockout match (higher score advances; if tied, pick a winner below).")

    def render_knockout_round(round_name, matchups):
        """Render a knockout round with score inputs. Returns list of winners."""
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
                    disabled=locked or "TBD" in [team_a, team_b]
                )
            with c3:
                st.write("vs")
            with c4:
                a_score = st.number_input(
                    "A", min_value=0, max_value=20,
                    value=existing_a if existing_a is not None else 0,
                    key=f"ko_a_{match_key}", label_visibility="collapsed",
                    disabled=locked or "TBD" in [team_a, team_b]
                )
            with c5:
                st.write(f"**{team_b}**")

            # Determine winner
            if "TBD" in [team_a, team_b]:
                winners.append("TBD")
            elif h_score == a_score:
                # Tie — user must pick who advances (penalties/ET)
                existing_winner = knockout_preds.get((round_name, i, "winner"), None)
                options = [team_a, team_b]
                default_idx = options.index(existing_winner) if existing_winner in options else 0
                winner = st.selectbox(
                    "Draw — who advances (ET/Pens)?",
                    options, index=default_idx,
                    key=f"ko_w_{match_key}", disabled=locked
                )
                winners.append(winner)
            else:
                winner = team_a if h_score > a_score else team_b
                st.caption(f"✅ {winner} advances")
                winners.append(winner)

            st.divider()
        return winners

    # Round of 32
    r32_teams = [(team_a, team_b) for (_, team_a, team_b) in r32_matchups]
    r32_winners = render_knockout_round("Round of 32", r32_teams)

    # Round of 16
    r16_teams = [(r32_winners[i], r32_winners[i+1]) for i in range(0, len(r32_winners), 2)]
    r16_winners = render_knockout_round("Round of 16", r16_teams)

    # Quarter-Finals
    qf_teams = [(r16_winners[i], r16_winners[i+1]) for i in range(0, len(r16_winners), 2)]
    qf_winners = render_knockout_round("Quarter-Finals", qf_teams)

    # Semi-Finals
    sf_teams = [(qf_winners[i], qf_winners[i+1]) for i in range(0, len(qf_winners), 2)]
    sf_winners = render_knockout_round("Semi-Finals", sf_teams)

    # Final
    if len(sf_winners) >= 2:
        final_teams = [(sf_winners[0], sf_winners[1])]
        final_winner = render_knockout_round("🏆 Final", final_teams)
        if final_winner and final_winner[0] != "TBD":
            st.markdown(f"### Your predicted champion: **{final_winner[0]}** 🏆")

    # Save all knockout predictions
    if not locked:
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
                    save_knockout_prediction(user_id, round_name, i, "home", h)
                    save_knockout_prediction(user_id, round_name, i, "away", a)
                    save_knockout_prediction(user_id, round_name, i, "winner", winners[i])
            st.success("Knockout predictions saved!")


# --- Leaderboard Page ---

def leaderboard_page():
    st.title("🏅 Leaderboard")

    board = get_leaderboard()
    if not board:
        st.info("No participants yet or no official results entered.")
        return

    is_admin = st.session_state.user["is_admin"]

    if is_admin:
        # Show leaderboard with paid checkboxes
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT user_id, username FROM users WHERE is_admin = 0")
        user_map = {row["username"]: row["user_id"] for row in c.fetchall()}
        conn.close()
        payment = get_payment_status()

        st.subheader("Entry Fee Tracker")
        for entry in board:
            uname = entry["username"]
            uid = user_map.get(uname)
            if uid is None:
                continue
            paid = st.checkbox(
                f"{uname} — {entry['points']} pts",
                value=payment.get(uid, False),
                key=f"paid_{uid}"
            )
            if paid != payment.get(uid, False):
                set_payment_status(uid, paid)
    else:
        df = pd.DataFrame(board)
        df.index = range(1, len(df) + 1)
        df.columns = ["Player", "Total Points", "Exact Scores (3pts)", "Correct Outcomes (1pt)"]
        st.dataframe(df, use_container_width=True)

    # Show current user's breakdown
    if not st.session_state.user["is_admin"]:
        st.subheader("Your Detailed Results")
        result = calculate_user_total(st.session_state.user["user_id"])
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Points", result["total"])
        col2.metric("Exact Scores", result["exact"])
        col3.metric("Correct Outcomes", result["correct_outcome"])
        col4.metric("Wrong", result["wrong"])

        if result["details"]:
            details_df = pd.DataFrame(result["details"])
            details_df.columns = ["Match", "Your Prediction", "Actual Result", "Points"]
            st.dataframe(details_df, use_container_width=True, hide_index=True)


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
                h_score = st.number_input(
                    "H", min_value=0, max_value=20,
                    value=existing_h if existing_h is not None else 0,
                    key=f"off_h_{mid}", label_visibility="collapsed"
                )
            with c3:
                st.write("vs")
            with c4:
                a_score = st.number_input(
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
        st.subheader("Prediction Lock")
        current_lock = is_locked()
        st.write(f"Current status: {'🔒 LOCKED' if current_lock else '🔓 UNLOCKED'}")
        if current_lock:
            if st.button("🔓 Unlock Predictions"):
                set_locked(False)
                st.rerun()
        else:
            if st.button("🔒 Lock Predictions (before tournament starts)"):
                set_locked(True)
                st.rerun()

    with tab3:
        st.subheader("Registered Users")
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT user_id, username, is_admin FROM users")
        users = c.fetchall()
        # Count group predictions per user
        c.execute("SELECT user_id, COUNT(*) as cnt FROM predictions GROUP BY user_id")
        p1_counts = {row["user_id"]: row["cnt"] for row in c.fetchall()}
        # Count knockout predictions per user (only 'winner' fields = 1 per match)
        c.execute("SELECT user_id, COUNT(*) as cnt FROM knockout_predictions WHERE field = 'winner' GROUP BY user_id")
        p2_counts = {row["user_id"]: row["cnt"] for row in c.fetchall()}
        conn.close()
        user_df = pd.DataFrame([{
            "Username": r["username"],
            "Admin": "Yes" if r["is_admin"] else "No",
            "P1P (Group)": p1_counts.get(r["user_id"], 0),
            "P2P (Knockout)": p2_counts.get(r["user_id"], 0),
        } for r in users])
        st.dataframe(user_df, use_container_width=True, hide_index=True)


    with tab4:
        st.subheader("Download User Predictions")
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT user_id, username FROM users WHERE is_admin = 0")
        all_users = c.fetchall()
        conn.close()

        if not all_users:
            st.info("No participants registered yet.")
        else:
            user_options = {row["username"]: row["user_id"] for row in all_users}
            selected_user = st.selectbox("Select User", list(user_options.keys()), key="download_user")
            if st.button("📥 Generate Excel", type="primary"):
                sel_user_id = user_options[selected_user]
                user_preds = get_user_predictions(sel_user_id)
                ko_preds = get_user_knockout_predictions(sel_user_id)

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
                ko_rows = []
                for (round_name, match_idx, field), val in sorted(ko_preds.items()):
                    if field == "winner":
                        home = ko_preds.get((round_name, match_idx, "home"), "")
                        away = ko_preds.get((round_name, match_idx, "away"), "")
                        ko_rows.append({
                            "Round": round_name,
                            "Match #": match_idx + 1,
                            "Home Score": home,
                            "Away Score": away,
                            "Winner": val,
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


# --- My Profile Page ---

def profile_page():
    st.title("👤 My Profile")
    st.write(f"**User ID:** {st.session_state.user['user_id']}")
    st.write(f"**Current Username:** {st.session_state.user['username']}")

    st.subheader("Change Username")
    new_name = st.text_input("New Username", key="new_username")
    if st.button("Update Username", type="primary"):
        if not new_name or not new_name.strip():
            st.error("Username cannot be empty.")
        elif new_name.strip() == st.session_state.user["username"]:
            st.warning("That's already your username.")
        else:
            if update_username(st.session_state.user["user_id"], new_name.strip()):
                st.session_state.user["username"] = new_name.strip()
                st.success("Username updated! Use your new username to log in next time.")
                st.rerun()
            else:
                st.error("Username already taken. Choose a different one.")


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
    elif page == "My Profile":
        profile_page()
    elif page == "Admin Panel":
        admin_page()


if __name__ == "__main__":
    main()
