import pytest
from pydantic import ValidationError

from app.models.pipeline_models import (
    CVFacts,
    GrowthRecommendations,
    Recommendation,
    SalaryEstimate,
    SalaryRange,
    SeniorityEvaluation,
    TechSkill,
)


class TestSalaryRange:
    def test_valid_range(self):
        r = SalaryRange(min_czk=50_000, median_czk=70_000, max_czk=90_000)
        assert r.median_czk == 70_000

    def test_min_greater_than_median_raises(self):
        with pytest.raises(ValidationError):
            SalaryRange(min_czk=80_000, median_czk=70_000, max_czk=90_000)

    def test_median_greater_than_max_raises(self):
        with pytest.raises(ValidationError):
            SalaryRange(min_czk=50_000, median_czk=95_000, max_czk=90_000)

    def test_all_equal_is_valid(self):
        r = SalaryRange(min_czk=70_000, median_czk=70_000, max_czk=70_000)
        assert r.min_czk == r.max_czk


class TestCVFacts:
    def test_all_education_levels_accepted(self):
        levels = ["high_school", "bachelor", "master", "phd", "bootcamp", "self_taught"]
        for level in levels:
            facts = CVFacts(
                total_years_experience=2.0,
                tech_skills=[TechSkill(name="Python", years_experience=2.0)],
                soft_skills=["communication"],
                education_level=level,
                industries=["saas"],
                notable_achievements=[],
            )
            assert facts.education_level == level

    def test_invalid_education_level_raises(self):
        with pytest.raises(ValidationError):
            CVFacts(
                total_years_experience=2.0,
                tech_skills=[],
                soft_skills=[],
                education_level="university",  # invalid
                industries=[],
                notable_achievements=[],
            )

    def test_full_name_optional(self):
        facts = CVFacts(
            total_years_experience=0.0,
            tech_skills=[],
            soft_skills=[],
            education_level="bachelor",
            industries=[],
            notable_achievements=[],
        )
        assert facts.full_name is None


class TestGrowthRecommendations:
    def _make_rec(self, action: str = "Learn Python") -> Recommendation:
        return Recommendation(
            action=action,
            impact="high",
            timeframe_months=6,
            expected_salary_increase_pct=15.0,
        )

    def _make_salary_estimate(self):
        from app.models.pipeline_models import CVFacts, SalaryEstimate, SeniorityEvaluation
        facts = CVFacts(
            total_years_experience=3.0,
            tech_skills=[TechSkill(name="Python", years_experience=3.0)],
            soft_skills=[],
            education_level="bachelor",
            industries=["saas"],
            notable_achievements=[],
        )
        seniority = SeniorityEvaluation(
            level="mid",
            score=55,
            reasoning="Solid mid-level dev",
            strengths=["Python"],
            weaknesses=["cloud"],
            confidence="medium",
            cv_facts=facts,
        )
        return SalaryEstimate(
            estimated_range=SalaryRange(min_czk=55_000, median_czk=70_000, max_czk=90_000),
            market_range_for_level=SalaryRange(min_czk=55_000, median_czk=70_000, max_czk=90_000),
            fit_score=70,
            salary_reasoning="Good fit for Czech market",
            top_skills_driving_salary=["python"],
            seniority_eval=seniority,
        )

    def test_single_recommendation_accepted(self):
        recs = GrowthRecommendations(
            target_salary_czk=90_000,
            recommendations=[self._make_rec()],
            narrative="Short narrative.",
            salary_estimate=self._make_salary_estimate(),
        )
        assert len(recs.recommendations) == 1

    def test_five_recommendations_accepted(self):
        recs = GrowthRecommendations(
            target_salary_czk=90_000,
            recommendations=[self._make_rec(f"Action {i}") for i in range(5)],
            narrative="Narrative.",
            salary_estimate=self._make_salary_estimate(),
        )
        assert len(recs.recommendations) == 5

    def test_six_recommendations_raises(self):
        with pytest.raises(ValidationError):
            GrowthRecommendations(
                target_salary_czk=90_000,
                recommendations=[self._make_rec(f"Action {i}") for i in range(6)],
                narrative="Narrative.",
                salary_estimate=self._make_salary_estimate(),
            )
