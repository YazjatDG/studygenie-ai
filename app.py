import streamlit as str_lt
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import io
import time

# --- INITIAL APP STATE SETUP ---
str_lt.set_page_config(page_title="StudyGenie AI", page_icon="🔮", layout="wide")

from sqlalchemy import func
from database import init_db, SessionLocal, User, Subject, Homework, Exam, StudySession, Note, Goal, TimetableItem
from ai import AIService

init_db()
db = SessionLocal()

# Global Theme Injector
str_lt.markdown("""
    <style>
    .reportview-container { background: linear-gradient(135deg, #0F172A, #1E1B4B); }
    div[data-testid="stCard"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
    }
    h1, h2, h3 { color: #F8FAFC !important; font-weight: 700; }
    .stButton>button {
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4); }
    </style>
""", unsafe_allow_html=True)

# Session tracking initialization
if "pomodoro_active" not in str_lt.session_state:
    str_lt.session_state.pomodoro_active = False
if "pomo_time" not in str_lt.session_state:
    str_lt.session_state.pomo_time = 1500

user_profile = db.query(User).first()

# --- NAVIGATION SIDEBAR ---
str_lt.sidebar.title("🔮 StudyGenie AI")
str_lt.sidebar.markdown(f"**Welcome back, {user_profile.username}!**")
str_lt.sidebar.markdown(f"🔥 **Streak:** {user_profile.streak} Days")

app_page = str_lt.sidebar.radio("Navigate To", [
    "Dashboard", "Subjects", "Study Planner", "Homework Manager", 
    "Exams", "Notes", "AI Study Assistant", "Analytics", "Goals", "Settings"
])

# Utility Context String compilation for metrics anchoring
def compute_metrics_context():
    total_subs = db.query(Subject).count()
    total_hw = db.query(Homework).filter(Homework.status == "Pending").count()
    total_ex = db.query(Exam).count()
    return f"Subjects: {total_subs}, Pending Homeworks: {total_hw}, Total Exams Scheduled: {total_ex}."

# --- PAGES ROUTING MODULES ---

if app_page == "Dashboard":
    str_lt.title("🚀 Executive Command Dashboard")
    
    # Live Interactive motivation banner
    with str_lt.spinner("Fetching motivation matrix..."):
        motivational_quote = AIService.daily_motivation(user_profile.streak)
    str_lt.info(f"💡 *{motivational_quote.strip()}*")
    
    # Micro Metrics Grid Layout
    col1, col2, col3, col4 = str_lt.columns(4)
    with col1:
        str_lt.metric("Study Streak", f"🔥 {user_profile.streak} Days")
    with col2:
        pending_hw_count = db.query(Homework).filter(Homework.status == 'Pending').count()
        str_lt.metric("Pending Tasks", f"📝 {pending_hw_count}")
    with col3:
        upcoming_exams_count = db.query(Exam).filter(Exam.date >= date.today()).count()
        str_lt.metric("Upcoming Exams", f"🎯 {upcoming_exams_count}")
    with col4:
        total_minutes = db.query(func.coalesce(func.sum(StudySession.duration_minutes), 0)).scalar()
        str_lt.metric("Total Time Studied", f"⏱️ {total_minutes}m")

    str_lt.markdown("---")
    
    left_layout, right_layout = str_lt.columns([2, 1])
    
    with left_layout:
        str_lt.subheader("📅 Today's Active Timetable Slots")
        today_name = datetime.now().strftime("%A")
        items = db.query(TimetableItem).filter(TimetableItem.day == today_name).all()
        if items:
            df_sched = pd.DataFrame([{"Time Slot": i.time_slot, "Subject Assignment": i.subject_name} for i in items])
            str_lt.table(df_sched)
        else:
            str_lt.write("No structural dynamic timetable tracks saved for today.")

        str_lt.subheader("⚠️ Urgent Assignments Due")
        hw_list = db.query(Homework).filter(Homework.status == "Pending").order_by(Homework.due_date.asc()).limit(3).all()
        if hw_list:
            for h in hw_list:
                str_lt.markdown(f"- **[{h.subject.name}]** {h.title} (Due: {h.due_date}) — `{h.priority}` Priority")
        else:
            str_lt.success("All assignments systematically cleared!")

    with right_layout:
        str_lt.subheader("🔮 Genie Insights Engine")
        if str_lt.button("Predict Exam Readiness Score"):
            raw_metrics = f"Studied Minutes: {total_minutes}, Unfinished Homework: {pending_hw_count}, Total Subjects: {db.query(Subject).count()}"
            with str_lt.spinner("Analyzing performance vectors..."):
                readiness_result = AIService.predict_readiness(raw_metrics)
            str_lt.success(readiness_result)
            
        str_lt.subheader("⏱️ Instant Pomodoro Focus")
        p_col1, p_col2 = str_lt.columns(2)
        with p_col1:
            if str_lt.button("Start 25m Focus Block"):
                str_lt.session_state.pomodoro_active = True
        with p_col2:
            if str_lt.button("Reset Timer"):
                str_lt.session_state.pomodoro_active = False
                str_lt.session_state.pomo_time = 1500
        
        if str_lt.session_state.pomodoro_active:
            str_lt.warning("⏰ Deep Work Phase Active. Keep this tab open.")


