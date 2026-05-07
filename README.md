# Job Fit & Salary Estimator

AI система анализа CV с оценкой сениорити, прогнозом зарплаты и рекомендациями по карьерному росту.

## Как работает

Система использует **Chain of Thought LLM pipeline** — 4 последовательных шага, каждый из которых строится на результате предыдущего:

```
CV (PDF/DOCX)
    ↓
Шаг 1: Извлечение фактов    → опыт, скиллы, образование, достижения
    ↓
Шаг 2: Оценка сениорити     → score 0-100, уровень, сильные/слабые стороны
    ↓
Шаг 3: Прогноз зарплаты     → диапазон CZK, сравнение с рынком
    ↓
Шаг 4: Рекомендации         → конкретный план для роста зарплаты на +30%
```

## Стек

| Слой | Технология |
|------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| LLM | Claude API (claude-3-5-sonnet) |
| CV парсинг | pdfplumber + python-docx |
| Валидация | Pydantic v2 |

## Запуск

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить API ключ
cp .env.example .env
# Открыть .env и вставить ANTHROPIC_API_KEY

# 3. Запустить backend (терминал 1)
uvicorn app.main:app --reload

# 4. Запустить frontend (терминал 2)
streamlit run frontend/streamlit_app.py
```

Открыть в браузере: http://localhost:8501

## API

| Метод | Endpoint | Описание |
|-------|----------|---------|
| POST | `/analyze` | Анализ CV (PDF/DOCX) |
| GET | `/health` | Статус сервиса |
| GET | `/salary-benchmarks` | Данные рынка CZ |

## Структура проекта

```
app/
├── main.py                    # FastAPI
├── models/pipeline_models.py  # Pydantic модели
├── pipeline/
│   ├── cv_parser.py           # PDF/DOCX → text
│   ├── step1_extract.py       # LLM шаг 1
│   ├── step2_seniority.py     # LLM шаг 2
│   ├── step3_salary.py        # LLM шаг 3
│   ├── step4_recommendations.py # LLM шаг 4
│   └── orchestrator.py        # Запуск pipeline
├── data/salary_data.py        # Данные CZ рынка
└── utils/claude_client.py     # Claude API wrapper
frontend/
└── streamlit_app.py           # UI
```
