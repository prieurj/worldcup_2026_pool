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
    init_db, get_supabase, get_knockout_teams_from_official, calculate_group_table,
    get_knockout_teams_from_predictions, save_prediction, get_user_predictions,
    save_knockout_prediction, get_user_knockout_predictions, calculate_user_total,
    get_leaderboard, save_official_result, get_official_results, is_locked, set_locked,
    get_knockout_mode, set_knockout_mode, is_knockout_open, update_username,
    get_payment_status, set_payment_status
)

st.set_page_config(page_title="World Cup 2026 Predictor", page_icon="⚽", layout="wide")
init_db()


# --- Auth Helpers ---

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(password: str, stored: str) -> bool:
    if not password or not stored:
        return False
    return hashlib.sha256(password.encode()).hexdigest() == stored


def register_user(username: str, password: str, request_admin: bool = False) -> bool:
    sb = get_supabase()
    existing = sb.table("users").select("username").eq("username", username).execute()
    if existing.data:
        return False
    sb.table("users").insert({
        "username": username,
        "password_hash": hash_password(password),
        "is_admin": False,
        "pending_admin": request_admin
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
        if not st.session_state.user["is_admin"]:
            username = st.session_state.user["username"]
            user_preds = get_user_predictions(username)
            group_count = sum(1 for mid, (h, a) in user_preds.items() if h is not None and a is not None)
            ko_preds = get_user_knockout_predictions(username)
            ko_count = sum(1 for (rnd, idx, field) in ko_preds if field == "home")
            st.sidebar.markdown(f"**Group Predictions:** {group_count} / 72")
            st.sidebar.markdown(f"**Knockout Predictions:** {ko_count} / 31")
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
        request_admin = st.checkbox("Request Admin Access", key="reg_admin")
        if st.button("Register"):
            if not new_user or not new_pass:
                st.error("Username and password required.")
            elif new_pass != confirm_pass:
                st.error("Passwords do not match.")
            else:
                if register_user(new_user, new_pass, request_admin):
                    if request_admin:
                        st.success("Registered! Admin access is pending approval.")
                    else:
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
    from knockout_bracket import knockout_bracket_page as _kbp
    _kbp()


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

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Enter GP Results", "Enter KO Results", "Lock/Unlock", "Manage Users", "Download Predictions"])

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
            is_played = mid in official

            st.caption(f"📅 {match['date']} · ⏰ {match['time']} · 🏟️ {match['venue']}")
            c0, c1, c2, c3, c4, c5 = st.columns([0.5, 3, 1, 1, 1, 3])
            with c0:
                st.checkbox("✓", value=is_played, key=f"played_{mid}", label_visibility="collapsed")
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
            sb = get_supabase()
            for match in group_matches:
                mid = match["match_id"]
                played = st.session_state.get(f"played_{mid}", False)
                if played:
                    h = st.session_state[f"off_h_{mid}"]
                    a = st.session_state[f"off_a_{mid}"]
                    save_official_result(mid, h, a)
                else:
                    # Remove result if unchecked
                    sb.table("official_results").delete().eq("match_id", mid).execute()
            st.success(f"Official results for Group {selected_group} saved!")

    with tab2:
        st.subheader("Enter Knockout Results")
        from knockout_bracket import KNOCKOUT_SCHEDULE, ROUND_ORDER, get_active_round, get_round_matchups

        sb_ko = get_supabase()
        r32_matchups = get_knockout_teams_from_official()

        # Get existing knockout official results
        try:
            ko_resp = sb_ko.table("official_knockout_results").select("round, match_index, home_score, away_score, winner").execute()
            ko_official = {}
            for r in ko_resp.data:
                ko_official[(r["round"], r["match_index"])] = (r["home_score"], r["away_score"], r["winner"])
        except Exception:
            ko_resp = sb_ko.table("official_knockout_results").select("round, match_index, home_score, away_score").execute()
            ko_official = {}
            for r in ko_resp.data:
                ko_official[(r["round"], r["match_index"])] = (r["home_score"], r["away_score"], None)

        selected_ko_round = st.selectbox("Select Round", ROUND_ORDER, key="admin_ko_round")
        matchups = get_round_matchups(selected_ko_round, r32_matchups, ko_official)
        schedule = KNOCKOUT_SCHEDULE[selected_ko_round]
        st.caption(f"📅 {schedule['first']} → {schedule['last']}")

        has_tbd = any("TBD" in [ta, tb] for ta, tb in matchups)
        if has_tbd:
            st.warning("⏳ Previous round results not complete — some matchups are TBD.")

        for i, (team_a, team_b) in enumerate(matchups):
            existing = ko_official.get((selected_ko_round, i))
            existing_h = existing[0] if existing else None
            existing_a = existing[1] if existing else None
            existing_w = existing[2] if existing else None
            is_played = existing is not None

            c0, c1, c2, c3, c4, c5 = st.columns([0.5, 3, 1, 1, 1, 3])
            with c0:
                st.checkbox("✓", value=is_played, key=f"ko_played_{selected_ko_round}_{i}", label_visibility="collapsed",
                            disabled="TBD" in [team_a, team_b])
            with c1:
                st.write(f"**{team_a}**")
            with c2:
                st.number_input(
                    "H", min_value=0, max_value=20,
                    value=existing_h if existing_h is not None else 0,
                    key=f"ko_off_h_{selected_ko_round}_{i}", label_visibility="collapsed",
                    disabled="TBD" in [team_a, team_b]
                )
            with c3:
                st.write("vs")
            with c4:
                st.number_input(
                    "A", min_value=0, max_value=20,
                    value=existing_a if existing_a is not None else 0,
                    key=f"ko_off_a_{selected_ko_round}_{i}", label_visibility="collapsed",
                    disabled="TBD" in [team_a, team_b]
                )
            with c5:
                st.write(f"**{team_b}**")

            # Winner selector for draws
            if "TBD" not in [team_a, team_b]:
                h_val = st.session_state.get(f"ko_off_h_{selected_ko_round}_{i}", 0)
                a_val = st.session_state.get(f"ko_off_a_{selected_ko_round}_{i}", 0)
                if h_val == a_val:
                    options = [team_a, team_b]
                    default_idx = options.index(existing_w) if existing_w in options else 0
                    st.selectbox(
                        "Who advanced (ET/Pens)?",
                        options, index=default_idx,
                        key=f"ko_off_w_{selected_ko_round}_{i}"
                    )

            st.divider()

        if st.button(f"💾 Save {selected_ko_round} Results", type="primary", key="save_ko_results"):
            saved = 0
            for i, (team_a, team_b) in enumerate(matchups):
                played = st.session_state.get(f"ko_played_{selected_ko_round}_{i}", False)
                if played and "TBD" not in [team_a, team_b]:
                    h = st.session_state[f"ko_off_h_{selected_ko_round}_{i}"]
                    a = st.session_state[f"ko_off_a_{selected_ko_round}_{i}"]
                    if h == a:
                        winner = st.session_state.get(f"ko_off_w_{selected_ko_round}_{i}", team_a)
                    elif h > a:
                        winner = team_a
                    else:
                        winner = team_b
                    sb_ko.table("official_knockout_results").upsert({
                        "round": selected_ko_round,
                        "match_index": i,
                        "home_score": h,
                        "away_score": a,
                        "winner": winner
                    }).execute()
                    saved += 1
                elif not played:
                    sb_ko.table("official_knockout_results").delete().eq("round", selected_ko_round).eq("match_index", i).execute()
            st.success(f"Saved {saved} results for {selected_ko_round}!")

    with tab3:
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
        if current_mode == "early":
            if st.button("🔄 Switch to Option 2 (Knockout Reset)"):
                set_knockout_mode("reset")
                st.rerun()
        else:
            if st.button("🔄 Switch to Option 1 (Early Knockout)"):
                set_knockout_mode("early")
                st.rerun()

    with tab4:
        st.subheader("Registered Users")
        sb = get_supabase()
        resp = sb.table("users").select("username, is_admin, pending_admin").execute()

        # Get prediction counts per user
        group_counts = {}
        ko_counts = {}
        for r in resp.data:
            uname = r["username"]
            u_preds = sb.table("predictions").select("match_id", count="exact").eq("username", uname).execute()
            group_counts[uname] = u_preds.count if u_preds.count else 0
            u_ko = sb.table("knockout_predictions").select("field", count="exact").eq("username", uname).eq("field", "winner").execute()
            ko_counts[uname] = u_ko.count if u_ko.count else 0

        user_df = pd.DataFrame([{
            "Username": r["username"],
            "Admin": "Yes" if r["is_admin"] else "No",
            "Group Preds": group_counts.get(r["username"], 0),
            "KO Preds": ko_counts.get(r["username"], 0),
        } for r in resp.data])
        st.dataframe(user_df, use_container_width=True, hide_index=True)

        # Pending admin requests
        pending = [r for r in resp.data if r.get("pending_admin") and not r["is_admin"]]
        if pending:
            st.divider()
            st.subheader("⏳ Pending Admin Requests")
            for user in pending:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{user['username']}**")
                with col2:
                    if st.button("✅ Approve", key=f"approve_{user['username']}"):
                        sb.table("users").update({"is_admin": True, "pending_admin": False}).eq("username", user["username"]).execute()
                        st.rerun()
                with col3:
                    if st.button("❌ Deny", key=f"deny_{user['username']}"):
                        sb.table("users").update({"pending_admin": False}).eq("username", user["username"]).execute()
                        st.rerun()

        # Reset password
        st.divider()
        st.subheader("Entry Fee Tracker")
        payment = get_payment_status()
        non_admins = [r for r in resp.data if not r["is_admin"]]
        for user in non_admins:
            uname = user["username"]
            paid = st.checkbox(
                f"{uname}",
                value=payment.get(uname, False),
                key=f"paid_{uname}"
            )
            if paid != payment.get(uname, False):
                set_payment_status(uname, paid)

        # Reset password
        st.divider()
        st.subheader("Reset User Password")
        user_names = [r["username"] for r in resp.data]
        reset_user = st.selectbox("Select User", user_names, key="reset_user_select")
        new_pw = st.text_input("New Password", type="password", key="reset_pw")
        if st.button("🔑 Reset Password", type="primary"):
            if not new_pw:
                st.error("Password cannot be empty.")
            else:
                sb.table("users").update({"password_hash": hash_password(new_pw)}).eq("username", reset_user).execute()
                st.success(f"Password reset for {reset_user}.")

        # Delete user
        st.divider()
        st.subheader("🗑️ Delete User")
        all_user_names = [r["username"] for r in resp.data if r["username"] != st.session_state.user["username"]]
        if all_user_names:
            delete_user = st.selectbox("Select User to Delete", all_user_names, key="delete_user_select")
            if st.button("❌ Delete User", type="primary"):
                sb.table("predictions").delete().eq("username", delete_user).execute()
                sb.table("knockout_predictions").delete().eq("username", delete_user).execute()
                sb.table("users").delete().eq("username", delete_user).execute()
                st.success(f"Deleted {delete_user} and all their predictions.")
                st.rerun()

    with tab5:
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
    username = st.session_state.user["username"]
    st.write(f"**Username:** {username}")

    st.subheader("Change Username")
    new_name = st.text_input("New Username", key="new_username")
    if st.button("Update Username", type="primary"):
        if not new_name or not new_name.strip():
            st.error("Username cannot be empty.")
        elif new_name.strip() == username:
            st.warning("That's already your username.")
        else:
            if update_username(username, new_name.strip()):
                st.session_state.user["username"] = new_name.strip()
                st.success("Username updated!")
                st.rerun()
            else:
                st.error("Username already taken.")

    st.divider()
    st.subheader("Export My Predictions")
    if st.button("⬇️ Download My Predictions as Excel"):
        user_preds = get_user_predictions(username)
        ko_preds = get_user_knockout_predictions(username)

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

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            group_df.to_excel(writer, sheet_name="Group Predictions", index=False)
            if not ko_df.empty:
                ko_df.to_excel(writer, sheet_name="Knockout Predictions", index=False)
        output.seek(0)

        st.download_button(
            label=f"📥 Download {username}_predictions.xlsx",
            data=output,
            file_name=f"{username}_predictions.xlsx",
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
    elif page == "My Profile":
        profile_page()
    elif page == "Admin Panel":
        admin_page()


if __name__ == "__main__":
    main()