elif app_page == "Subjects":
    str_lt.title("📚 Subject Inventory Hub")
    
    with str_lt.form("add_subject_form", clear_on_submit=True):
        str_lt.subheader("Add New Academic Area")
        sub_name = str_lt.text_input("Subject Name (Unique key designation)")
        sub_color = str_lt.color_picker("Aesthetic Color Identification Track", "#6366F1")
        if str_lt.form_submit_button("Commit Subject to Memory"):
            if sub_name.strip():
                if db.query(Subject).filter(Subject.name == sub_name.strip()).first():
                    str_lt.error("Subject key allocation duplicate detected.")
                else:
                    db.add(Subject(name=sub_name.strip(), color=sub_color))
                    db.commit()
                    str_lt.success(f"Successfully tracking: {sub_name}")
                    str_lt.rerun()

    str_lt.markdown("---")
    str_lt.subheader("Currently Tracking Subjects")
    all_subjects = db.query(Subject).all()
    
    if all_subjects:
        for s in all_subjects:
            col_s1, col_s2 = str_lt.columns([4, 1])
            with col_s1:
                total_hours = sum([sess.duration_minutes for sess in s.sessions]) / 60.0
                str_lt.markdown(f"<h4 style='color:{s.color};'>● {s.name}</h4> <small>Logged Exposure: {total_hours:.2f} Hours</small>", unsafe_allow_html=True)
            with col_s2:
                if str_lt.button("Drop Module", key=f"del_sub_{s.id}"):
                    db.delete(s)
                    db.commit()
                    str_lt.rerun()
    else:
        str_lt.info("No active structural learning domains specified.")


elif app_page == "Study Planner":
    str_lt.title("🗓️ Smart Scheduler Engine")
    
    tab1, tab2 = str_lt.tabs(["AI Automated Optimization Framework", "Manual Core Planner Matrix"])
    
    all_subs_list = [s.name for s in db.query(Subject).all()]
    
    with tab1:
        str_lt.subheader("Generate Optimized Engine Recommendations")
        hours_target = str_lt.slider("Target Daily Intensity Allocation (Hours)", 1, 12, 4)
        if str_lt.button("Initialize Generative Timetable System"):
            if not all_subs_list:
                str_lt.error("Configure subjects in inventory module prior to execution.")
            else:
                with str_lt.spinner("Synthesizing balance patterns..."):
                    timetable_output = AIService.generate_timetable(all_subs_list, hours_target)
                str_lt.markdown(timetable_output)
                
        str_lt.markdown("---")
        str_lt.subheader("AI Disruption Mitigation Routine")
        missed_sub = str_lt.selectbox("Select Block Target Missed", ["None"] + all_subs_list)
        missed_reason = str_lt.text_input("Operational failure reason (e.g., Illness, Fatigue)")
        if str_lt.button("Recalibrate Study Path Plan"):
            if missed_sub != "None" and missed_reason:
                with str_lt.spinner("Generating recovery routes..."):
                    rearrange_res = AIService.rearrange_timetable(missed_sub, missed_reason)
                str_lt.info(rearrange_res)
                
    with tab2:
        str_lt.subheader("Saved Timetable Ledger Structure")
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        with str_lt.form("manual_slot_add"):
            d_sel = str_lt.selectbox("Target Routing Day", days_of_week)
            t_sel = str_lt.text_input("Execution Time Bracket (e.g. 04:00 PM - 05:30 PM)")
            s_sel = str_lt.selectbox("Target Domain Block Allocation", all_subs_list if all_subs_list else ["None"])
            if str_lt.form_submit_button("Anchor Slot Definition"):
                if t_sel and s_sel != "None":
                    db.add(TimetableItem(day=d_sel, time_slot=t_sel, subject_name=s_sel))
                    db.commit()
                    str_lt.rerun()
                    
        saved_items = db.query(TimetableItem).all()
        if saved_items:
            df_m = pd.DataFrame([{"ID": s.id, "Day": s.day, "Time Slot": s.time_slot, "Subject": s.subject_name} for s in saved_items])
            str_lt.dataframe(df_m, use_container_width=True)
            clear_id = str_lt.number_input("Enter Row ID reference to wipe", min_value=1, step=1)
            if str_lt.button("Purge Specific Row Block Mapping"):
                target_wipe = db.query(TimetableItem).filter(TimetableItem.id == clear_id).first()
                if target_wipe:
                    db.delete(target_wipe)
                    db.commit()
                    str_lt.rerun()


