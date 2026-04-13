import streamlit as st
from orchestrator import Orchestrator

# --- Page Config & Styling ---
st.set_page_config(
    page_title="Agentic Trust Laboratory", layout="wide", page_icon="🧪"
)

# Custom CSS for Premium Look
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stCode { border-radius: 10px; }
    .agent-log { padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #58a6ff; background-color: #161b22; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- App Header ---
st.title("🧪 Agentic Trust Laboratory")
st.markdown("### Verifying AI-Generated Software Through Recursive Multi-Agent Loops")
st.divider()

# --- Inputs ---
with st.container():
    problem_input = st.text_area(
        "🚀 Enter a Coding Problem or DSA Question",
        height=100,
        placeholder="e.g., Implement an LRU Cache with O(1) time complexity.",
    )
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        run_button = st.button(
            "Generate & Verify Code", use_container_width=True, type="primary"
        )
    with col_btn2:
        max_retries = st.number_input("Max Retries", min_value=1, max_value=5, value=3)

# --- Initializing Session State ---
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None

# --- Pipeline Execution ---
if run_button and problem_input:
    with st.status("🧠 Agents are thinking...", expanded=True) as status:
        orchestrator = Orchestrator()

        # Run the pipeline
        results = orchestrator.run_pipeline(problem_input, max_retries=int(max_retries))
        st.session_state.pipeline_results = results

        # Show agent logs in real-time
        for log in results["logs"]:
            st.write(f"**[{log['timestamp']}] {log['agent']}:** {log['message']}")

        status.update(
            label="✅ Analysis Complete!", state="complete", expanded=False
        )

# --- Results Presentation ---
if st.session_state.pipeline_results:
    res = st.session_state.pipeline_results
    report = res["report"]
    metrics = res["objective_metrics"]

    # Calculate pass rate from REAL parsed data
    pass_rate = (report.passed_tests / report.total_tests) if report.total_tests > 0 else 0

    # 🏅 Trust Scorecard — Row 1: Core Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Trust Score", f"{report.trust_score}/100")
    with col2:
        st.metric("Trust Grade", report.trust_grade)
    with col3:
        st.metric("Time Complexity", report.time_complexity)
    with col4:
        st.metric("Space Complexity", report.space_complexity)

    # 🏅 Row 2: Objective Measurements
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Tests Passed", f"{report.passed_tests}/{report.total_tests}")
    with col6:
        st.metric("Pylint Score", f"{metrics['pylint_score']}/10")
    with col7:
        st.metric("Complexity Grade", metrics["complexity_grade"])
    with col8:
        st.metric("Iterations Used", res["iterations_used"])

    st.divider()

    # 💻 Code & Analysis Panel
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🧬 Generated Code", "🔬 Test Suite", "📊 Final Verdict", "📜 Agent Logs"]
    )

    with tab1:
        st.subheader("Implementation (Python)")
        st.code(res["code"], language="python")
        st.info(
            f"**Suggested Data Structures:** "
            f"{', '.join(res['spec'].suggested_data_structures)}"
        )

    with tab2:
        st.subheader("Adversarial Test Suite")
        st.code(res["test_script"], language="python")
        st.subheader("Raw Execution Output")
        st.text_area("Execution Logs", res["execution_output"], height=250)

    with tab3:
        st.subheader("Agent Evaluation Report")

        st.markdown(f"**Verdict:** {report.verdict}")
        defense_status = "🛡️ Secure" if pass_rate > 0.8 else "❌ Vulnerable"
        st.markdown(f"**Adversarial Defense Status:** {defense_status}")
        st.markdown(f"**Edge Case Resilience:** {report.edge_case_resilience}")
        st.markdown(f"**Reviewer Feedback:**\n{report.feedback}")

        st.write(
            f"**Core Tests Passed: {report.passed_tests}/{report.total_tests}**"
        )
        st.progress(pass_rate)

    with tab4:
        st.subheader("Full Agent Thought Stream")
        for log in res["logs"]:
            st.markdown(
                f"**`[{log['timestamp']}]` {log['agent']}:** {log['message']}"
            )

# --- Footer ---
st.divider()
st.markdown("Designed for **Internship Showcase** | Built with Agentic AI & Groq")
