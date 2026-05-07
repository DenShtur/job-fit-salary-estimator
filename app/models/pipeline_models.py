from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TechSkill(BaseModel):
    name: str
    years_experience: float = Field(ge=0)


class SalaryRange(BaseModel):
    min_czk: int = Field(ge=0)
    median_czk: int = Field(ge=0)
    max_czk: int = Field(ge=0)

    @model_validator(mode="after")
    def check_range_order(self) -> SalaryRange:
        if not (self.min_czk <= self.median_czk <= self.max_czk):
            raise ValueError("Salary range must satisfy min <= median <= max")
        return self


# ── Шаг 1: Извлечение фактов из CV ──────────────────────────────────────────

class CVFacts(BaseModel):
    full_name: str | None = None
    total_years_experience: float = Field(ge=0)
    tech_skills: list[TechSkill]
    soft_skills: list[str]
    education_level: Literal[
        "high_school", "bachelor", "master", "phd", "bootcamp", "self_taught"
    ]
    industries: list[str]
    notable_achievements: list[str]


# ── Шаг 2: Оценка сениорити ─────────────────────────────────────────────────

class SeniorityEvaluation(BaseModel):
    level: Literal["intern", "junior", "mid", "senior", "lead", "principal"]
    score: int = Field(ge=0, le=100)
    reasoning: str
    strengths: list[str]
    weaknesses: list[str]
    confidence: Literal["low", "medium", "high"]
    cv_facts: CVFacts


# ── Шаг 3: Прогноз зарплаты ─────────────────────────────────────────────────

class SalaryEstimate(BaseModel):
    estimated_range: SalaryRange
    market_range_for_level: SalaryRange
    fit_score: int = Field(ge=0, le=100)
    salary_reasoning: str
    top_skills_driving_salary: list[str]
    seniority_eval: SeniorityEvaluation


# ── Шаг 4: Рекомендации для роста на +30% ───────────────────────────────────

class Recommendation(BaseModel):
    action: str
    impact: Literal["low", "medium", "high"]
    timeframe_months: int = Field(ge=1)
    expected_salary_increase_pct: float = Field(ge=0)


class GrowthRecommendations(BaseModel):
    target_salary_czk: int = Field(ge=0)
    recommendations: list[Recommendation] = Field(min_length=3, max_length=5)
    narrative: str
    salary_estimate: SalaryEstimate


# ── Финальный результат API ──────────────────────────────────────────────────

class PipelineResult(BaseModel):
    cv_facts: CVFacts
    seniority: SeniorityEvaluation
    salary: SalaryEstimate
    recommendations: GrowthRecommendations
    processing_time_seconds: float = Field(ge=0)
