# 🤖 Jarvis v6 – Autonomous Software Builder AI

> An advanced AI system that automatically builds complete software projects from a single natural-language instruction. Runs entirely locally using free, open-source tools.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-Agent Architecture** | 8 specialised agents that plan, design, code, test, and fix projects |
| **Dual AI Backend** | Ollama (recommended) or HuggingFace Transformers — your choice |
| **Automatic Code Generation** | Generates FastAPI backend + HTML/CSS/JS frontend + SQLite database |
| **Self-Healing** | Detects errors and iterates up to 3 times to fix them |
| **Screen Analysis** | Optional OCR-based error detection from screenshots |
| **Web Dashboard** | Premium Streamlit UI — dark theme, glassmorphism, live pipeline view |
| **CLI Mode** | Run from the terminal with `python main.py "your idea"` |
| **100% Local & Free** | No API keys, no cloud, no cost |

---

## 🔄 System Workflow

```
User enters idea
      │
      ▼
┌─────────────────┐
│  PlannerAgent    │  Break idea → development tasks
└────────┬────────┘
         ▼
┌─────────────────┐
│ ArchitectAgent   │  Design folder structure & components
└────────┬────────┘
         ▼
┌─────────────────┐
│ DatabaseAgent    │  Generate SQLAlchemy models
└────────┬────────┘
         ▼
┌─────────────────┐
│  BackendAgent    │  Generate FastAPI backend code
└────────┬────────┘
         ▼
┌─────────────────┐
│ FrontendAgent    │  Generate HTML / CSS / JS frontend
└────────┬────────┘
         ▼
┌─────────────────┐
│ ExecutionAgent   │  Create folders & write files to disk
└────────┬────────┘
         ▼
┌─────────────────┐
│  TestingAgent    │  Syntax check, import check, error scan
└────────┬────────┘
         ▼
┌─────────────────┐
│ImprovementAgent  │  Fix errors (up to 3 iterations)
└─────────────────┘
```

---

## 🏗️ Project Structure

```
jarvis-v6/
├── .env                     # Configuration
├── config.py                # Settings loader
├── main.py                  # CLI entry point
├── requirements.txt         # Dependencies
│
├── agents/                  # Multi-agent system
│   ├── base_agent.py        # Abstract base class
│   ├── planner_agent.py     # Task planning
│   ├── architect_agent.py   # Architecture design
│   ├── backend_agent.py     # FastAPI generation
│   ├── frontend_agent.py    # HTML/CSS/JS generation
│   ├── database_agent.py    # Database models
│   ├── execution_agent.py   # File system operations
│   ├── testing_agent.py     # Testing & error detection
│   └── improvement_agent.py # Error fixing
│
├── core/                    # Engine & orchestration
│   ├── ai_engine.py         # AI backend (Ollama / HF)
│   └── task_manager.py      # Pipeline orchestrator
│
├── vision/                  # Screen analysis
│   └── screen_reader.py     # Screenshot + OCR
│
├── ui/                      # Web dashboard
│   └── dashboard.py         # Streamlit UI
│
└── generated_projects/      # Output folder
```

---

## 📦 Prerequisites

- **Python 3.10+**
- **Ollama** (recommended AI backend) — [download](https://ollama.com)
- **Tesseract OCR** (optional, for screen analysis) — `winget install UB-Mannheim.TesseractOCR`

---

## 🚀 Installation (Step by Step)

### Step 1: Clone or navigate to the project

```bash
cd jarvis-v6
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the virtual environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Install Ollama and pull a model

```bash
# Download Ollama from https://ollama.com
# Then pull the coding model:
ollama pull qwen2.5-coder:7b
```

### Step 6: Configure (optional)

Edit `.env` to change settings:

```ini
AI_BACKEND=ollama
OLLAMA_MODEL=qwen2.5-coder:7b
MAX_TOKENS=2048
TEMPERATURE=0.2
```

---

## 🖥️ Usage

### Option A: Web Dashboard (Recommended)

```bash
streamlit run ui/dashboard.py
```

Then open **http://localhost:8501** in your browser.

### Option B: Command Line

```bash
python main.py "Build a task management web application with login and dashboard"
```

Or run interactively:

```bash
python main.py
# Then type your idea when prompted
```

---

## 💡 Example Commands

```
"Build a blog website"
"Create a Flask API for user authentication"
"Generate a React dashboard"
"Build a task management app with login and dashboard"
"Create a REST API for a bookstore with CRUD operations"
"Build a weather app that shows forecasts"
```

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_BACKEND` | `ollama` | AI backend: `ollama` or `huggingface` |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Ollama model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `HF_MODEL` | `microsoft/Phi-3-mini-4k-instruct` | HuggingFace model ID |
| `MAX_TOKENS` | `2048` | Max tokens per generation |
| `TEMPERATURE` | `0.2` | Sampling temperature (0 = deterministic) |
| `PROJECTS_DIR` | `generated_projects` | Output directory for projects |
| `TEST_TIMEOUT` | `30` | Timeout in seconds for test commands |
| `MAX_FIX_ITERATIONS` | `3` | Max error-fix iterations |

---

## 🤖 Agent Reference

| Agent | Role | Uses LLM? |
|-------|------|-----------|
| **PlannerAgent** | Breaks idea into dev tasks | ✅ |
| **ArchitectAgent** | Designs folder structure & APIs | ✅ |
| **DatabaseAgent** | Generates SQLAlchemy models | ✅ |
| **BackendAgent** | Generates FastAPI backend | ✅ |
| **FrontendAgent** | Generates HTML/CSS/JS frontend | ✅ |
| **ExecutionAgent** | Creates folders & writes files | ❌ |
| **TestingAgent** | Runs syntax/import checks | ❌ |
| **ImprovementAgent** | Feeds errors to LLM for fixes | ✅ |

---

## 🔧 Troubleshooting

### Ollama connection error
Make sure Ollama is running:
```bash
ollama serve
```

### Model not found
Pull the model first:
```bash
ollama pull qwen2.5-coder:7b
```

### HuggingFace out of memory
Use a smaller model or switch to Ollama:
```ini
AI_BACKEND=ollama
```

### Tesseract not found
Install Tesseract OCR:
```bash
winget install UB-Mannheim.TesseractOCR
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

> Built with ❤️ using Python, Streamlit, Ollama, and open-source AI.
