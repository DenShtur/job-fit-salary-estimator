# Job Fit & Salary Estimator — Project Plan

## Context
Тестовое задание для получения работы. Нужно показать умение строить AI pipeline, работать модульно, использовать git-ветки профессионально и творчески подходить к задаче.

**Подход:** Chain of Thought LLM pipeline — каждый из 4 шагов получает результат предыдущего. Элегантно, прозрачно, легко объяснить.

**Ключевые решения:**
- API Key: `.env` файл + поле ввода в Streamlit sidebar (оба варианта)
- MCP Server: не делаем, не усложняем
- Git веток: 6-7 feature веток + main + develop

---

## Стек

| Слой | Технология |
|------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| LLM | Claude API (claude-3-5-sonnet-20241022) |
| CV парсинг | pdfplumber + python-docx |
| Валидация | Pydantic v2 |
| HTTP клиент | httpx |

---

## Структура проекта

```
 Job Fit Salary Estimator/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── specs/
│   └── plan.md                        # этот файл
│
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI entrypoint
│   ├── models/
│   │   ├── __init__.py
│   │   └── pipeline_models.py         # Все Pydantic модели
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── cv_parser.py               # PDF/DOCX → text
│   │   ├── step1_extract.py           # LLM: text → CVFacts
│   │   ├── step2_seniority.py         # LLM: CVFacts → SeniorityEvaluation
│   │   ├── step3_salary.py            # LLM: SeniorityEval → SalaryEstimate
│   │   ├── step4_recommendations.py   # LLM: SalaryEstimate → GrowthRecommendations
│   │   └── orchestrator.py            # Запускает все 4 шага последовательно
│   ├── data/
│   │   └── salary_data.py             # Синтетические данные CZ рынка
│   └── utils/
│       ├── __init__.py
│       ├── claude_client.py           # Anthropic SDK wrapper
│       └── logging_config.py          # Structured logging
│
└── frontend/
    └── streamlit_app.py               # Single-file Streamlit UI
```

---

## Chain of Thought Pipeline

```
CV (PDF/DOCX)
    ↓ cv_parser.py
    ↓ step1_extract    → CVFacts
    ↓ step2_seniority  → SeniorityEvaluation (score 0-100 + reasoning)
    ↓ step3_salary     → SalaryEstimate (range CZK + market benchmark)
    ↓ step4_recommend  → GrowthRecommendations (план +30%)
    ↓
FastAPI → Streamlit UI
```

---

## Pydantic модели (pipeline_models.py)

```python
class CVFacts(BaseModel):
    full_name: str | None
    total_years_experience: float
    tech_skills: list[TechSkill]       # name + years_experience
    soft_skills: list[str]
    education_level: Literal[...]
    industries: list[str]
    notable_achievements: list[str]

class SeniorityEvaluation(BaseModel):
    level: Literal["intern","junior","mid","senior","lead","principal"]
    score: int                         # 0-100
    reasoning: str
    strengths: list[str]
    weaknesses: list[str]
    cv_facts: CVFacts

class SalaryEstimate(BaseModel):
    estimated_range: SalaryRange       # min/median/max CZK
    market_range_for_level: SalaryRange
    fit_score: int
    salary_reasoning: str
    top_skills_driving_salary: list[str]
    seniority_eval: SeniorityEvaluation

class GrowthRecommendations(BaseModel):
    target_salary_czk: int             # median + 30%
    recommendations: list[Recommendation]  # action, impact, timeframe, % increase
    narrative: str
    salary_estimate: SalaryEstimate

class PipelineResult(BaseModel):      # финальный ответ API
    cv_facts: CVFacts
    seniority: SeniorityEvaluation
    salary: SalaryEstimate
    recommendations: GrowthRecommendations
    processing_time_seconds: float
```

---

## Данные CZ рынка (salary_data.py)

```python
CZ_SALARY_RANGES = {
    "intern":    {"min": 18_000, "median": 22_000, "max": 28_000},
    "junior":    {"min": 30_000, "median": 42_000, "max": 55_000},
    "mid":       {"min": 55_000, "median": 70_000, "max": 90_000},
    "senior":    {"min": 85_000, "median": 105_000, "max": 135_000},
    "lead":      {"min": 110_000, "median": 130_000, "max": 165_000},
    "principal": {"min": 140_000, "median": 165_000, "max": 200_000},
}
SKILL_MULTIPLIERS = {
    "machine_learning": 1.15, "cloud_aws": 1.12,
    "kubernetes": 1.08, "python": 1.05, "php": 0.92, ...
}
DOMAIN_MULTIPLIERS = {
    "fintech": 1.18, "saas": 1.10, "consulting": 0.95, ...
}
```

