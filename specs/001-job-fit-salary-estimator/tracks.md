# Parallel Development Tracks

> Source plan: `plan.md`
> Generated: 2026-05-07
> Total tracks: 6

---

## Dependency Graph

```
Track 1: Scaffold            ← старт, нет зависимостей
    ↓
Track 2a: salary-data        ← параллельно с Track 2b (зависит от Track 1)
Track 2b: pydantic-models    ← параллельно с Track 2a (зависит от Track 1)
    ↓
Track 3: cv-parser           ← зависит от Track 1
    ↓
Track 4: pipeline-steps      ← зависит от Track 2a, 2b, Track 3
    ↓
Track 5: fastapi-api         ← зависит от Track 4
    ↓
Track 6: streamlit-ui        ← зависит от Track 5
```

**Можно запустить сразу:** Track 1
**После Track 1:** Track 2a, Track 2b, Track 3 — параллельно
**После 2a + 2b + 3:** Track 4
**После Track 4:** Track 5
**После Track 5:** Track 6

---

## Track 1: Scaffold — структура проекта

**Skills:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`
**Dependencies:** None (можно запустить сразу)
**Git ветка:** `chore/project-scaffold` → merge → `develop` → merge → `main`
**Scope:** Создать скелет проекта: папки, конфигурационные файлы, requirements.txt
**Files likely affected:**
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `README.md`
- `app/__init__.py`, `app/models/__init__.py`, `app/pipeline/__init__.py`, `app/utils/__init__.py`
- `specs/001-job-fit-salary-estimator/plan.md` (уже существует)

### Tasks
1. Переключиться на ветку `develop` (создать от `main`)
2. Создать ветку `chore/project-scaffold` от `develop`
3. Создать всю структуру папок согласно плану
4. Написать `requirements.txt` со всеми зависимостями
5. Написать `.env.example` с `ANTHROPIC_API_KEY=your_key_here`
6. Обновить `.gitignore` (добавить `.env`, `__pycache__`, `*.pyc`, `.DS_Store`)
7. Написать `README.md` с описанием проекта и инструкцией запуска
8. Создать пустые `__init__.py` во всех пакетах
9. Commit + merge в `develop` + merge в `main`

### Agent Prompt
> Ты работаешь над проектом "Job Fit & Salary Estimator" — AI система анализа CV с Chain of Thought LLM pipeline.
>
> **Задача:** Создать scaffold проекта (Фаза 1).
>
> **Рабочая директория:** `/Users/denis/RiderProjects/ Job Fit Salary Estimator/`
>
> **Git стратегия:**
> 1. Создай ветку `develop` от `main`
> 2. Создай ветку `chore/project-scaffold` от `develop`
> 3. После выполнения всех задач — merge `chore/project-scaffold` → `develop` → `main`
>
> **Создай следующую структуру:**
> ```
> app/__init__.py
> app/models/__init__.py
> app/pipeline/__init__.py
> app/data/  (пустая папка — создай .gitkeep)
> app/utils/__init__.py
> frontend/  (пустая папка — создай .gitkeep)
> ```
>
> **requirements.txt:**
> ```
> fastapi>=0.111.0
> uvicorn[standard]>=0.29.0
> anthropic>=0.25.0
> pdfplumber>=0.11.0
> python-docx>=1.1.0
> pydantic>=2.7.0
> streamlit>=1.35.0
> python-multipart>=0.0.9
> httpx>=0.27.0
> python-dotenv>=1.0.0
> ```
>
> **.env.example:**
> ```
> ANTHROPIC_API_KEY=your_anthropic_api_key_here
> ```
>
> **README.md** — опиши проект, стек, pipeline (4 шага CoT), инструкцию запуска в 2 команды.
>
> **Используй:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`

---

## Track 2a: salary-data — данные CZ рынка

