import pytest
from document_refinement.services.layer2_ocr_correction import Layer2OCRCorrection

class TestLayer2:
    @pytest.fixture
    def layer(self):
        return Layer2OCRCorrection()

    def test_fixes_concrele_to_concrete(self, layer):
        text = "poured concrele here"
        repaired, fixes = layer.repair(text) if hasattr(layer, 'repair') else layer.correct(text)
        assert "concrete" in repaired
        assert "fixed_word_concrete" in fixes

    def test_fixes_digit_l_digit_to_digit_1_digit(self, layer):
        text = "Size is 2l4 mm"
        repaired, fixes = layer.repair(text) if hasattr(layer, 'repair') else layer.correct(text)
        assert "214" in repaired

    def test_fixes_m3_to_unicode(self, layer):
        text = "Volume is 10 m3"
        repaired, fixes = layer.repair(text) if hasattr(layer, 'repair') else layer.correct(text)
        assert "m³" in repaired
        assert "fixed_unit_m³" in fixes

    def test_fixes_il_to_II(self, layer):
        text = "Phase Il building"
        repaired, fixes = layer.repair(text) if hasattr(layer, 'repair') else layer.correct(text)
        assert "Phase II" in repaired

    def test_fixes_specilication(self, layer):
        text = "per specilication"
        repaired, fixes = layer.repair(text) if hasattr(layer, 'repair') else layer.correct(text)
        assert "specification" in repaired
