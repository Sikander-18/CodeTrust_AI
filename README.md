# 🧪 Agentic Trust Laboratory

> **A production-ready multi-agent AI system that generates, adversarially tests, and verifies Python code for correctness, reliability, and trust.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-orange)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🔍 What It Does

The Agentic Trust Laboratory takes a natural-language DSA problem description and runs it through a **self-healing multi-agent pipeline** that:

1. **Architect** — Analyzes the problem → produces a strict `TechnicalSpec` (entry point, constraints, edge cases)
2. **Developer** — Implements a validated Python solution matching the spec
3. **Test Engineer** — Generates adversarial unit tests (stress tests, pattern-breakers, invariant checks)
4. **Sandbox** — Executes code + tests in an isolated subprocess; runs `pylint` + `radon` for static analysis
5. **Evaluator** — Scores the solution on a 0–100 **Trust Scale** (`A–F` grade) grounded in real test results
6. **Orchestrator** — Feeds failure details back to the Architect and loops until APPROVED or max retries

All steps stream to the browser in **real time** via Server-Sent Events (SSE).

---

## 🏗️ Project Structure

```
Ai-code-validator/
├── backend/                    # Python backend — all server logic
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── architect.py        # TechnicalSpec generation
│   │   ├── developer.py        # Code implementation
│   │   ├── test_engineer.py    # Adversarial test generation
│   │   └── evaluator.py        # Trust score evaluation
│   ├── main.py                 # FastAPI app + SSE endpoint
│   ├── orchestrator.py         # Pipeline logic + streaming generator
│   ├── sandbox.py              # Isolated subprocess execution
│   ├── llm_client.py           # Groq API wrapper with retries
│   ├── utils.py                # Shared JSON extractor
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variable template
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── hooks/
│   │   │   └── usePipeline.js  # SSE consumer hook
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── InputPanel.jsx
│   │   │   ├── CodePanel.jsx
│   │   │   ├── MetricsPanel.jsx
│   │   │   └── TabsSection.jsx
│   │   ├── App.jsx
│   │   ├── App.module.css
│   │   ├── index.css           # Stitch Sentinel Core design tokens
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js          # Proxy: /api → localhost:8000
│   └── package.json
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- A free [Groq API key](https://console.groq.com)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/Ai-code-validator.git
cd Ai-code-validator
```

Copy the environment template and add your key:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set GROQ_API_KEY=gsk_...
```

### 2. Install backend dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd ../frontend
npm install
```

### 4. Run (two terminals)

**Terminal 1 — Backend:**
```bash
# From project root
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# Open http://localhost:5173
```

---

## 🤖 Agent Architecture

```
Problem Input
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                         │
│  ┌───────────┐   ┌───────────┐   ┌──────────────────┐   │
│  │ Architect │──▶│ Developer │──▶│  Test Engineer   │   │
│  └───────────┘   └───────────┘   └──────────────────┘   │
│        │                 │               │               │
│        │         ┌───────┴───────┐       │               │
│        │         │    Sandbox    │◀──────┘               │
│        │         │ (subprocess)  │                       │
│        │         └───────┬───────┘                       │
│        │                 │ metrics                       │
│        │         ┌───────▼───────┐                       │
│        │         │   Evaluator   │                       │
│        │         └───────┬───────┘                       │
│        │                 │ NEEDS_REFINEMENT               │
│        └─────────────────┘ (feedback loop)               │
│                           │ APPROVED / max retries       │
└───────────────────────────┼──────────────────────────────┘
                            ▼
                     Final Result (SSE stream)
```

---

## 📊 Trust Score Scale

| Grade | Score | Meaning |
|:-----:|:-----:|:--------|
| **A** | 90–100 | Optimal — passes all adversarial stress tests |
| **B** | 80–89  | Correct — passes standard, minor stress issues |
| **C** | 70–79  | Correct but inefficient or memory-growth risk |
| **D** | 50–69  | Fails adversarial tests, passes basic logic |
| **F** | < 50   | Major logic failures |

---

## 🌊 SSE Event Schema

The `/api/generate` endpoint streams newline-delimited JSON events:

| Type | Fields | Description |
|:-----|:-------|:------------|
| `log` | `agent`, `message`, `timestamp` | Agent thought-stream |
| `progress` | `iteration`, `max_retries`, `step` | Pipeline step indicator |
| `code` | `content` | Generated Python implementation |
| `tests` | `content` | Generated adversarial test suite |
| `execution` | `stdout`, `stderr` | Raw sandbox output |
| `metrics` | `data` | Ground-truth test + static analysis numbers |
| `report` | `data` | Full `EvaluationReport` object |
| `done` | `result` | Final packaged result |
| `error` | `message` | Non-fatal pipeline error |

---

## 🛠️ Key Design Decisions

- **No hallucinated metrics** — `passed_tests` and `total_tests` are always overridden with ground-truth values from `parse_test_results()`; the LLM cannot fabricate scores
- **Robust JSON parsing** — `extract_json_from_text()` uses 4-strategy cascade (raw → strip fences → brace-depth matching → regex) shared across all agents
- **Entry-point enforcement** — Developer and Test Engineer always receive the explicit `entry_point` from the spec in their prompts; generated code is validated via `compile()` before use
- **Self-healing loop** — Only the specific failure lines from stderr are fed back, not the whole output, keeping the context focused
- **Streaming-first** — `run_pipeline_stream()` is a Python generator; FastAPI wraps it in an SSE response with no buffering

---

## 📦 Tech Stack

| Layer | Technology |
|:------|:----------|
| LLM | Groq — `llama-3.3-70b-versatile` |
| Backend | FastAPI + Uvicorn |
| Agent framework | Custom Python (no LangChain) |
| Static analysis | pylint + radon |
| Frontend | React 18 + Vite |
| UI design tokens | Stitch MCP — Sentinel Core |
| Code highlighting | react-syntax-highlighter (vscDarkPlus) |

---

## 📝 License

MIT © 2025 — see [LICENSE](LICENSE)