**Skills:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`
**Dependencies:** Track 1 (scaffold должен существовать)
**Git ветка:** `feature/salary-data` → merge → `develop`
**Scope:** Синтетические данные о зарплатах чешского IT рынка
**Files likely affected:**
- `app/data/salary_data.py`

### Tasks
1. Создать ветку `feature/salary-data` от `develop`
2. Написать `salary_data.py` с константами
3. Commit + merge → `develop`

### Agent Prompt
> Ты работаешь над проектом "Job Fit & Salary Estimator".
>
> **Задача:** Создать файл с данными по зарплатам чешского IT рынка (Фаза 2a).
>
> **Git:** создай ветку `feature/salary-data` от `develop`, после — merge в `develop`.
>
> **Создай файл** `app/data/salary_data.py`:
>
> ```python
> # Синтетические данные CZ IT рынка (месячная брутто зарплата в CZK, 2024-2025)
>
> CZ_SALARY_RANGES: dict[str, dict[str, int]] = {
>     "intern":    {"min": 18_000, "median": 22_000, "max": 28_000},
>     "junior":    {"min": 30_000, "median": 42_000, "max": 55_000},
>     "mid":       {"min": 55_000, "median": 70_000, "max": 90_000},
>     "senior":    {"min": 85_000, "median": 105_000, "max": 135_000},
>     "lead":      {"min": 110_000, "median": 130_000, "max": 165_000},
>     "principal": {"min": 140_000, "median": 165_000, "max": 200_000},
> }
>
> SKILL_MULTIPLIERS: dict[str, float] = {
>     "machine_learning": 1.15,
>     "deep_learning": 1.15,
>     "cloud_aws": 1.12,
>     "cloud_azure": 1.10,
>     "cloud_gcp": 1.10,
>     "kubernetes": 1.08,
>     "data_engineering": 1.10,
>     "golang": 1.07,
>     "rust": 1.06,
>     "python": 1.05,
>     "typescript": 1.04,
>     "java": 1.00,
>     "react": 1.02,
>     "sql": 0.98,
>     "php": 0.92,
>     "wordpress": 0.85,
> }
>
> DOMAIN_MULTIPLIERS: dict[str, float] = {
>     "fintech": 1.18,
>     "banking": 1.15,
>     "saas": 1.10,
>     "gaming": 1.05,
>     "ecommerce": 1.00,
>     "consulting": 0.95,
>     "agency": 0.90,
>     "public_sector": 0.85,
> }
> ```
>
> **Используй:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`

---

## Track 2b: pydantic-models — все модели данных

**Skills:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`
**Dependencies:** Track 1 (scaffold должен существовать)
**Git ветка:** `feature/pydantic-models` → merge → `develop`
**Scope:** Все Pydantic v2 модели для 4 шагов CoT pipeline
**Files likely affected:**
- `app/models/pipeline_models.py`

### Tasks
1. Создать ветку `feature/pydantic-models` от `develop`
2. Написать все Pydantic модели
3. Commit + merge → `develop`

### Agent Prompt
> Ты работаешь над проектом "Job Fit & Salary Estimator".
>
> **Задача:** Создать все Pydantic v2 модели для CoT pipeline (Фаза 2b).
>
> **Git:** создай ветку `feature/pydantic-models` от `develop`, после — merge в `develop`.
>
> **Создай файл** `app/models/pipeline_models.py` со следующими моделями:
>
> - `TechSkill` — name: str, years_experience: float
> - `SalaryRange` — min_czk: int, median_czk: int, max_czk: int
> - `CVFacts` — full_name, total_years_experience, tech_skills, soft_skills, education_level (Literal), industries, notable_achievements
> - `SeniorityEvaluation` — level (Literal intern/junior/mid/senior/lead/principal), score (0-100), reasoning, strengths, weaknesses, confidence (Literal low/medium/high), cv_facts: CVFacts
> - `SalaryEstimate` — estimated_range: SalaryRange, market_range_for_level: SalaryRange, fit_score (0-100), salary_reasoning, top_skills_driving_salary, seniority_eval: SeniorityEvaluation
> - `Recommendation` — action: str, impact: Literal[low/medium/high], timeframe_months: int, expected_salary_increase_pct: float
> - `GrowthRecommendations` — target_salary_czk: int, recommendations: list[Recommendation], narrative: str, salary_estimate: SalaryEstimate
> - `PipelineResult` — cv_facts, seniority, salary, recommendations, processing_time_seconds: float
>
> Используй Pydantic v2 синтаксис (`model_config`, `model_validate`).
>
> **Используй:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`

---

## Track 3: cv-parser — извлечение текста из CV

