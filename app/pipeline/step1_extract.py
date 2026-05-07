from app.models.pipeline_models import CVFacts
from app.utils.claude_client import call_claude

SYSTEM_PROMPT = """You are an expert CV analyst. Your task is to extract structured
information from a candidate's CV text.

Be precise and objective. Extract only what is explicitly stated in the CV.
For years_experience, estimate based on employment history dates.
For education_level, choose the highest level achieved."""

def run(cv_text: str, api_key: str | None = None) -> CVFacts:
    """Шаг 1: Извлекает структурированные факты из текста CV."""
    user_message = f"Extract structured information from this CV:\n\n{cv_text}"
    return call_claude(SYSTEM_PROMPT, user_message, CVFacts, api_key)
