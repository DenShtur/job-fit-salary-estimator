from app.data.salary_data import (
    CZ_SALARY_RANGES,
    get_salary_range,
    get_top_skill_multiplier,
)

EXPECTED_LEVELS = {"intern", "junior", "mid", "senior", "lead", "principal"}


class TestCZSalaryRanges:
    def test_all_levels_present(self):
        assert set(CZ_SALARY_RANGES.keys()) == EXPECTED_LEVELS

    def test_each_level_has_required_keys(self):
        for level, data in CZ_SALARY_RANGES.items():
            assert "min" in data, f"{level} missing 'min'"
            assert "median" in data, f"{level} missing 'median'"
            assert "max" in data, f"{level} missing 'max'"

    def test_ranges_are_ordered(self):
        for level, data in CZ_SALARY_RANGES.items():
            assert data["min"] <= data["median"] <= data["max"], (
                f"{level}: min={data['min']} median={data['median']} max={data['max']}"
            )

    def test_seniority_increases_with_level(self):
        levels = ["intern", "junior", "mid", "senior", "lead", "principal"]
        medians = [CZ_SALARY_RANGES[l]["median"] for l in levels]
        assert medians == sorted(medians), "Medians should increase with seniority"


class TestGetSalaryRange:
    def test_senior_returns_correct_range(self):
        result = get_salary_range("senior")
        assert result["min"] == 85_000
        assert result["median"] == 110_000
        assert result["max"] == 145_000

    def test_unknown_level_returns_mid(self):
        result = get_salary_range("unknown_level")
        assert result == CZ_SALARY_RANGES["mid"]


class TestGetTopSkillMultiplier:
    def test_llm_skill_returns_highest(self):
        result = get_top_skill_multiplier(["python", "llm"])
        assert result == 1.18

    def test_single_python_skill(self):
        result = get_top_skill_multiplier(["python"])
        assert result == 1.05

    def test_empty_list_returns_one(self):
        result = get_top_skill_multiplier([])
        assert result == 1.0

    def test_unknown_skills_return_one(self):
        result = get_top_skill_multiplier(["cobol", "fortran"])
        assert result == 1.0

    def test_case_insensitive(self):
        result = get_top_skill_multiplier(["Python"])
        assert result == 1.05