**Skills:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`
**Dependencies:** Track 1 (scaffold)
**Git ветка:** `feature/cv-parser` → merge → `develop`
**Scope:** Модуль для извлечения текста из PDF и DOCX файлов
**Files likely affected:**
- `app/pipeline/cv_parser.py`

### Tasks
1. Создать ветку `feature/cv-parser` от `develop`
2. Написать `cv_parser.py`
3. Commit + merge → `develop`

### Agent Prompt
> Ты работаешь над проектом "Job Fit & Salary Estimator".
>
> **Задача:** Создать модуль извлечения текста из CV файлов (Фаза 3).
>
> **Git:** создай ветку `feature/cv-parser` от `develop`, после — merge в `develop`.
>
> **Создай файл** `app/pipeline/cv_parser.py` с функцией:
>
> ```python
> def extract_text(file_bytes: bytes, filename: str) -> str:
>     """Извлекает текст из PDF или DOCX файла."""
> ```
>
> Логика:
> - Если `.pdf` — использовать `pdfplumber`
> - Если `.docx` — использовать `python-docx`
> - Если другой формат — raise `ValueError("Unsupported file format. Please upload PDF or DOCX.")`
> - Если PDF — проверить что извлечённый текст не пустой (< 50 символов). Если пустой — raise `ValueError("CV appears to be a scanned image — please upload a text-based PDF.")`
> - Очистить текст: убрать лишние пробелы, нормализовать переносы строк
>
> **Используй:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`

---

## Track 4: pipeline-steps — CoT pipeline

**Skills:** `/claude-api`, `/feature-dev:feature-dev`, `/checkpoint`, `/superpowers:verification-before-completion`
**Dependencies:** Track 2a, Track 2b, Track 3 (все должны быть в `develop`)
**Git ветка:** `feature/pipeline-steps` → merge → `develop`
**Scope:** Claude API wrapper + 4 шага CoT + orchestrator + logging
**Files likely affected:**
- `app/utils/claude_client.py`
- `app/utils/logging_config.py`
- `app/pipeline/step1_extract.py`
- `app/pipeline/step2_seniority.py`
- `app/pipeline/step3_salary.py`
- `app/pipeline/step4_recommendations.py`
- `app/pipeline/orchestrator.py`

### Tasks
1. Создать ветку `feature/pipeline-steps` от `develop`
2. Написать `logging_config.py`
3. Написать `claude_client.py` — обёртка Anthropic SDK
4. Написать `step1_extract.py`
5. Написать `step2_seniority.py`
6. Написать `step3_salary.py` (использует данные из `salary_data.py`)
7. Написать `step4_recommendations.py`
8. Написать `orchestrator.py`
9. Commit + merge → `develop`

### Agent Prompt
> Ты работаешь над проектом "Job Fit & Salary Estimator".
>
> **Задача:** Создать Chain of Thought LLM pipeline (Фаза 4) — самая важная часть проекта.
>
> **Git:** создай ветку `feature/pipeline-steps` от `develop`, после — merge в `develop`.
>
> **Прочитай сначала:**
> - `app/models/pipeline_models.py` — все Pydantic модели
> - `app/data/salary_data.py` — данные CZ рынка
> - `app/pipeline/cv_parser.py` — парсер CV
>
> **Архитектура Chain of Thought:**
> ```
> cv_text → step1 → CVFacts → step2 → SeniorityEvaluation → step3 → SalaryEstimate → step4 → GrowthRecommendations
> ```
> Каждый шаг получает результат предыдущего как контекст.
>
> **`app/utils/logging_config.py`:** настрой logging с форматом `%(asctime)s | %(levelname)s | %(name)s | %(message)s`
>
> **`app/utils/claude_client.py`:**
> - Функция `call_claude(system_prompt, user_message, response_model)` → возвращает экземпляр Pydantic модели
> - Использует `claude-3-5-sonnet-20241022`
> - Добавляет JSON schema модели в system prompt
> - Парсит JSON из ответа, валидирует через Pydantic
> - 1 retry при JSON parse failure
> - Логирует время и количество токенов каждого вызова
> - Читает `ANTHROPIC_API_KEY` из env (поддержка `.env` через python-dotenv)
>
> **Каждый step файл (`step1_extract.py` и т.д.):**
> - Экспортирует одну функцию `run(...)` → возвращает Pydantic модель
> - Промпты — модульные константы в том же файле
> - Step 3 получает релевантный диапазон из `salary_data.py` и передаёт в промпт как факт
>
> **`app/pipeline/orchestrator.py`:**
> ```python
> def run_pipeline(cv_text: str, api_key: str | None = None) -> PipelineResult:
>     # Запускает все 4 шага последовательно
>     # Замеряет общее время
>     # Возвращает PipelineResult
> ```
>
> **Используй:** `/claude-api`, `/feature-dev:feature-dev`, `/checkpoint`, `/superpowers:verification-before-completion`