elif app_page == "Homework Manager":
    str_lt.title("📝 Structural Task Assignment Engine")
    
    all_subs = db.query(Subject).all()
    if not all_subs:
        str_lt.warning("Define tracking nodes inside the Subjects module before recording deliverables.")
    else:
        with str_lt.form("homework_entry", clear_on_submit=True):
            hw_title = str_lt.text_input("Deliverable Description / Topic Mapping")
            hw_sub = str_lt.selectbox("Core Module Owner", [s.name for s in all_subs])
            hw_date = str_lt.date_input("Hard Milestone Deadline Date", date.today() + timedelta(days=2))
            hw_prio = str_lt.selectbox("Task Urgency Prioritization Level", ["High", "Medium", "Low"])
            if str_lt.form_submit_button("Register Structural Task Deliverable"):
                target_sub = db.query(Subject).filter(Subject.name == hw_sub).first()
                db.add(Homework(title=hw_title, due_date=hw_date, priority=hw_prio, status="Pending", subject_id=target_sub.id))
                db.commit()
                str_lt.success("Task successfully queued inside engine repository.")
                str_lt.rerun()
                
        str_lt.markdown("---")
        str_lt.subheader("Active Tasks Backlog Engine Matrix")
        
        all_homeworks = db.query(Homework).all()
        if all_homeworks:
            for hw in all_homeworks:
                hw_col1, hw_col2, hw_col3 = str_lt.columns([3, 1, 1])
                with hw_col1:
                    status_emoji = "✅" if hw.status == "Completed" else "⏳"
                    str_lt.markdown(f"**{status_emoji} {hw.title}** — *{hw.subject.name}* (Due: {hw.due_date})")
                with hw_col2:
                    str_lt.info(f"Priority: {hw.priority}")
                with hw_col3:
                    if hw.status == "Pending":
                        if str_lt.button("Resolve Task", key=f"complete_hw_{hw.id}"):
                            hw.status = "Completed"
                            db.commit()
                            str_lt.rerun()
                    else:
                        if str_lt.button("Purge Archive Record", key=f"del_hw_{hw.id}"):
                            db.delete(hw)
                            db.commit()
                            str_lt.rerun()
        else:
            str_lt.info("Backlog operational vector completely empty.")


elif app_page == "Exams":
    str_lt.title("🎯 Milestone Examinations Radar Matrix")
    
    all_subs = db.query(Subject).all()
    if not all_subs:
        str_lt.warning("Configure tracking categories inside Subjects panel first.")
    else:
        with str_lt.form("exam_add"):
            ex_title = str_lt.text_input("Exam Name / Milestone ID Code")
            ex_sub = str_lt.selectbox("Subject Focus Allocation", [s.name for s in all_subs])
            ex_date = str_lt.date_input("Target Date Evaluation Execution", date.today() + timedelta(days=7))
            ex_target = str_lt.number_input("Target Evaluation Benchmark (%)", 0.0, 100.0, 90.0)
            if str_lt.form_submit_button("Track Exam Vector"):
                target_sub = db.query(Subject).filter(Subject.name == ex_sub).first()
                db.add(Exam(title=ex_title, date=ex_date, target_marks=ex_target, subject_id=target_sub.id))
                db.commit()
                str_lt.success("Target evaluation track registered successfully.")
                str_lt.rerun()
                
        str_lt.markdown("---")
        str_lt.subheader("Active Exams Tracking Pipelines")
        all_exams = db.query(Exam).all()
        if all_exams:
            for ex in all_exams:
                days_remaining = (ex.date - date.today()).days
                e_col1, e_col2 = str_lt.columns([3, 1])
                with e_col1:
                    str_lt.markdown(f"### {ex.title} — `{ex.subject.name}`")
                    str_lt.write(f"Milestone Target Standard: **{ex.target_marks}%** | Planned date execution: {ex.date}")
                with e_col2:
                    if days_remaining > 0:
                        str_lt.metric("Countdown Window", f"{days_remaining} Days Left")
                    elif days_remaining == 0:
                        str_lt.warning("🔥 Active Benchmark testing window today!")
                    else:
                        str_lt.error(f"Passed by {abs(days_remaining)} days")
                if str_lt.button("Delete Exam Tracker Reference", key=f"del_ex_{ex.id}"):
                    db.delete(ex)
                    db.commit()
                    str_lt.rerun()
        else:
            str_lt.info("No primary benchmark verification milestones assigned.")


