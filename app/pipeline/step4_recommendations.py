import json

from app.models.pipeline_models import GrowthRecommendations, SalaryEstimate
from app.utils.claude_client import call_claude

SYSTEM_PROMPT = """You are an expert career coach specializing in IT career growth
in the Czech Republic. Your task is to provide concrete, actionable recommendations
that will help a candidate increase their salary by 30%.

Guidelines for recommendations:
- Provide 3 to 5 specific, actionable recommendations
- Each recommendation must have a realistic timeframe (in months)
- Focus on highest-impact actions first (certifications, skills, domain switches)
- Be specific: not "learn cloud" but "get AWS Solutions Architect Associate certification"
- Consider the Czech market specifically — what employers here value most
- target_salary_czk = current median salary * 1.30 (round to nearest 1000)
- narrative MUST be max 3 sentences total — keep it concise"""


def run(
    salary_estimate: SalaryEstimate, api_key: str | None = None
) -> GrowthRecommendations:
    """Шаг 4: Генерирует план карьерного роста для увеличения зарплаты на +30%."""
    context = {
        "seniority_level": salary_estimate.seniority_eval.level,
        "seniority_score": salary_estimate.seniority_eval.score,
        "estimated_median_czk": salary_estimate.estimated_range.median_czk,
        "top_skills": salary_estimate.top_skills_driving_salary,
        "weaknesses": salary_estimate.seniority_eval.weaknesses,
        "fit_score": salary_estimate.fit_score,
    }
    user_message = (
        "Create a concise career growth plan for this candidate to achieve +30% salary:\n\n"
        f"{json.dumps(context, indent=2, ensure_ascii=False)}"
    )
    return call_claude(SYSTEM_PROMPT, user_message, GrowthRecommendations, api_key)
