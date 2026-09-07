import pytest
from document_indexing.services.text_preprocessor import TextPreprocessor

class TestTextPreprocessor:
    def setup_method(self):
        self.preprocessor = TextPreprocessor()

    def test_expands_rfi_abbreviation(self):
        text = "Please submit the RFI by tomorrow."
        result = self.preprocessor.preprocess(text, "drawing")
        assert "Request for Information RFI" in result

    def test_expands_boq_abbreviation(self):
        text = "Check the BOQ summary"
        result = self.preprocessor.preprocess(text, "boq")
        assert "Bill of Quantities BOQ" in result

    def test_normalises_m3_unit_variants(self):
        for variant in ["10 m3", "10 m³", "10 CUM"]:
            result = self.preprocessor.preprocess(variant, "drawing")
            assert "cubic metres m3" in result

    def test_expands_c35_grade_synonym(self):
        text = "C35 concrete"
        result = self.preprocessor.preprocess(text, "drawing")
        assert "35 N/mm2" in result

    def test_prepends_correct_doc_type_prefix(self):
        result = self.preprocessor.preprocess("content", "contract")
        assert result.startswith("Construction contract legal clause:")

    def test_handles_empty_string_without_raising(self):
        result = self.preprocessor.preprocess("", "drawing")
        assert result == ""

    def test_handles_unknown_doc_type_with_generic_prefix(self):
        result = self.preprocessor.preprocess("content", "unknown_type")
        assert result.startswith("Construction document:")

    def test_multiple_abbreviations_in_same_text(self):
        text = "RFI regarding BOQ item"
        result = self.preprocessor.preprocess(text, "drawing")
        assert "Request for Information RFI" in result
        assert "Bill of Quantities BOQ" in result

    def test_estimate_tokens_returns_int(self):
        result = self.preprocessor.estimate_tokens("hello world")
        assert isinstance(result, int)
        assert result >= 1
