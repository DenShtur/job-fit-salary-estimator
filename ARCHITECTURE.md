# Architecture & Technical Deep-Dive

Этот документ объясняет как устроен Job Fit & Salary Estimator: технологии, pipeline, структура кода и решения, принятые при разработке.

---

## Общая архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    Browser / User                        │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP / SSE
┌───────────────────────▼─────────────────────────────────┐
│              Streamlit Frontend  :8501                   │
│   • File upload (PDF/DOCX)                               │
│   • SSE consumer → live progress bar                     │
│   • 4-tab results: CV / Seniority / Salary / Growth      │
│   • Download Report (JSON)                               │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP POST /analyze/stream
┌───────────────────────▼─────────────────────────────────┐
│               FastAPI Backend  :8000                     │
│   POST /analyze/stream   ← SSE endpoint                 │
│   POST /analyze          ← sync endpoint                 │
│   GET  /health                                           │
│   GET  /salary-benchmarks                               │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│            Chain of Thought Pipeline                     │
│   Step 1 → Step 2 → Step 3 → Step 4                     │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS
┌───────────────────────▼─────────────────────────────────┐
│              Anthropic Claude API                        │
│              model: claude-sonnet-4-5                    │
└─────────────────────────────────────────────────────────┘
```

---

## Chain of Thought Pipeline

Ключевая идея: каждый шаг получает **полный вывод предыдущего** как контекст. Это позволяет каждому шагу «думать» опираясь на уже извлечённые факты, а не на сырой текст CV.

### Шаг 1 — Извлечение фактов (`step1_extract.py`)

**Вход:** сырой текст CV
**Выход:** `CVFacts` — структурированный объект

```python
CVFacts(
    full_name="Jan Novák",
    total_years_experience=3.5,
    tech_skills=[TechSkill(name="Python", years_experience=3.0), ...],
    soft_skills=["communication", "problem-solving"],
    education_level="bachelor",   # Enum: intern/junior/mid/senior/lead/principal
    industries=["saas", "fintech"],
    notable_achievements=["Built Telegram bot with 2k MAU"]
)
```

Промпт просит модель **только извлекать факты**, не оценивать. Это принцип разделения ответственности — оценка делается на шаге 2.

---

### Шаг 2 — Оценка сениорити (`step2_seniority.py`)

**Вход:** `CVFacts` из шага 1
**Выход:** `SeniorityEvaluation`

Модель получает `CVFacts` как JSON и оценивает по критериям:
- Глубина технических навыков (не просто список, а годы и контекст)
- Масштаб проектов (личные pet-проекты vs продакшн системы)
- Командный опыт
- Образование как фактор, не как главный критерий

```python
SeniorityEvaluation(
    level="mid",          # intern | junior | mid | senior | lead | principal
    score=55,             # 0–100
    confidence="medium",  # low | medium | high
    reasoning="...",      # Chain of Thought — объяснение решения
    strengths=["..."],
    weaknesses=["..."],
    cv_facts=cv_facts,    # propagate для следующих шагов
)
```

`score` — не порог, а непрерывная шкала. Уровни:

| Level | Score |
|-------|-------|
| Intern | 10–29 |
| Junior | 30–49 |
| Mid | 50–69 |
| Senior | 70–84 |
| Lead | 85–94 |
| Principal | 95–100 |

---

### Шаг 3 — Прогноз зарплаты (`step3_salary.py`)

**Вход:** `SeniorityEvaluation` (содержит `CVFacts` внутри)
**Выход:** `SalaryEstimate`

В системный промпт **инжектируются реальные данные** CZ IT рынка из `salary_data.py`:

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
    "llm": 1.18, "machine_learning": 1.15, "cloud_aws": 1.12,
    "kubernetes": 1.10, "python": 1.05, ...
}

DOMAIN_MULTIPLIERS = {
    "fintech": 1.18, "saas": 1.10, "consulting": 0.95, ...
}
```

Модель видит эти данные и обосновывает свою оценку. `fit_score` (0–100) отражает насколько скиллы кандидата соответствуют текущему рынку.

---

### Шаг 4 — Рекомендации роста (`step4_recommendations.py`)

**Вход:** slim-контекст из шага 3 (только ключевые поля, ~800 токенов)
**Выход:** `GrowthRecommendations`

Получает целевую зарплату (+30% от медианы) и генерирует 3–5 конкретных действий:

```python
Recommendation(
    action="Get AWS Solutions Architect cert + deploy 2 projects",
    impact="high",                   # high | medium | low
    timeframe_months=4,
    expected_salary_increase_pct=12.0,
)
```

**Почему slim-контекст?** Полный дамп `SalaryEstimate` → `SeniorityEvaluation` → `CVFacts` занимает ~3500 токенов. При `MAX_TOKENS=4096` на вывод почти ничего не остаётся и JSON обрезается. Передаём только 6 ключевых полей → ~800 токенов входа, ~1500 на вывод.

---

## LLM Client (`claude_client.py`)

Три уровня защиты от некорректного JSON:

### 1. Schema injection
JSON Schema целевой Pydantic модели инжектируется в system prompt:
```
You MUST respond with valid JSON matching this schema: { ... }
```