---

## Track 5: fastapi-api — REST API

**Skills:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`
**Dependencies:** Track 4 (pipeline должен быть готов)
**Git ветка:** `feature/fastapi-api` → merge → `develop`
**Scope:** FastAPI приложение с 3 эндпоинтами
**Files likely affected:**
- `app/main.py`

### Tasks
1. Создать ветку `feature/fastapi-api` от `develop`
2. Написать `app/main.py`
3. Commit + merge → `develop`

### Agent Prompt
> Ты работаешь над проектом "Job Fit & Salary Estimator".
>
> **Задача:** Создать FastAPI приложение (Фаза 5).
>
> **Git:** создай ветку `feature/fastapi-api` от `develop`, после — merge в `develop`.
>
> **Прочитай сначала:**
> - `app/pipeline/orchestrator.py`
> - `app/models/pipeline_models.py`
> - `app/data/salary_data.py`
>
> **Создай `app/main.py`** с тремя эндпоинтами:
>
> 1. `POST /analyze`
>    - Принимает `file: UploadFile` (PDF или DOCX, max 5MB)
>    - Опциональный header `X-API-Key` для передачи ANTHROPIC_API_KEY
>    - Валидирует тип файла (400 если не PDF/DOCX)
>    - Запускает `orchestrator.run_pipeline(cv_text, api_key)`
>    - Возвращает `PipelineResult`
>
> 2. `GET /health`
>    - Возвращает `{"status": "ok", "model": "claude-3-5-sonnet-20241022", "timestamp": "..."}`
>
> 3. `GET /salary-benchmarks`
>    - Возвращает `CZ_SALARY_RANGES` и `SKILL_MULTIPLIERS` из `salary_data.py`
>
> **CORS:** включи для `http://localhost:8501` и `http://127.0.0.1:8501`
>
> **Используй:** `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`

---

## Track 6: streamlit-ui — веб интерфейс

**Skills:** `/frontend-design:frontend-design`, `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`
**Dependencies:** Track 5 (FastAPI должен быть готов)
**Git ветка:** `feature/streamlit-ui` → merge → `develop` → merge → `main`
**Scope:** Полный Streamlit UI — загрузка CV + отображение результатов
**Files likely affected:**
- `frontend/streamlit_app.py`

### Tasks
1. Создать ветку `feature/streamlit-ui` от `develop`
2. Написать `frontend/streamlit_app.py`
3. Commit + merge → `develop` → merge → `main` (финальный релиз)

### Agent Prompt
> Ты работаешь над проектом "Job Fit & Salary Estimator".
>
> **Задача:** Создать Streamlit UI (Фаза 6 — финальная).
>
> **Git:** создай ветку `feature/streamlit-ui` от `develop`, после — merge в `develop`, затем merge `develop` → `main`.
>
> **Создай `frontend/streamlit_app.py`** (~150-200 строк:
>
> **Sidebar:**
> - Поле ввода `ANTHROPIC_API_KEY` (type="password") — если не задан в .env
> - Индикатор `/health` — зелёный если API доступен, красный если нет
> - `BASE_URL` по умолчанию `http://localhost:8000`
>
> **Фаза 1 (нет результата в session_state):**
> - `st.file_uploader` для PDF/DOCX
> - Кнопка "Analyze CV"
> - Progress bar с текстом шагов: "Extracting facts...", "Evaluating seniority...", "Calculating salary...", "Generating recommendations..."
>
> **Фаза 2 (есть результат):**
> - KPI метрики в 4 колонках: Seniority Score, Level, Salary Range, Target +30%
> - 4 вкладки:
>   - **CV Summary** — скиллы тэгами, опыт, образование, индустрии
>   - **Seniority** — progress bar score, strengths/weaknesses списками, reasoning в expander
>   - **Salary** — bar chart "Ты vs Рынок" (`st.bar_chart`), топ скиллы, reasoning в expander
>   - **Recommendations** — для каждой: action, impact badge (🔴/🟡🟢), timeframe, % increase; narrative в expander
> - Кнопка "Analyze Another CV" (сброс session_state)
>
> **Кэширование:** `@st.cache_data` на функции вызова API, ключ = hash загруженного файла
>
> **Используй:** `/frontend-design:frontend-design`, `/feature-dev:feature-dev`, `/superpowers:verification-before-completion`
