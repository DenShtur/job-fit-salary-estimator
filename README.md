# Job Fit & Salary Estimator

AI-powered CV analysis: seniority score, Czech market salary range, and a personalized growth plan — all from a single PDF or DOCX upload.

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![Claude](https://img.shields.io/badge/Claude-claude--sonnet--4--5-purple)

---

## How it works

**Chain of Thought LLM pipeline** — 4 sequential steps, each building on the previous:

```
CV (PDF / DOCX)
    ↓
Step 1 — Extract facts       skills, experience, education, achievements
    ↓
Step 2 — Evaluate seniority  score 0–100, level, strengths, weaknesses
    ↓
Step 3 — Estimate salary     CZK range vs Czech IT market benchmarks
    ↓
Step 4 — Recommend growth    concrete actions to reach +30% salary
```

Progress streams live to the UI via **Server-Sent Events** — no waiting for a spinner.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit (dark theme, SSE streaming) |
| Backend | FastAPI |
| LLM | Claude API (`claude-sonnet-4-5`) |
| CV parsing | pdfplumber + python-docx |
| Validation | Pydantic v2 with structured output |
| Streaming | Server-Sent Events (SSE) |

---

## Quick start

**macOS / Linux:**
```bash
./run.sh
```

**Windows — use Docker:**
```bash
docker-compose up
```

Open in browser: **http://localhost:8501**
API docs: **http://localhost:8000/docs**

> **Anthropic API Key — two ways to provide it:**
> 1. **`.env` file** — copy `.env.example` → `.env` and set `ANTHROPIC_API_KEY=sk-ant-...`
> 2. **UI sidebar** — paste the key directly in the app, no file needed

---

## Docker

```bash
docker-compose up
```

Services:
- `api` → http://localhost:8000
- `ui`  → http://localhost:8501

---

## Run tests

```bash
./run.sh test
```

Or directly:

```bash
pytest tests/ -v
```

37 tests covering CV parsing, Pydantic models, salary data, and LLM JSON cleaning.

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Analyze CV, returns full `PipelineResult` |
| `POST` | `/analyze/stream` | SSE stream — progress events per step |
| `GET`  | `/health` | Service status + model name |
| `GET`  | `/salary-benchmarks` | Czech IT market salary data |

### Example response `/analyze`

```json
{
  "cv_facts": {
    "total_years_experience": 3.0,
    "tech_skills": [{"name": "Python", "years_experience": 3.0}],
    "education_level": "bachelor"
  },
  "seniority": {
    "level": "mid",
    "score": 55,
    "confidence": "medium",
    "strengths": ["Strong Python fundamentals"],
    "weaknesses": ["Limited cloud experience"]
  },
  "salary": {
    "estimated_range": {"min_czk": 55000, "median_czk": 70000, "max_czk": 90000},
    "fit_score": 72
  },
  "recommendations": {
    "target_salary_czk": 91000,
    "recommendations": [
      {
        "action": "Get AWS Solutions Architect certification",
        "impact": "high",
        "timeframe_months": 4,
        "expected_salary_increase_pct": 12.0
      }
    ]
  },
  "processing_time_seconds": 18.4
}
```

---

## Project structure

```
app/
├── main.py                      # FastAPI — /analyze, /analyze/stream, /health
├── models/pipeline_models.py    # Pydantic v2 models with validators
├── pipeline/
│   ├── cv_parser.py             # PDF/DOCX → plain text
│   ├── step1_extract.py         # LLM step 1: extract CV facts
│   ├── step2_seniority.py       # LLM step 2: seniority score 0–100
│   ├── step3_salary.py          # LLM step 3: salary estimate vs CZ market
│   ├── step4_recommendations.py # LLM step 4: growth plan
│   └── orchestrator.py          # Sequential pipeline runner
├── data/salary_data.py          # Czech IT market salary benchmarks
└── utils/
    ├── claude_client.py         # Claude API wrapper (retry, JSON extraction)
    └── logging_config.py        # Structured logging
frontend/
└── streamlit_app.py             # UI with SSE streaming progress
tests/                           # 37 pytest tests
.streamlit/config.toml           # Dark theme config
```