---

## FastAPI эндпоинты (main.py)

- `POST /analyze` — принимает PDF/DOCX, запускает pipeline, возвращает `PipelineResult`
- `GET /health` — статус сервиса + версия модели
- `GET /salary-benchmarks` — синтетические данные CZ рынка

CORS включён для `localhost:8501`.

---

## Streamlit UI (streamlit_app.py)

**Sidebar:**
- Поле ввода ANTHROPIC_API_KEY (если не задан в .env)
- Индикатор health check (зелёный/красный)

**Фаза 1 — Upload:**
- Загрузка файла (PDF/DOCX)
- Кнопка "Analyze"
- Progress bar с подписями шагов CoT

**Фаза 2 — Results (4 вкладки):**
- Tab 1: CV Summary — скиллы тэгами, опыт, образование
- Tab 2: Seniority — score gauge, сильные/слабые стороны, reasoning
- Tab 3: Salary — бар-чарт "Ты vs Рынок", топ-скиллы
- Tab 4: Recommendations — карточки с action/impact/timeframe + narrative

---

## Git стратегия

```
main                              ← стабильный релиз
└── develop                       ← интеграционная ветка
    ├── chore/project-scaffold    ← фаза 1: структура + requirements
    ├── feature/salary-data       ← фаза 2: CZ рыночные данные
    ├── feature/pydantic-models   ← фаза 2: все Pydantic модели
    ├── feature/cv-parser         ← фаза 3: PDF/DOCX extraction
    ├── feature/pipeline-steps    ← фаза 4: 4 CoT шага + orchestrator
    ├── feature/fastapi-api       ← фаза 5: FastAPI endpoints
    └── feature/streamlit-ui      ← фаза 6: Streamlit frontend
```

Каждая ветка → PR → develop → финальный PR → main.

---

## Фазы реализации

### Фаза 1: Scaffold (`chore/project-scaffold`)
- Создать структуру папок
- `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
- Merge → develop → main (первый релиз)

### Фаза 2: Data & Models (`feature/salary-data` + `feature/pydantic-models`)
- `salary_data.py` — константы CZ рынка
- `pipeline_models.py` — все Pydantic модели
- Обе ветки параллельно → merge → develop

### Фаза 3: CV Parser (`feature/cv-parser`)
- `cv_parser.py` — pdfplumber для PDF, python-docx для DOCX
- Обработка edge case: scanned PDF → понятная ошибка

### Фаза 4: Pipeline (`feature/pipeline-steps`)
- `claude_client.py` — обёртка Anthropic SDK + JSON schema в промпт
- `step1_extract.py` → `step2_seniority.py` → `step3_salary.py` → `step4_recommendations.py`
- `orchestrator.py` — последовательный запуск, передаёт результат каждого шага
- `logging_config.py` — логирует время и токены каждого шага

### Фаза 5: API (`feature/fastapi-api`)
- `main.py` — 3 эндпоинта, CORS, загрузка файла, валидация типа

### Фаза 6: Frontend (`feature/streamlit-ui`)
- `streamlit_app.py` — полный UI с двумя фазами и 4 вкладками
- `@st.cache_data` по hash файла — нет повторных LLM вызовов

---

## Запуск

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить ключ
cp .env.example .env
# вставить ANTHROPIC_API_KEY в .env

# 3. Запустить backend
uvicorn app.main:app --reload

# 4. Запустить frontend (другой терминал)
streamlit run frontend/streamlit_app.py
```

---

## Верификация

- Загрузить тестовый PDF CV → должен вернуть `PipelineResult` JSON
- Загрузить DOCX → то же самое
- Загрузить JPEG → получить 400 ошибку
- Загрузить scanned PDF → получить понятное сообщение об ошибке
- `GET /health` → `{"status": "ok"}`
- `GET /salary-benchmarks` → словарь с диапазонами
- В Streamlit: ввести API key в sidebar если нет .env → анализ работает
- Повторная загрузка того же файла → результат из кэша (без нового LLM вызова)
