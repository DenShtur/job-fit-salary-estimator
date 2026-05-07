import json
from datetime import datetime, timezone

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.data.salary_data import CZ_SALARY_RANGES, DOMAIN_MULTIPLIERS, SKILL_MULTIPLIERS
from app.models.pipeline_models import PipelineResult
from app.pipeline import orchestrator
from app.pipeline import step1_extract, step2_seniority, step3_salary, step4_recommendations
from app.pipeline.cv_parser import extract_text
from app.utils.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Job Fit & Salary Estimator",
    description="AI-powered CV analysis with Chain of Thought LLM pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@app.post("/analyze", response_model=PipelineResult)
async def analyze_cv(
    file: UploadFile = File(...),
    x_api_key: str | None = Header(default=None),
) -> PipelineResult:
    """Анализирует CV и возвращает seniority score, зарплату и рекомендации."""
    # Валидация имени файла
    filename = file.filename or ""
    if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".docx")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a PDF or DOCX file.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5 MB.",
        )

    logger.info(f"Received CV | file={filename} | size={len(file_bytes)} bytes")

    try:
        cv_text = extract_text(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = orchestrator.run_pipeline(cv_text, api_key=x_api_key)
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))

    return result


@app.post("/analyze/stream")
async def analyze_cv_stream(
    file: UploadFile = File(...),
    x_api_key: str | None = Header(default=None),
) -> StreamingResponse:
    """SSE endpoint — отправляет события о каждом шаге pipeline в реальном времени."""
    filename = file.filename or ""
    if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".docx")):
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5 MB.")

    try:
        cv_text = extract_text(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    def event_stream():
        import time
        total_start = time.perf_counter()
        try:
            yield f"data: {json.dumps({'step': 1, 'label': 'Extracting CV facts...', 'progress': 10})}\n\n"
            cv_facts = step1_extract.run(cv_text, x_api_key)

            yield f"data: {json.dumps({'step': 2, 'label': 'Evaluating seniority...', 'progress': 35})}\n\n"
            seniority = step2_seniority.run(cv_facts, x_api_key)

            yield f"data: {json.dumps({'step': 3, 'label': 'Calculating salary...', 'progress': 60})}\n\n"
            salary = step3_salary.run(seniority, x_api_key)

            yield f"data: {json.dumps({'step': 4, 'label': 'Generating recommendations...', 'progress': 85})}\n\n"
            recommendations = step4_recommendations.run(salary, x_api_key)

            total_time = round(time.perf_counter() - total_start, 2)
            result = PipelineResult(
                cv_facts=cv_facts,
                seniority=seniority,
                salary=salary,
                recommendations=recommendations,
                processing_time_seconds=total_time,
            )
            yield f"data: {json.dumps({'step': 'done', 'progress': 100, 'result': result.model_dump()})}\n\n"
        except Exception as e:
            logger.exception("Stream pipeline failed")
            yield f"data: {json.dumps({'step': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
async def health() -> dict:
    """Статус сервиса."""
    return {
        "status": "ok",
        "model": "claude-sonnet-4-5",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/salary-benchmarks")
async def salary_benchmarks() -> dict:
    """Данные CZ IT рынка — диапазоны зарплат и мультипликаторы."""
    return {
        "salary_ranges": CZ_SALARY_RANGES,
        "skill_multipliers": SKILL_MULTIPLIERS,
        "domain_multipliers": DOMAIN_MULTIPLIERS,
        "currency": "CZK",
        "period": "monthly_gross",
        "market": "Czech Republic",
        "year": "2024-2025",
    }
