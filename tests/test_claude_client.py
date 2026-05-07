from app.utils.claude_client import _clean_raw


class TestCleanRaw:
    def test_strips_json_markdown_block(self):
        raw = '```json\n{"key": "value"}\n```'
        result = _clean_raw(raw)
        assert result == '{"key": "value"}'

    def test_strips_plain_code_block(self):
        raw = '```\n{"key": "value"}\n```'
        result = _clean_raw(raw)
        assert result == '{"key": "value"}'

    def test_extracts_json_with_surrounding_text(self):
        raw = 'Here is the result:\n{"score": 42}\nHope that helps!'
        result = _clean_raw(raw)
        assert result == '{"score": 42}'

    def test_clean_json_unchanged(self):
        raw = '{"name": "Denis", "score": 85}'
        result = _clean_raw(raw)
        assert result == raw

    def test_nested_json_extracted_correctly(self):
        raw = '{"outer": {"inner": "value"}, "count": 1}'
        result = _clean_raw(raw)
        assert result == raw

    def test_json_with_trailing_text(self):
        raw = '{"key": "val"} some extra text after'
        result = _clean_raw(raw)
        assert result == '{"key": "val"}'

    def test_empty_string_returns_empty(self):
        result = _clean_raw("")
        assert result == ""
