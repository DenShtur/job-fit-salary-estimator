import json
import os
import re
import time
from typing import TypeVar

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

from app.utils.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4096
T = TypeVar("T", bound=BaseModel)


def call_claude(
    system_prompt: str,
    user_message: str,
    response_model: type[T],
    api_key: str | None = None,
) -> T:
    """Вызывает Claude API и возвращает валидированный Pydantic объект.

    Args:
        system_prompt: системный промпт с инструкциями
        user_message: сообщение пользователя
        response_model: Pydantic модель для валидации ответа
        api_key: опциональный API ключ (иначе берётся из env)

    Returns:
        Экземпляр response_model с данными из ответа LLM

    Raises:
        ValueError: если LLM вернул невалидный JSON после retry
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=key)

    schema = response_model.model_json_schema()
    full_system = (
        f"{system_prompt}\n\n"
        "IMPORTANT: Respond ONLY with a valid JSON object matching this schema. "
        "No markdown, no explanation, just raw JSON.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}"
    )

    for attempt in range(2):
        start = time.perf_counter()
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=full_system,
            messages=[{"role": "user", "content": user_message}],
            timeout=60.0,
        )
        elapsed = time.perf_counter() - start
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        logger.info(
            f"Claude call | model={MODEL} | step={response_model.__name__} "
            f"| in={input_tokens} out={output_tokens} tokens | {elapsed:.2f}s"
        )

        raw = _clean_raw(response.content[0].text.strip())

        try:
            data = json.loads(raw)
            return response_model.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            if attempt == 0:
                logger.warning(f"JSON parse failed (attempt 1), retrying... error={e}")
                continue
            raise ValueError(
                f"LLM returned invalid JSON for {response_model.__name__} "
                f"after 2 attempts. Raw response: {raw[:300]}"
            ) from e

    raise ValueError("Unreachable")


def _clean_raw(raw: str) -> str:
    """Очищает ответ LLM: убирает markdown обёртку и вырезает JSON по скобкам."""
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    match = re.search(r'\{', raw)
    if match:
        start = match.start()
        depth = 0
        end = start
        for i, ch in enumerate(raw[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        raw = raw[start:end + 1]

    return raw.strip()
