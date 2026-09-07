import pytest
from unittest.mock import MagicMock
from document_refinement.services.layer5_semantic_validator import Layer5SemanticValidator
from document_refinement.services.providers.groq_provider import GroqRepairProvider
from document_refinement.services.providers.ollama_provider import OllamaRepairProvider

class TestLayer5:
    @pytest.fixture
    def groq_mock(self):
        return MagicMock(spec=GroqRepairProvider)

    @pytest.fixture
    def ollama_mock(self):
        return MagicMock(spec=OllamaRepairProvider)

    @pytest.fixture
    def layer(self, groq_mock, ollama_mock):
        return Layer5SemanticValidator(groq_provider=groq_mock, ollama_provider=ollama_mock)

    def test_should_run_true_heavy_low_quality_contract(self, layer):
        assert layer.should_run('HEAVY', 0.60, 'contract', 500, 0) == True

    def test_should_run_false_light_level(self, layer):
        assert layer.should_run('LIGHT', 0.60, 'contract', 500, 0) == False

    def test_should_run_false_gemini_good_quality(self, layer):
        assert layer.should_run('HEAVY', 0.85, 'contract', 500, 0) == False

    def test_should_run_false_retry_count_above_zero(self, layer):
        assert layer.should_run('HEAVY', 0.60, 'contract', 500, 1) == False

    def test_uses_ollama_when_available(self, layer, groq_mock, ollama_mock):
        text = "A" * 800
        ollama_mock.is_available.return_value = True
        ollama_mock.repair.return_value = "Repaired by Ollama"
        
        repaired, used = layer.repair(text, 'contract', 1)
        
        assert used == True
        assert "Repaired by Ollama" in repaired
        ollama_mock.is_available.assert_called_once()
        ollama_mock.repair.assert_called_once()
        groq_mock.repair.assert_not_called()

    def test_falls_back_to_groq_when_ollama_fails(self, layer, groq_mock, ollama_mock):
        text = "A" * 800
        ollama_mock.is_available.return_value = True
        ollama_mock.repair.side_effect = Exception("Ollama Rate Limit")
        groq_mock.repair.return_value = "Repaired by Groq"
        
        repaired, used = layer.repair(text, 'contract', 1)
        
        assert used == True
        assert "Repaired by Groq" in repaired
        ollama_mock.is_available.assert_called_once()
        ollama_mock.repair.assert_called_once()
        groq_mock.repair.assert_called_once()

    def test_returns_original_when_both_fail(self, layer, groq_mock, ollama_mock):
        text = "A" * 800
        groq_mock.repair.side_effect = Exception("Groq Error")
        ollama_mock.is_available.return_value = True
        ollama_mock.repair.side_effect = Exception("Ollama Error")
        
        repaired, used = layer.repair(text, 'contract', 1)
        
        assert used == False
        assert repaired == text

    def test_ollama_unavailable_skipped_cleanly(self, layer, groq_mock, ollama_mock):
        text = "A" * 800
        groq_mock.repair.side_effect = Exception("Groq Error")
        ollama_mock.is_available.return_value = False
        
        repaired, used = layer.repair(text, 'contract', 1)
        
        assert used == False
        assert repaired == text
        ollama_mock.repair.assert_not_called()

    def test_hallucination_guard_rejects_long_response_from_ollama(self, layer, groq_mock, ollama_mock):
        text = "A" * 800
        groq_mock.repair.side_effect = Exception("Groq Error")
        ollama_mock.is_available.return_value = True
        # response > 1.3 * 800 = 1040 chars
        ollama_mock.repair.return_value = "B" * 1500
        
        repaired, used = layer.repair(text, 'contract', 1)
        
        assert used == False
        assert repaired == text
