# Данные CZ IT рынка — месячная брутто зарплата в CZK, 2024-2025
# Источники: platy.cz, Český statistický úřad (CSU 2024), jobs.cz, Glassdoor Prague
# CSU 2024: средняя зарплата ICT-специалиста = 94 000 CZK/мес (+7% г/г)

from functools import lru_cache


CZ_SALARY_RANGES: dict[str, dict[str, int]] = {
    "intern":    {"min": 15_000, "median": 25_000, "max": 40_000},
    "junior":    {"min": 40_000, "median": 55_000, "max": 75_000},
    "mid":       {"min": 60_000, "median": 80_000, "max": 105_000},
    "senior":    {"min": 85_000, "median": 110_000, "max": 145_000},
    "lead":      {"min": 110_000, "median": 140_000, "max": 175_000},
    "principal": {"min": 140_000, "median": 170_000, "max": 220_000},
}

# Мультипликаторы по скиллам — применяются к медианной зарплате уровня
SKILL_MULTIPLIERS: dict[str, float] = {
    "machine_learning": 1.15,
    "deep_learning": 1.15,
    "llm": 1.18,
    "cloud_aws": 1.12,
    "cloud_azure": 1.10,
    "cloud_gcp": 1.10,
    "kubernetes": 1.08,
    "data_engineering": 1.10,
    "golang": 1.07,
    "rust": 1.06,
    "python": 1.05,
    "typescript": 1.04,
    "react": 1.02,
    "java": 1.00,
    "dotnet": 1.00,
    "sql": 0.98,
    "php": 0.92,
    "wordpress": 0.85,
}

# Мультипликаторы по индустрии/домену
DOMAIN_MULTIPLIERS: dict[str, float] = {
    "fintech": 1.18,
    "banking": 1.15,
    "saas": 1.10,
    "cybersecurity": 1.12,
    "gaming": 1.05,
    "ecommerce": 1.00,
    "healthcare": 1.02,
    "consulting": 0.95,
    "agency": 0.90,
    "public_sector": 0.85,
}


@lru_cache(maxsize=None)
def get_salary_range(level: str) -> dict[str, int]:
    """Возвращает диапазон зарплат для уровня сениорити."""
    return CZ_SALARY_RANGES.get(level, CZ_SALARY_RANGES["mid"])


def get_top_skill_multiplier(skills: list[str]) -> float:
    """Возвращает наибольший мультипликатор из списка скиллов кандидата."""
    multipliers = [
        SKILL_MULTIPLIERS[s.lower().replace(" ", "_")]
        for s in skills
        if s.lower().replace(" ", "_") in SKILL_MULTIPLIERS
    ]
    return max(multipliers, default=1.0)
