"""
Jarvis v6 - Dashboard
======================
Premium Streamlit dashboard for the Autonomous Software Builder.
Supports full local mode (with Ollama) and cloud demo mode.
"""

from __future__ import annotations

import sys
import time
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so imports work when run via
# `streamlit run ui/dashboard.py` from the jarvis-v6 directory.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from config import config

# ===========================================================================
# Check cloud/local mode
# ===========================================================================
def _is_ollama_available() -> bool:
    """Check if Ollama server is reachable."""
    try:
        import requests
        resp = requests.get(f"{config.ollama_base_url}/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


CLOUD_MODE = not _is_ollama_available()

# Only import heavy modules if running locally
if not CLOUD_MODE:
    from core.ai_engine import AIEngine
    from core.task_manager import TaskManager, ProjectResult
    from agents.execution_agent import ExecutionAgent


# ===========================================================================
# Page configuration
# ===========================================================================
st.set_page_config(
    page_title="Jarvis v6 – AI Software Builder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===========================================================================
# Custom CSS – Premium dark theme
# ===========================================================================
st.markdown(
    """
<style>
/* ---------- Global ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit header & footer */
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

/* Background */
.stApp {
    background: linear-gradient(135deg, #0b0f19 0%, #131927 50%, #0b0f19 100%);
}

/* ---------- Header banner ---------- */
.hero-banner {
    background: linear-gradient(135deg, #1a1f35 0%, #0d1321 100%);
    border: 1px solid rgba(56, 189, 248, 0.15);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(56,189,248,0.06) 0%, transparent 60%);
    pointer-events: none;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.35rem 0;
}
.hero-sub {
    color: #94a3b8;
    font-size: 1rem;
    font-weight: 400;
}

/* ---------- Cards ---------- */
.info-card {
    background: rgba(30, 41, 59, 0.65);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(71, 85, 105, 0.35);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.3s ease, transform 0.2s ease;
}
.info-card:hover {
    border-color: rgba(56, 189, 248, 0.4);
    transform: translateY(-2px);
}
.card-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.35rem;
}
.card-value {
    font-size: 1.35rem;
    font-weight: 600;
    color: #e2e8f0;
}

/* ---------- Stat cards ---------- */
.stat-card {
    background: rgba(30, 41, 59, 0.65);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(71, 85, 105, 0.35);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
}
.stat-card:hover {
    border-color: rgba(56, 189, 248, 0.4);
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}
.stat-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}
.stat-number {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-label {
    font-size: 0.8rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.25rem;
}

/* ---------- Step badges ---------- */
.step-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.55rem 1rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
    width: 100%;
    transition: all 0.2s ease;
}
.step-badge:hover {
    transform: translateX(4px);
}
.step-success { background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.step-warning { background: rgba(250,204,21,0.12); color: #facc15; border: 1px solid rgba(250,204,21,0.2); }
.step-error   { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.2); }
.step-pending { background: rgba(100,116,139,0.12); color: #94a3b8; border: 1px solid rgba(100,116,139,0.2); }
.step-active  { background: rgba(56,189,248,0.12);  color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); }

/* ---------- Agent card ---------- */
.agent-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
    border: 1px solid rgba(71, 85, 105, 0.35);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.agent-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    border-radius: 4px 0 0 4px;
}
.agent-card:hover {
    border-color: rgba(56, 189, 248, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}
.agent-card.planner::before { background: linear-gradient(180deg, #38bdf8, #0ea5e9); }
.agent-card.architect::before { background: linear-gradient(180deg, #818cf8, #6366f1); }
.agent-card.database::before { background: linear-gradient(180deg, #34d399, #10b981); }
.agent-card.backend::before { background: linear-gradient(180deg, #fb923c, #f97316); }
.agent-card.frontend::before { background: linear-gradient(180deg, #f472b6, #ec4899); }
.agent-card.execution::before { background: linear-gradient(180deg, #a78bfa, #8b5cf6); }
.agent-card.testing::before { background: linear-gradient(180deg, #facc15, #eab308); }
.agent-card.improvement::before { background: linear-gradient(180deg, #4ade80, #22c55e); }
.agent-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.35rem;
}
.agent-desc {
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.5;
}

/* ---------- Code block ---------- */
.code-block {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 1rem;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.82rem;
    overflow-x: auto;
    color: #e2e8f0;
}

/* ---------- Feature pill ---------- */
.feature-pill {
    display: inline-block;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 20px;
    padding: 0.4rem 1rem;
    margin: 0.25rem;
    font-size: 0.8rem;
    color: #38bdf8;
    font-weight: 500;
    transition: all 0.2s ease;
}
.feature-pill:hover {
    background: rgba(56, 189, 248, 0.2);
    transform: scale(1.05);
}

/* ---------- Pipeline flow ---------- */
.pipeline-flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.25rem;
    padding: 1.5rem 0;
    flex-wrap: wrap;
}
.pipeline-node {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(71, 85, 105, 0.4);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    font-size: 0.78rem;
    color: #e2e8f0;
    font-weight: 500;
    text-align: center;
    min-width: 90px;
    transition: all 0.3s ease;
}
.pipeline-node:hover {
    border-color: rgba(56, 189, 248, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);
}
.pipeline-arrow {
    color: #475569;
    font-size: 1.2rem;
}

/* ---------- Demo banner ---------- */
.demo-banner {
    background: linear-gradient(135deg, rgba(251, 146, 60, 0.12), rgba(249, 115, 22, 0.08));
    border: 1px solid rgba(251, 146, 60, 0.25);
    border-radius: 10px;
    padding: 0.75rem 1.25rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.demo-banner-icon { font-size: 1.2rem; }
.demo-banner-text {
    font-size: 0.85rem;
    color: #fb923c;
    font-weight: 500;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
    border-right: 1px solid rgba(56, 189, 248, 0.1);
}

/* ---------- Button ---------- */
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(37, 99, 235, 0.45) !important;
}

/* ---------- Text area ---------- */
.stTextArea textarea {
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(71, 85, 105, 0.4) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus {
    border-color: rgba(56, 189, 248, 0.6) !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.15) !important;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(30, 41, 59, 0.5);
    border-radius: 8px;
    color: #94a3b8;
    padding: 0.5rem 1rem;
    border: 1px solid transparent;
}
.stTabs [aria-selected="true"] {
    background: rgba(56, 189, 248, 0.12) !important;
    color: #38bdf8 !important;
    border-color: rgba(56, 189, 248, 0.3) !important;
}

/* ---------- Animations ---------- */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}
.animate-in {
    animation: fadeInUp 0.5s ease-out;
}
.pulse {
    animation: pulse 2s infinite;
}
</style>
""",
    unsafe_allow_html=True,
)


# ===========================================================================
# Session state
# ===========================================================================
def _init_state():
    defaults = {
        "building": False,
        "result": None,
        "progress_steps": [],
        "current_step": "",
        "logs": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ===========================================================================
# Progress callback (used by TaskManager in local mode)
# ===========================================================================
def progress_callback(agent: str, message: str, step: int, total: int):
    """Called by TaskManager on each pipeline step."""
    st.session_state["current_step"] = f"{agent}: {message}"
    st.session_state["progress_steps"].append(
        {"agent": agent, "message": message, "step": step, "total": total}
    )


# ===========================================================================
# Hero Banner
# ===========================================================================
st.markdown(
    """
<div class="hero-banner animate-in">
    <div class="hero-title">🤖 Jarvis v6</div>
    <div class="hero-sub">Autonomous Software Builder &mdash; Local &bull; Free &bull; Open Source</div>
</div>
""",
    unsafe_allow_html=True,
)

# ===========================================================================
# Sidebar – Configuration
# ===========================================================================
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    mode_label = "☁️ CLOUD DEMO" if CLOUD_MODE else "🟢 LOCAL"
    mode_color = "#fb923c" if CLOUD_MODE else "#4ade80"
    st.markdown(
        f"""
<div class="info-card">
    <div class="card-label">Mode</div>
    <div class="card-value" style="color:{mode_color}; font-size:1.1rem;">{mode_label}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="info-card">
    <div class="card-label">AI Backend</div>
    <div class="card-value">{config.ai_backend.upper()}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    model_name = (
        config.ollama_model if config.ai_backend == "ollama" else config.hf_model
    )
    st.markdown(
        f"""
<div class="info-card">
    <div class="card-label">Model</div>
    <div class="card-value" style="font-size:1rem;">{model_name}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="info-card">
    <div class="card-label">Max Tokens</div>
    <div class="card-value">{config.max_tokens}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="info-card">
    <div class="card-label">Temperature</div>
    <div class="card-value">{config.temperature}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    if CLOUD_MODE:
        st.markdown("### 🚀 Run Locally")
        st.code(
            "git clone <repo-url>\ncd jarvis-v6\npip install -r requirements-local.txt\nstreamlit run ui/dashboard.py",
            language="bash",
        )
    else:
        st.markdown("### 📂 Output Directory")
        st.code(str(config.projects_path), language=None)

    st.markdown("---")
    st.markdown(
        """
<div style="text-align:center; color:#475569; font-size:0.75rem; margin-top:1rem;">
    Jarvis v6 &copy; 2026<br/>
    Powered by Open-Source AI
</div>
""",
        unsafe_allow_html=True,
    )


# ===========================================================================
# CLOUD DEMO MODE
# ===========================================================================
if CLOUD_MODE:
    st.markdown(
        """
<div class="demo-banner animate-in">
    <span class="demo-banner-icon">☁️</span>
    <span class="demo-banner-text">
        Cloud Demo Mode &mdash; Ollama not detected. Showing interactive showcase.
        Clone the repo and run locally for full functionality.
    </span>
</div>
""",
        unsafe_allow_html=True,
    )

    # ---- Stats Row ----
    c1, c2, c3, c4 = st.columns(4)
    stats = [
        ("🧠", "8", "AI Agents"),
        ("⚡", "100%", "Local & Free"),
        ("🔄", "Auto", "Fix Loop"),
        ("📁", "Full Stack", "Generation"),
    ]
    for col, (icon, number, label) in zip([c1, c2, c3, c4], stats):
        with col:
            st.markdown(
                f"""
<div class="stat-card animate-in">
    <div class="stat-icon">{icon}</div>
    <div class="stat-number">{number}</div>
    <div class="stat-label">{label}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown("")

    # ---- Pipeline Visualization ----
    st.markdown("### 🔄 Multi-Agent Pipeline")
    st.markdown(
        """
<div class="pipeline-flow animate-in">
    <div class="pipeline-node">💡 Idea</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">📋 Planner</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">🏗️ Architect</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">🗄️ Database</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">⚙️ Backend</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">🎨 Frontend</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">📁 Files</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">🧪 Test</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">🔧 Fix</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-node">✅ Done!</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ---- Tabs ----
    tab_demo, tab_agents, tab_arch, tab_code = st.tabs(
        ["🚀 Live Demo", "🤖 Agents", "🏗️ Architecture", "💻 Sample Output"]
    )

    # --- Tab: Live Demo ---
    with tab_demo:
        st.markdown("#### 💡 Try a simulated build")

        # Apply pending example value BEFORE the widget
        if "_pending_idea_demo" in st.session_state:
            st.session_state["demo_idea_input"] = st.session_state.pop("_pending_idea_demo")

        col_input, col_examples = st.columns([3, 1])

        with col_input:
            demo_idea = st.text_area(
                "**Describe your software idea**",
                placeholder="e.g.  Build a task management web application with login and dashboard",
                height=100,
                key="demo_idea_input",
            )

        with col_examples:
            st.markdown("**Quick Examples**")
            examples = [
                "Build a blog website",
                "Create a Flask REST API",
                "Generate a React dashboard",
                "Build a task manager app",
            ]
            for ex in examples:
                if st.button(ex, key=f"demo_ex_{hash(ex)}", use_container_width=True):
                    st.session_state["_pending_idea_demo"] = ex
                    st.rerun()

        demo_clicked = st.button("🚀  Simulate Build", use_container_width=True)

        if demo_clicked and demo_idea and demo_idea.strip():
            project_slug = demo_idea.strip().lower().replace(" ", "-")[:30]

            with st.status("🔨 Simulating build pipeline…", expanded=True) as status:
                steps_data = [
                    ("PlannerAgent", "Analyzing requirements…", 0.8),
                    ("ArchitectAgent", "Designing architecture…", 0.6),
                    ("DatabaseAgent", "Creating database schema…", 0.5),
                    ("BackendAgent", "Generating backend APIs…", 1.0),
                    ("FrontendAgent", "Generating frontend UI…", 0.9),
                    ("ExecutionAgent", "Writing files to disk…", 0.4),
                    ("TestingAgent", "Running syntax checks…", 0.5),
                    ("ImprovementLoop", "No fixes needed", 0.2),
                ]

                for agent, msg, delay in steps_data:
                    st.write(f"🔄 **{agent}**: {msg}")
                    time.sleep(delay)

                status.update(label="✅ Simulation complete!", state="complete")

            # Show simulated results
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    """<div class="info-card">
                    <div class="card-label">Status</div>
                    <div class="card-value">✅ Success</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"""<div class="info-card">
                    <div class="card-label">Project</div>
                    <div class="card-value" style="font-size:1rem;">{project_slug}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    """<div class="info-card">
                    <div class="card-label">Files Created</div>
                    <div class="card-value">12</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    """<div class="info-card">
                    <div class="card-label">Build Time</div>
                    <div class="card-value">4.9s</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            # Simulated pipeline steps
            st.markdown("### 🔄 Pipeline Steps")
            for agent, msg, delay in steps_data:
                st.markdown(
                    f"""<div class="step-badge step-success">
                    ✅ <strong>{agent}</strong> &mdash; {msg}
                    <span style="margin-left:auto; opacity:0.6;">{delay:.1f}s</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

            # Simulated project tree
            st.markdown("---")
            st.markdown("### 📁 Generated Project Structure")
            st.code(
                f"""{project_slug}/
├── app.py
├── requirements.txt
├── config.py
├── models/
│   ├── __init__.py
│   └── user.py
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   └── main.py
├── templates/
│   ├── base.html
│   ├── index.html
│   └── dashboard.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js""",
                language=None,
            )

        elif demo_clicked:
            st.warning("Please enter a software idea first.")

    # --- Tab: Agents ---
    with tab_agents:
        st.markdown("#### 🤖 Meet the Agent Squad")
        st.markdown("")

        agents = [
            ("planner", "📋 PlannerAgent", "Breaks down the user's idea into a structured project plan with name, description, features, tech stack, and file list."),
            ("architect", "🏗️ ArchitectAgent", "Designs the software architecture — folder structure, design patterns, data flow, and module relationships."),
            ("database", "🗄️ DatabaseAgent", "Generates database schemas, models, and migration files based on the project requirements."),
            ("backend", "⚙️ BackendAgent", "Creates backend code — routes, controllers, business logic, API endpoints, and server configuration."),
            ("frontend", "🎨 FrontendAgent", "Generates frontend UI — HTML templates, CSS styles, JavaScript interactions, and responsive layouts."),
            ("execution", "📁 ExecutionAgent", "Writes all generated files to disk, creates directories, and manages the file system operations."),
            ("testing", "🧪 TestingAgent", "Runs syntax checks, import validation, and basic tests on the generated code to find errors."),
            ("improvement", "🔧 ImprovementAgent", "Takes test errors, sends them to the LLM for fixes, and iterates up to N times until all tests pass."),
        ]

        col1, col2 = st.columns(2)
        for i, (css_class, name, desc) in enumerate(agents):
            with col1 if i % 2 == 0 else col2:
                st.markdown(
                    f"""
<div class="agent-card {css_class} animate-in">
    <div class="agent-name">{name}</div>
    <div class="agent-desc">{desc}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

    # --- Tab: Architecture ---
    with tab_arch:
        st.markdown("#### 🏗️ System Architecture")
        st.markdown("")

        st.markdown(
            """
<div class="info-card animate-in">
    <div class="card-label">Core Pipeline</div>
    <div style="color:#e2e8f0; font-size:0.9rem; line-height:1.8;">
        <strong>User Idea</strong> → <strong>PlannerAgent</strong> breaks it down →
        <strong>ArchitectAgent</strong> designs structure →
        <strong>DatabaseAgent</strong> creates schemas →
        <strong>BackendAgent</strong> writes server code →
        <strong>FrontendAgent</strong> builds UI →
        <strong>ExecutionAgent</strong> saves files →
        <strong>TestingAgent</strong> validates →
        <strong>ImprovementAgent</strong> fixes any errors → <strong>✅ Done!</strong>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("#### 🔧 Tech Stack")
        features = [
            "Python 3.10+",
            "Streamlit",
            "Ollama (Local LLM)",
            "HuggingFace Transformers",
            "Multi-Agent Pipeline",
            "Auto Fix Loop",
            "Syntax Validation",
            "File System Ops",
            "Screen Analysis (Vision)",
            "100% Free & Local",
        ]
        pills_html = "".join(
            f'<span class="feature-pill">{f}</span>' for f in features
        )
        st.markdown(
            f'<div style="margin:1rem 0;">{pills_html}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("#### 📂 Project Structure")
        st.code(
            """jarvis-v6/
├── main.py                 # CLI entry point
├── config.py               # Central configuration
├── requirements.txt        # Cloud dependencies
├── requirements-local.txt  # Full local dependencies
│
├── ui/
│   └── dashboard.py        # Streamlit dashboard
│
├── core/
│   ├── ai_engine.py        # LLM backend (Ollama/HuggingFace)
│   └── task_manager.py     # Pipeline orchestrator
│
├── agents/
│   ├── base_agent.py       # Abstract base class
│   ├── planner_agent.py    # Project planning
│   ├── architect_agent.py  # Architecture design
│   ├── database_agent.py   # DB schema generation
│   ├── backend_agent.py    # Backend code generation
│   ├── frontend_agent.py   # Frontend UI generation
│   ├── execution_agent.py  # File system operations
│   ├── testing_agent.py    # Test runner
│   └── improvement_agent.py# Error fixer
│
├── vision/
│   └── screen_reader.py    # Screen capture & OCR
│
└── generated_projects/     # Output folder""",
            language=None,
        )

    # --- Tab: Sample Output ---
    with tab_code:
        st.markdown("#### 💻 Sample Generated Code")
        st.markdown("Here's an example of what Jarvis v6 generates for a Flask API:")

        sample_files = {
            "app.py": '''"""Flask Application - Generated by Jarvis v6"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from models.user import User, db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SECRET_KEY"] = "jarvis-generated-secret"

CORS(app)
db.init_app(app)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})

@app.route("/api/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json()
    user = User(name=data["name"], email=data["email"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
''',
            "models/user.py": '''"""User Model - Generated by Jarvis v6"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }
''',
            "templates/index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My App - Generated by Jarvis v6</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <header class="navbar">
        <h1>🚀 My Application</h1>
        <nav>
            <a href="/">Home</a>
            <a href="/dashboard">Dashboard</a>
        </nav>
    </header>
    <main class="container">
        <h2>Welcome to your app!</h2>
        <p>This project was autonomously built by Jarvis v6.</p>
    </main>
    <script src="/static/js/app.js"></script>
</body>
</html>
''',
        }

        selected_file = st.selectbox(
            "Select file to preview",
            list(sample_files.keys()),
        )

        lang_map = {".py": "python", ".html": "html", ".css": "css", ".js": "javascript"}
        ext = "." + selected_file.rsplit(".", 1)[-1]
        st.code(sample_files[selected_file], language=lang_map.get(ext, None))


# ===========================================================================
# LOCAL MODE (Full Functionality)
# ===========================================================================
else:
    # ---- Main area – Input ----

    # Apply pending example value BEFORE the widget
    if "_pending_idea" in st.session_state:
        st.session_state["idea_input"] = st.session_state.pop("_pending_idea")

    col_input, col_examples = st.columns([3, 1])

    with col_input:
        user_idea = st.text_area(
            "💡 **Describe your software idea**",
            placeholder="e.g.  Build a task management web application with login and dashboard",
            height=120,
            key="idea_input",
        )

    with col_examples:
        st.markdown("**Quick Examples**")
        examples = [
            "Build a blog website",
            "Create a Flask API for user authentication",
            "Generate a React dashboard",
            "Build a task management app with login",
            "Create a REST API for a bookstore",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{hash(ex)}", use_container_width=True):
                st.session_state["_pending_idea"] = ex
                st.rerun()

    # Build button
    build_clicked = st.button(
        "🚀  Build Project",
        use_container_width=True,
        disabled=st.session_state["building"],
    )

    # ---- Build logic ----
    if build_clicked and user_idea and user_idea.strip():
        st.session_state["building"] = True
        st.session_state["result"] = None
        st.session_state["progress_steps"] = []
        st.session_state["logs"] = []

        with st.status("🔨 Building your project…", expanded=True) as status:
            try:
                ai_engine = AIEngine(config)
                manager = TaskManager(
                    config,
                    ai_engine=ai_engine,
                    on_progress=progress_callback,
                )

                st.write("🧠 Initialising agents…")
                time.sleep(0.3)

                result: ProjectResult = manager.build_project(user_idea.strip())

                st.session_state["result"] = result
                if result.success:
                    status.update(label="✅ Project built successfully!", state="complete")
                else:
                    status.update(label="⚠️ Project built with warnings", state="complete")

            except Exception as exc:
                status.update(label=f"❌ Build failed: {exc}", state="error")

            finally:
                st.session_state["building"] = False

    elif build_clicked:
        st.warning("Please enter a software idea first.")

    # ---- Results display ----
    result: ProjectResult | None = st.session_state.get("result")

    if result is not None:
        st.markdown("---")

        # Summary cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            status_icon = "✅" if result.success else "⚠️"
            st.markdown(
                f"""<div class="info-card">
                <div class="card-label">Status</div>
                <div class="card-value">{status_icon} {'Success' if result.success else 'Warnings'}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""<div class="info-card">
                <div class="card-label">Project</div>
                <div class="card-value">{result.project_name}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""<div class="info-card">
                <div class="card-label">Files Created</div>
                <div class="card-value">{result.files_created}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"""<div class="info-card">
                <div class="card-label">Build Time</div>
                <div class="card-value">{result.total_time:.1f}s</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Pipeline steps
        st.markdown("### 🔄 Pipeline Steps")
        for step in result.steps:
            icon_map = {"success": "✅", "warning": "⚠️", "error": "❌"}
            css_class = f"step-{step.status}"
            icon = icon_map.get(step.status, "⏳")
            st.markdown(
                f"""<div class="step-badge {css_class}">
                {icon} <strong>{step.agent_name}</strong> &mdash; {step.message}
                <span style="margin-left:auto; opacity:0.6;">{step.elapsed:.1f}s</span>
                </div>""",
                unsafe_allow_html=True,
            )

        # Tabs
        st.markdown("---")
        tab_tree, tab_code, tab_errors = st.tabs(
            ["📁 Project Structure", "💻 Generated Code", "🐛 Errors"]
        )

        project_path = Path(result.project_path) if result.project_path else None

        with tab_tree:
            if project_path and project_path.exists():
                tree = ExecutionAgent.get_project_tree(project_path)
                st.markdown(f"**{result.project_name}/**")
                st.code(tree, language=None)
                st.markdown(f"📂 **Path:** `{project_path}`")
            else:
                st.info("No project files found.")

        with tab_code:
            if project_path and project_path.exists():
                files = sorted(project_path.rglob("*"))
                code_files = [
                    f
                    for f in files
                    if f.is_file()
                    and f.suffix in (".py", ".html", ".css", ".js", ".txt", ".md", ".json")
                ]

                if code_files:
                    selected = st.selectbox(
                        "Select file to view",
                        code_files,
                        format_func=lambda f: str(f.relative_to(project_path)),
                    )
                    if selected:
                        content = selected.read_text(encoding="utf-8", errors="replace")
                        lang_map = {
                            ".py": "python",
                            ".html": "html",
                            ".css": "css",
                            ".js": "javascript",
                            ".json": "json",
                            ".md": "markdown",
                            ".txt": None,
                        }
                        lang = lang_map.get(selected.suffix, None)
                        st.code(content, language=lang)
                else:
                    st.info("No code files found.")
            else:
                st.info("Build a project first to see the code.")

        with tab_errors:
            if result.errors:
                for err in result.errors:
                    st.error(err)
            else:
                st.success("🎉 No errors detected!")
