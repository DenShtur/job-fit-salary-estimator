import json

from app.models.pipeline_models import GrowthRecommendations, SalaryEstimate
from app.utils.claude_client import call_claude

SYSTEM_PROMPT = """You are an expert career coach specializing in IT career growth
in the Czech Republic. Your task is to provide concrete, actionable recommendations
that will help a candidate increase their salary by 30%.

Guidelines for recommendations:
- Provide 3-5 specific, actionable recommendations
- Each recommendation must have a realistic timeframe (in months)
- Focus on highest-impact actions first (certifications, skills, domain switches)
- Be specific: not "learn cloud" but "get AWS Solutions Architect Associate certification"
- Consider the Czech market specifically — what employers here value most
- target_salary_czk = current median salary * 1.30 (round to nearest 1000)
- narrative should be 2-3 paragraphs: current position analysis, growth path, motivation"""


def run(
    salary_estimate: SalaryEstimate, api_key: str | None = None
) -> GrowthRecommendations:
    """Шаг 4: Генерирует план карьерного роста для увеличения зарплаты на +30%."""
    user_message = (
        "Create a career growth plan for this candidate to achieve +30% salary increase:\n\n"
        f"{json.dumps(salary_estimate.model_dump(), indent=2, ensure_ascii=False)}"
    )
    return call_claude(SYSTEM_PROMPT, user_message, GrowthRecommendations, api_key)