elif app_page == "Notes":
    str_lt.title("📂 Generative Learning Materials Matrix")
    
    str_lt.subheader("Synthesize Text Knowledge Base Nodes")
    n_title = str_lt.text_input("Intellectual Property Node Label (Title)")
    n_content = str_lt.text_area("Raw Text Structural Payload Content")
    
    if str_lt.button("Anchor Payload Node and Initialize Analysis Engine"):
        if n_title.strip() and n_content.strip():
            with str_lt.spinner("Running core semantic pipeline metrics components..."):
                sum_text = AIService.summarize_notes(n_content)
                flash_text = AIService.generate_flashcards(n_content)
                quest_text = AIService.create_mcqs(n_content)
                
            new_note = Note(title=n_title.strip(), content=n_content, summary=sum_text, flashcards=flash_text, questions=quest_text)
            db.add(new_note)
            db.commit()
            str_lt.success("Structural note metadata mapped to centralized database storage container.")
            str_lt.rerun()

    str_lt.markdown("---")
    str_lt.subheader("Saved Knowledge Inventories")
    all_notes = db.query(Note).all()
    if all_notes:
        for n in all_notes:
            with str_lt.expander(f"📖 Reference Node: {n.title}"):
                ntabs = str_lt.tabs(["Original Source Material", "AI Comprehensive Summary", "AI Flashcard Pairings", "AI MCQ Verification Set"])
                with ntabs[0]:
                    str_lt.write(n.content)
                with ntabs[1]:
                    str_lt.markdown(n.summary)
                with ntabs[2]:
                    str_lt.markdown(n.flashcards)
                with ntabs[3]:
                    str_lt.markdown(n.questions)
                if str_lt.button("Wipe Note Record Base", key=f"del_note_{n.id}"):
                    db.delete(n)
                    db.commit()
                    str_lt.rerun()
    else:
        str_lt.info("Knowledge inventory databases presently lack registered source nodes.")


elif app_page == "AI Study Assistant":
    str_lt.title("💬 StudyGenie AI Cognitive Engine Hub")
    str_lt.caption("Consult your structural academic engineering strategist for live solutions.")
    
    if "chat_history" not in str_lt.session_state:
        str_lt.session_state.chat_history = []
        
    for msg in str_lt.session_state.chat_history:
        with str_lt.chat_message(msg["role"]):
            str_lt.markdown(msg["text"])
            
    user_query = str_lt.chat_input("Input mathematical, technical or structural optimization inquiries...")
    if user_query:
        with str_lt.chat_message("user"):
            str_lt.markdown(user_query)
        str_lt.session_state.chat_history.append({"role": "user", "text": user_query})
        
        ctx_anchor = compute_metrics_context()
        with str_lt.chat_message("assistant"):
            with str_lt.spinner("Computing structural response paths..."):
                engine_reply = AIService.chat_assistant(user_query, ctx_anchor)
            str_lt.markdown(engine_reply)
        str_lt.session_state.chat_history.append({"role": "assistant", "text": engine_reply})


