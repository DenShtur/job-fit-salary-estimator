import json

from app.models.pipeline_models import CVFacts, SeniorityEvaluation
from app.utils.claude_client import call_claude

SYSTEM_PROMPT = """You are a senior technical recruiter with 10+ years of experience
evaluating software engineers. Your task is to assess the seniority level of a candidate
based on their structured CV data.

Seniority scoring guide (0-100):
- intern (0-20): student or < 1 year experience, basic skills
- junior (21-40): 1-2 years, works under supervision, limited scope
- mid (41-60): 2-5 years, works independently, owns features
- senior (61-80): 5+ years, leads projects, mentors others, system design
- lead (81-90): technical leadership, cross-team impact, architecture decisions
- principal (91-100): org-wide technical strategy, deep domain expertise

Be honest about weaknesses — this helps the candidate grow."""


def run(cv_facts: CVFacts, api_key: str | None = None) -> SeniorityEvaluation:
    """Шаг 2: Оценивает уровень сениорити на основе фактов CV."""
    user_message = (
        "Evaluate the seniority level of this candidate based on their CV data:\n\n"
        f"{json.dumps(cv_facts.model_dump(), indent=2, ensure_ascii=False)}"
    )
    return call_claude(SYSTEM_PROMPT, user_message, SeniorityEvaluation, api_key)
