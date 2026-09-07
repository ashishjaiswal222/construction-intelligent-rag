import pytest
from document_refinement.services.layer3_symbol_normalizer import Layer3SymbolNormalizer

class TestLayer3:
    @pytest.fixture
    def layer(self):
        return Layer3SymbolNormalizer()

    def test_normalizes_phi_to_standard(self, layer):
        text = "Rebar φ 10mm"
        repaired, fixes = layer.normalize(text)
        assert "Ø" in repaired

    def test_converts_deg_to_degree_symbol(self, layer):
        text = "Angle is 90 deg."
        repaired, fixes = layer.normalize(text)
        assert "90°" in repaired

    def test_converts_plus_minus(self, layer):
        text = "Tolerance +/- 5mm"
        repaired, fixes = layer.normalize(text)
        assert "±" in repaired

    def test_expands_c35_grade(self, layer):
        text = "Use C35 mix"
        repaired, fixes = layer.normalize(text)
        assert "Grade C35 (35 N/mm² concrete)" in repaired

    def test_expands_fe500_grade(self, layer):
        text = "Steel Fe500"
        repaired, fixes = layer.normalize(text)
        assert "Grade Fe500 rebar (500 N/mm²)" in repaired

    def test_normalizes_n_mm2(self, layer):
        text = "Strength 30 N/mm2"
        repaired, fixes = layer.normalize(text)
        assert "N/mm²" in repaired