elif app_page == "Analytics":
    str_lt.title("📊 Analytical System Insight Graphs")
    
    # Load session log history sets
    sessions_data = db.query(StudySession).all()
    if not sessions_data:
        str_lt.info("Log your active work sessions inside the manual system tracker or build datasets to render graphs.")
        
        # Inject sample simulation data button to satisfy testing requests safely
        if str_lt.button("Seed Simulation Track Progress Metrics Dataset"):
            sub_ref = db.query(Subject).first()
            if sub_ref:
                db.add_all([
                    StudySession(duration_minutes=90, date=date.today() - timedelta(days=2), subject_id=sub_ref.id),
                    StudySession(duration_minutes=120, date=date.today() - timedelta(days=1), subject_id=sub_ref.id),
                    StudySession(duration_minutes=150, date=date.today(), subject_id=sub_ref.id)
                ])
                db.commit()
                str_lt.rerun()
    else:
        df_sessions = pd.DataFrame([
            {"Duration": s.duration_minutes, "Date": s.date, "Subject": s.subject.name} for s in sessions_data
        ])
        
        graph_col1, graph_col2 = str_lt.columns(2)
        with graph_col1:
            str_lt.subheader("Productivity Track Over Time Window")
            fig_line = px.line(df_sessions, x="Date", y="Duration", color="Subject", title="Minutes Invested per Block Session")
            str_lt.plotly_chart(fig_line, use_container_width=True)
            
        with graph_col2:
            str_lt.subheader("Subject Distribution Allocation Weightings")
            fig_pie = px.pie(df_sessions, values="Duration", names="Subject", title="Relative Focus Footprint Allocation")
            str_lt.plotly_chart(fig_pie, use_container_width=True)
            
        str_lt.markdown("---")
        str_lt.subheader("AI Performance Diagnostics Matrix Report")
        if str_lt.button("Synthesize Executive Analytics Assessment Data Summary"):
            history_string = df_sessions.to_string()
            with str_lt.spinner("Processing optimization parameters..."):
                report_out = AIService.weekly_report(history_string)
                weak_out = AIService.suggest_weak_subjects(history_string)
            str_lt.success("System-Wide Analytical Report Generation Finalized.")
            str_lt.markdown(report_out)
            str_lt.warning(weak_out)


elif app_page == "Goals":
    str_lt.title("🏁 Strategic Performance Tracking Objectives")
    
    with str_lt.form("goal_add_form", clear_on_submit=True):
        g_desc = str_lt.text_input("Objective Vector Goal Statement Specification")
        g_target = str_lt.number_input("Target Numeric Metric Target Ceiling Value", min_value=1.0, value=100.0)
        if str_lt.form_submit_button("Lock Optimization Goal Target"):
            if g_desc.strip():
                db.add(Goal(description=g_desc.strip(), target_value=g_target, current_value=0.0, completed=False))
                db.commit()
                str_lt.success("Goal constraint profile safely tracked.")
                str_lt.rerun()
                
    str_lt.markdown("---")
    str_lt.subheader("Active Structural Goals Repository Pipelines")
    all_goals = db.query(Goal).all()
    if all_goals:
        for g in all_goals:
            str_lt.markdown(f"#### Target: {g.description}")
            progress_ratio = min((g.current_value / g.target_value), 1.0)
            str_lt.progress(progress_ratio)
            str_lt.write(f"System State Metrics: `{g.current_value}` completed / `{g.target_value}` ultimate baseline constraint target parameters.")
            
            up_col1, up_col2 = str_lt.columns(2)
            with up_col1:
                incr_val = str_lt.number_input("Increment step unit index progress metrics value", min_value=1.0, key=f"step_{g.id}")
                if str_lt.button("Log Step Work Value Vector Increments", key=f"btn_step_{g.id}"):
                    g.current_value += incr_val
                    if g.current_value >= g.target_value:
                        g.completed = True
                    db.commit()
                    str_lt.rerun()
            with up_col2:
                if str_lt.button("Terminate Strategy Objective Track Linkage Instance", key=f"del_g_{g.id}"):
                    db.delete(g)
                    db.commit()
                    str_lt.rerun()
            str_lt.markdown("---")
    else:
        str_lt.info("No long-range target profiles assigned.")


elif app_page == "Settings":
    str_lt.title("⚙️ System Core Operations & Configuration Parameters")
    
    str_lt.subheader("User Strategy Profile Management Parameters")
    current_name_state = str_lt.text_input("Modify Operational User Token Handle Identifier Name", value=user_profile.username)
    mod_streak = str_lt.number_input("Reset System Metric Study Streak Matrix Target Counter", value=user_profile.streak)
    
    if str_lt.button("Save Profile Adjustments"):
        user_profile.username = current_name_state
        user_profile.streak = mod_streak
        db.commit()
        str_lt.success("System context profiles updated successfully.")
        str_lt.rerun()
        
    str_lt.markdown("---")
    str_lt.subheader("System Data Extraction Procedures")
    
    if str_lt.button("Run System Data Integrity Backup Sync Sequence"):
        try:
            from database import DB_PATH
            with open(DB_PATH, "rb") as source_db_file:
                bytes_payload = source_db_file.read()
            str_lt.download_button(
                label="Download SQLite Binary Database Image Snapshot",
                data=bytes_payload,
                file_name="studygenie_production_backup.db",
                mime="application/octet-stream"
            )
            str_lt.success("Backup stream compiled successfully.")
        except Exception as system_io_error:
            str_lt.error(f"Execution Error compiling storage engine streams: {str(system_io_error)}")

db.close()