### 2. Strip markdown
LLM иногда оборачивает ответ в ```json ... ```. `_clean_raw()` убирает это:
```python
if raw.startswith("```"):
    raw = raw.split("```", 2)[1]
    if raw.startswith("json"):
        raw = raw[4:]
```

### 3. Brace-matching extraction
Даже если вокруг JSON есть лишний текст — находим первую `{` и идём по вложенности скобок до закрывающей:
```python
match = re.search(r'\{', raw)
depth = 0
for i, ch in enumerate(raw[start:], start):
    if ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            end = i; break
```

### Retry
2 попытки. При неудаче на первой — повтор с тем же промптом. Если обе упали — исключение с raw-ответом для дебага.

### Параметры
```python
MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4096
timeout = 60.0   # секунды — не висит бесконечно
```

---

## SSE Streaming

Классическая проблема: пока LLM думает (15–30 сек) — UI показывает spinner, пользователь ничего не знает.

**Решение:** FastAPI endpoint `POST /analyze/stream` — генератор, который `yield`-ает JSON-события после каждого шага:

```python
def event_stream():
    yield f"data: {json.dumps({'step': 1, 'progress': 10, 'label': 'Extracting...'}}\n\n"
    cv_facts = step1_extract.run(cv_text)

    yield f"data: {json.dumps({'step': 2, 'progress': 35, ...})}\n\n"
    seniority = step2_seniority.run(cv_facts)
    # ... и т.д.

    yield f"data: {json.dumps({'step': 'done', 'result': result.model_dump()})}\n\n"
```

Streamlit читает поток через `httpx.Client.stream()`:

```python
with client.stream("POST", f"{BASE_URL}/analyze/stream", files=...) as resp:
    for line in resp.iter_lines():
        event = json.loads(line[6:])   # strip "data: "
        progress_bar.progress(event["progress"])
        steps_box.markdown(render_steps(...))
```

Прогресс: 10% → 35% → 60% → 85% → 100%

---

## Кэширование

`@st.cache_data` по MD5 хешу файла: если пользователь загружает тот же CV дважды — LLM не вызывается, результат берётся из кэша Streamlit. Ключ кэша: `md5(file_bytes) + api_key`.

---

## CV Parsing (`cv_parser.py`)

| Формат | Библиотека | Нюансы |
|--------|-----------|--------|
| PDF | pdfplumber | Детектирует сканы (< 50 символов текста → `ValueError`) |
| DOCX | python-docx | Читает все параграфы + таблицы |

После извлечения — `_normalize()`: убирает двойные пробелы, лишние переносы строк.

---

## Структура проекта

```
.
├── app/
│   ├── main.py                      # FastAPI: endpoints, CORS, validation
│   ├── models/
│   │   └── pipeline_models.py       # Все Pydantic v2 модели
│   ├── pipeline/
│   │   ├── cv_parser.py             # PDF/DOCX → str
│   │   ├── step1_extract.py         # CV text → CVFacts
│   │   ├── step2_seniority.py       # CVFacts → SeniorityEvaluation
│   │   ├── step3_salary.py          # SeniorityEval → SalaryEstimate
│   │   ├── step4_recommendations.py # SalaryEstimate → GrowthRecommendations
│   │   └── orchestrator.py          # Sequential runner (для sync /analyze)
│   ├── data/
│   │   └── salary_data.py           # CZ IT рынок: диапазоны + мультипликаторы
│   └── utils/
│       ├── claude_client.py         # call_claude(), _clean_raw(), retry
│       └── logging_config.py        # JSON-friendly logging
├── frontend/
│   └── streamlit_app.py             # UI: upload → SSE → 4 вкладки
├── tests/
│   ├── test_cv_parser.py            # PDF/DOCX parsing + edge cases
│   ├── test_pipeline_models.py      # Pydantic validators
│   ├── test_salary_data.py          # Market data integrity
│   └── test_claude_client.py        # _clean_raw() edge cases
├── .streamlit/
│   └── config.toml                  # Dark theme (base = "dark")
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt             # pytest
├── run.sh                           # One-command launcher
└── .env.example
```

---

## Git Workflow

```
main
 └── develop
      ├── feature/security-and-tests   # тесты, .env fix, _clean_raw
      ├── feature/docker               # Dockerfile, docker-compose
      ├── feature/code-quality         # timeout, Pydantic fix, JSON export
      └── feature/docs                 # README, ARCHITECTURE
```

Каждая feature-ветка мержится в `develop`, `develop` → `main` при готовности версии.

---

## Технические решения и почему

| Решение | Альтернатива | Почему выбрано |
|---------|-------------|----------------|
| SSE вместо polling | WebSocket / long-poll | Проще для FastAPI + Streamlit, однонаправленный поток — идеально |
| Pydantic v2 schema injection | Prompt engineering вручную | Гарантированная структура, автовалидация |
| Brace-matching JSON | `json.loads()` напрямую | LLM иногда добавляет текст до/после JSON |
| Slim context на шаге 4 | Полный дамп объектов | Полный дамп ~3500 токенов → обрезает вывод при MAX_TOKENS=4096 |
| MD5 кэш в Streamlit | Без кэша | Повторный анализ того же CV → 0 API вызовов |
| pdfplumber vs PyMuPDF | PyMuPDF | pdfplumber точнее на CV с таблицами, легче в зависимостях |
