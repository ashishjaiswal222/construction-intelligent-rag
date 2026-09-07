import pytest
from document_refinement.services.layer1_structural_repair import Layer1StructuralRepair

class TestLayer1:
    @pytest.fixture
    def layer(self):
        return Layer1StructuralRepair()

    def test_removes_lone_page_number_line(self, layer):
        text = "Some text\n42\nMore text"
        repaired, fixes = layer.repair(text)
        assert "42" not in repaired
        assert "removed_lone_page_number_line" in fixes

    def test_merges_broken_sentence_lowercase_start(self, layer):
        text = "This is a broken\nsentence."
        repaired, fixes = layer.repair(text)
        assert "This is a broken sentence." in repaired
        assert "merged_broken_sentence_lowercase_start" in fixes

    def test_does_not_merge_list_items_starting_with_dash(self, layer):
        text = "List:\n- item 1\n- item 2"
        repaired, fixes = layer.repair(text)
        assert "- item 1\n- item 2" in repaired

    def test_fixes_hyphenated_line_break(self, layer):
        text = "This is a hy-\nphenated word."
        repaired, fixes = layer.repair(text)
        assert "hyphenated word." in repaired
        assert "fixed_hyphenated_line_break" in fixes

    def test_collapses_four_blank_lines_to_two(self, layer):
        text = "Line 1\n\n\n\n\nLine 2"
        repaired, fixes = layer.repair(text)
        assert "Line 1\n\n\nLine 2" in repaired
        assert "collapsed_four_blank_lines_to_two" in fixes

    def test_removes_page_x_of_y_footer(self, layer):
        text = "Content\nPage 1 of 10\nMore content"
        repaired, fixes = layer.repair(text)
        assert "Page 1 of 10" not in repaired
        assert "removed_page_x_of_y_footer" in fixes
