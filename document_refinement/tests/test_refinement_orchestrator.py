import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from document_refinement.services.refinement_orchestrator import RefinementOrchestrator

class TestRefinementOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        layer1 = MagicMock()
        layer1.repair.return_value = ("L1", ["fix1"])
        
        layer2 = MagicMock()
        layer2.correct.return_value = ("L2", ["fix2"])
        
        layer3 = MagicMock()
        layer3.normalize.return_value = ("L3", ["fix3"])
        
        layer4 = MagicMock()
        layer4.expand.return_value = ("L4", ["fix4"])
        
        layer5 = MagicMock()
        layer5.should_run.return_value = True
        layer5.repair.return_value = ("L5", True)
        
        return RefinementOrchestrator(
            layer1=layer1, layer2=layer2, layer3=layer3, layer4=layer4, layer5=layer5, quality_calculator=None
        )

    def test_light_only_runs_l1_l3_l4(self, orchestrator):
        layers = ['structural_repair', 'symbol_normalizer', 'abbreviation_expander']
        orchestrator.refine(uuid4(), "raw", "LIGHT", layers, "doc", 1, 0)
        
        orchestrator.layer1.repair.assert_called()
        orchestrator.layer2.correct.assert_not_called()
        orchestrator.layer3.normalize.assert_called()
        orchestrator.layer4.expand.assert_called()
        orchestrator.layer5.repair.assert_not_called()

    def test_medium_runs_l1_l2_l3_l4(self, orchestrator):
        layers = ['structural_repair', 'ocr_correction', 'symbol_normalizer', 'abbreviation_expander']
        orchestrator.refine(uuid4(), "raw", "MEDIUM", layers, "doc", 1, 0)
        
        orchestrator.layer1.repair.assert_called()
        orchestrator.layer2.correct.assert_called()
        orchestrator.layer3.normalize.assert_called()
        orchestrator.layer4.expand.assert_called()
        orchestrator.layer5.repair.assert_not_called()

    def test_heavy_runs_all_layers(self, orchestrator):
        layers = ['structural_repair', 'ocr_correction', 'symbol_normalizer', 'abbreviation_expander', 'semantic_validator']
        orchestrator.refine(uuid4(), "raw", "HEAVY", layers, "doc", 1, 0)
        
        orchestrator.layer5.should_run.assert_called()
        orchestrator.layer5.repair.assert_called()

    def test_semantic_skipped_if_quality_ok_after_l4(self, orchestrator):
        orchestrator.layer5.should_run.return_value = False
        layers = ['structural_repair', 'ocr_correction', 'symbol_normalizer', 'abbreviation_expander', 'semantic_validator']
        orchestrator.refine(uuid4(), "raw", "HEAVY", layers, "doc", 1, 0)
        
        orchestrator.layer5.should_run.assert_called()
        orchestrator.layer5.repair.assert_not_called()

    def test_raw_text_never_modified_in_result(self, orchestrator):
        res = orchestrator.refine(uuid4(), "raw_text_here", "LIGHT", ['structural_repair'], "doc", 1, 0)
        assert res.raw_text == "raw_text_here"

    def test_needs_human_review_when_quality_below_065(self, orchestrator):
        orchestrator._quality = MagicMock(return_value=0.5)
        res = orchestrator.refine(uuid4(), "raw", "LIGHT", ['structural_repair'], "doc", 1, 0)
        assert res.needs_human_review == True
        assert res.passed_quality_gate == False
