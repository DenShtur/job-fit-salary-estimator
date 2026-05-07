import json

from app.data.salary_data import CZ_SALARY_RANGES, DOMAIN_MULTIPLIERS, SKILL_MULTIPLIERS
from app.models.pipeline_models import SalaryEstimate, SeniorityEvaluation
from app.utils.claude_client import call_claude

SYSTEM_PROMPT_TEMPLATE = """You are a compensation specialist for the Czech IT market.
Your task is to estimate a fair salary range for a candidate based on their seniority
evaluation and market data.

Use the following Czech market data as your ground truth:

Market salary range for this candidate's level ({level}):
{market_range}

Skill multipliers (applied to median salary):
{skill_multipliers}

Domain multipliers:
{domain_multipliers}

Instructions:
- estimated_range should reflect THIS candidate's actual worth (considering their specific
  skills and domain experience), not just the generic level range
- market_range_for_level should be the raw range for their level from the data above
- fit_score (0-100): how well the candidate's profile fits the CZ market demand
- Identify top 3 skills that most positively influence this candidate's salary"""


def run(
    seniority_eval: SeniorityEvaluation, api_key: str | None = None
) -> SalaryEstimate:
    """Шаг 3: Рассчитывает зарплатный прогноз на основе рынка CZ."""
    level = seniority_eval.level
    market_range = CZ_SALARY_RANGES.get(level, CZ_SALARY_RANGES["mid"])

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        level=level,
        market_range=json.dumps(market_range, indent=2),
        skill_multipliers=json.dumps(SKILL_MULTIPLIERS, indent=2),
        domain_multipliers=json.dumps(DOMAIN_MULTIPLIERS, indent=2),
    )

    user_message = (
        "Estimate the salary for this candidate based on their evaluation:\n\n"
        f"{json.dumps(seniority_eval.model_dump(), indent=2, ensure_ascii=False)}"
    )

    return call_claude(system_prompt, user_message, SalaryEstimate, api_key)
