import time

from app.models.pipeline_models import PipelineResult
from app.pipeline import step1_extract, step2_seniority, step3_salary, step4_recommendations
from app.utils.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def run_pipeline(cv_text: str, api_key: str | None = None) -> PipelineResult:
    """Запускает полный Chain of Thought pipeline из 4 шагов.

    Args:
        cv_text: извлечённый текст CV
        api_key: опциональный Anthropic API ключ

    Returns:
        PipelineResult со всеми результатами анализа
    """
    total_start = time.perf_counter()

    logger.info("Pipeline started")

    logger.info("Step 1/4: Extracting CV facts...")
    cv_facts = step1_extract.run(cv_text, api_key)
    logger.info(f"Step 1 done | name={cv_facts.full_name} | exp={cv_facts.total_years_experience}y")

    logger.info("Step 2/4: Evaluating seniority...")
    seniority = step2_seniority.run(cv_facts, api_key)
    logger.info(f"Step 2 done | level={seniority.level} | score={seniority.score}")

    logger.info("Step 3/4: Estimating salary...")
    salary = step3_salary.run(seniority, api_key)
    logger.info(
        f"Step 3 done | range={salary.estimated_range.min_czk}-"
        f"{salary.estimated_range.max_czk} CZK"
    )

    logger.info("Step 4/4: Generating recommendations...")
    recommendations = step4_recommendations.run(salary, api_key)
    logger.info(
        f"Step 4 done | target={recommendations.target_salary_czk} CZK | "
        f"recs={len(recommendations.recommendations)}"
    )

    total_time = time.perf_counter() - total_start
    logger.info(f"Pipeline completed in {total_time:.2f}s")

    return PipelineResult(
        cv_facts=cv_facts,
        seniority=seniority,
        salary=salary,
        recommendations=recommendations,
        processing_time_seconds=round(total_time, 2),
    )
