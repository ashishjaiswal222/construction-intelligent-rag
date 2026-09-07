import pytest
from document_refinement.services.layer4_abbreviation_expander import Layer4AbbreviationExpander

class TestLayer4:
    @pytest.fixture
    def layer(self):
        return Layer4AbbreviationExpander()

    def test_expands_rfi_standalone(self, layer):
        text = "Submit the RFI tomorrow"
        repaired, fixes = layer.expand(text)
        assert "Request for Information (RFI)" in repaired

    def test_does_not_expand_rfi_in_code_rfi_023(self, layer):
        text = "See RFI-023 for details"
        repaired, fixes = layer.expand(text)
        assert "Request for Information (RFI)-023" not in repaired
        assert "RFI-023" in repaired

    def test_expands_boq(self, layer):
        text = "Check the BOQ"
        repaired, fixes = layer.expand(text)
        assert "Bill of Quantities (BOQ)" in repaired

    def test_expands_mep(self, layer):
        text = "MEP coordination"
        repaired, fixes = layer.expand(text)
        assert "Mechanical Electrical Plumbing (MEP)" in repaired

    def test_expands_ifc_standalone(self, layer):
        text = "These drawings are IFC"
        repaired, fixes = layer.expand(text)
        assert "Issued for Construction (IFC)" in repaired

    def test_expands_hvac(self, layer):
        text = "HVAC system"
        repaired, fixes = layer.expand(text)
        assert "Heating Ventilation Air Conditioning (HVAC)" in repaired
