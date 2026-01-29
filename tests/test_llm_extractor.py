"""
Unit Tests for LLM Extractor Module
====================================

Tests for the enhanced llm_extractor.py with:
- Conclusion node type support
- 2-call extraction (classification + relations)
- Post-processing validation and repair
- Connectivity checking

All tests use mocked responses (no real API calls).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app_mockup'))

from llm_extractor import (
    GraphNode,
    GraphEdge,
    _validate_and_repair_edges,
    _compute_connected_components,
    _repair_connectivity,
    _format_candidates_for_llm,
)


# ============================================================================
# Test Data
# ============================================================================

SAMPLE_TEXT = """The death penalty is wrong. This is because it violates human rights. 
Therefore, we must abolish capital punishment."""


# ============================================================================
# Schema Tests
# ============================================================================

@pytest.mark.unit
class TestSchemas:
    """Tests for Pydantic schemas."""
    
    def test_graph_node_accepts_conclusion(self):
        """Test that GraphNode schema accepts 'conclusion' type."""
        node = GraphNode(
            id="n1",
            type="conclusion",
            label="Must abolish death penalty",
            span="Therefore, we must abolish capital punishment.",
            paraphrase="We should end capital punishment",
            confidence=0.9
        )
        assert node.type == "conclusion"
        assert node.id == "n1"
    
    def test_graph_node_accepts_all_types(self):
        """Test that GraphNode accepts all valid types."""
        valid_types = ["claim", "premise", "objection", "reply", "conclusion"]
        
        for node_type in valid_types:
            node = GraphNode(
                id=f"n_{node_type}",
                type=node_type,
                label="Test",
                span="Test text",
                paraphrase="Test paraphrase",
                confidence=0.8
            )
            assert node.type == node_type
    
    def test_graph_node_rejects_other_type(self):
        """Test that GraphNode rejects 'other' type (removed)."""
        with pytest.raises(Exception):  # Pydantic validation error
            GraphNode(
                id="n1",
                type="other",  # Should be rejected
                label="Test",
                span="Test text",
                paraphrase="Test paraphrase",
                confidence=0.8
            )
    
    def test_graph_edge_schema(self):
        """Test GraphEdge schema."""
        edge = GraphEdge(
            source="n1",
            target="n2",
            relation="support",
            confidence=0.85
        )
        assert edge.source == "n1"
        assert edge.target == "n2"
        assert edge.relation == "support"


# ============================================================================
# Validation Tests
# ============================================================================

@pytest.mark.unit
class TestValidation:
    """Tests for edge validation and repair."""
    
    def test_validate_drops_missing_endpoints(self):
        """Test that edges with missing endpoints are dropped."""
        nodes = [
            GraphNode(id="n1", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n2", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
        ]
        
        edges = [
            GraphEdge(source="n1", target="n2", relation="support", confidence=0.8),
            GraphEdge(source="n1", target="n99", relation="support", confidence=0.8),  # n99 missing
            GraphEdge(source="n99", target="n2", relation="attack", confidence=0.8),  # n99 missing
        ]
        
        valid_edges = _validate_and_repair_edges(nodes, edges)
        
        assert len(valid_edges) == 1
        assert valid_edges[0].source == "n1"
        assert valid_edges[0].target == "n2"
    
    def test_validate_drops_self_loops(self):
        """Test that self-loops are dropped."""
        nodes = [
            GraphNode(id="n1", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
        ]
        
        edges = [
            GraphEdge(source="n1", target="n1", relation="support", confidence=0.8),  # Self-loop
        ]
        
        valid_edges = _validate_and_repair_edges(nodes, edges)
        
        assert len(valid_edges) == 0
    
    def test_validate_enforces_conclusion_constraint(self):
        """Test that conclusion constraint is enforced."""
        nodes = [
            GraphNode(id="n1", type="conclusion", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n2", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n3", type="conclusion", label="Test", span="Test", paraphrase="Test", confidence=0.9),
        ]
        
        edges = [
            GraphEdge(source="n1", target="n2", relation="support", confidence=0.8),  # Invalid: conclusion -> claim
            GraphEdge(source="n2", target="n1", relation="support", confidence=0.8),  # Valid: claim -> conclusion
            GraphEdge(source="n1", target="n3", relation="support", confidence=0.8),  # Valid: conclusion -> conclusion
        ]
        
        valid_edges = _validate_and_repair_edges(nodes, edges)
        
        # Should keep only valid edges
        assert len(valid_edges) == 2
        
        # Check that conclusion -> claim was dropped
        for edge in valid_edges:
            if edge.source == "n1":
                assert edge.target == "n3"  # Only conclusion -> conclusion allowed
    
    def test_validate_allows_non_conclusion_to_conclusion(self):
        """Test that non-conclusion -> conclusion edges are allowed."""
        nodes = [
            GraphNode(id="n1", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n2", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n3", type="conclusion", label="Test", span="Test", paraphrase="Test", confidence=0.9),
        ]
        
        edges = [
            GraphEdge(source="n1", target="n3", relation="support", confidence=0.8),
            GraphEdge(source="n2", target="n3", relation="support", confidence=0.8),
        ]
        
        valid_edges = _validate_and_repair_edges(nodes, edges)
        
        # Both should be kept
        assert len(valid_edges) == 2


# ============================================================================
# Connectivity Tests
# ============================================================================

@pytest.mark.unit
class TestConnectivity:
    """Tests for connectivity checking and repair."""
    
    def test_compute_connected_components_single(self):
        """Test computing components for fully connected graph."""
        nodes = [
            GraphNode(id="n1", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n2", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n3", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
        ]
        
        edges = [
            GraphEdge(source="n2", target="n1", relation="support", confidence=0.8),
            GraphEdge(source="n3", target="n1", relation="support", confidence=0.8),
        ]
        
        components = _compute_connected_components(nodes, edges)
        
        assert len(components) == 1
        assert len(components[0]) == 3
    
    def test_compute_connected_components_multiple(self):
        """Test computing components for disconnected graph."""
        nodes = [
            GraphNode(id="n1", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n2", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n3", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n4", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
        ]
        
        edges = [
            GraphEdge(source="n2", target="n1", relation="support", confidence=0.8),
            GraphEdge(source="n4", target="n3", relation="support", confidence=0.8),
        ]
        
        components = _compute_connected_components(nodes, edges)
        
        assert len(components) == 2
        assert {len(c) for c in components} == {2, 2}
    
    def test_repair_connectivity_adds_bridges(self):
        """Test that connectivity repair adds bridging edges."""
        nodes = [
            GraphNode(id="n1", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n2", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n3", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n4", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
        ]
        
        # Two disconnected components
        edges = [
            GraphEdge(source="n2", target="n1", relation="support", confidence=0.8),
            GraphEdge(source="n4", target="n3", relation="support", confidence=0.8),
        ]
        
        # Should have 2 components before repair
        components_before = _compute_connected_components(nodes, edges)
        assert len(components_before) == 2
        
        # Repair
        repaired_edges = _repair_connectivity(nodes, edges)
        
        # Should have more edges after repair
        assert len(repaired_edges) > len(edges)
        
        # Should ideally have 1 component (or at least fewer)
        components_after = _compute_connected_components(nodes, repaired_edges)
        assert len(components_after) <= len(components_before)
    
    def test_repair_connectivity_no_op_if_connected(self):
        """Test that repair doesn't modify already connected graph."""
        nodes = [
            GraphNode(id="n1", type="claim", label="Test", span="Test", paraphrase="Test", confidence=0.9),
            GraphNode(id="n2", type="premise", label="Test", span="Test", paraphrase="Test", confidence=0.9),
        ]
        
        edges = [
            GraphEdge(source="n2", target="n1", relation="support", confidence=0.8),
        ]
        
        repaired_edges = _repair_connectivity(nodes, edges)
        
        # Should not add edges if already connected
        assert len(repaired_edges) == len(edges)


# ============================================================================
# Format Tests
# ============================================================================

@pytest.mark.unit
class TestFormatting:
    """Tests for input formatting."""
    
    def test_format_candidates_for_llm(self):
        """Test formatting preprocessed candidates for LLM input."""
        # Create mock preprocessed doc
        from backend.preprocessing import preprocess_text
        
        text = "Death penalty is wrong. This is because it violates human rights."
        preprocessed = preprocess_text(text)
        
        formatted = _format_candidates_for_llm(preprocessed)
        
        # Should contain sentence IDs
        assert "S" in formatted
        assert "p" in formatted  # paragraph markers
        
        # Should contain candidate sentences
        candidates_count = preprocessed.metadata.get('candidate_count', 0)
        if candidates_count > 0:
            # Check format: "S{id} (p{para}): {text}"
            lines = formatted.split("\n")
            assert len(lines) > 0
            
            # Check first line format
            first_line = lines[0]
            assert first_line.startswith("S")
            assert "(p" in first_line
            assert "):" in first_line


# ============================================================================
# Regression Tests
# ============================================================================

@pytest.mark.regression
class TestRegressionBehavior:
    """Regression tests for stable behavior."""
    
    def test_conclusion_constraint_stable(self):
        """Regression test: conclusion constraint always enforced."""
        # This test ensures the conclusion constraint is consistently applied
        nodes = [
            GraphNode(id="c1", type="conclusion", label="Final", span="Text", paraphrase="Para", confidence=0.9),
            GraphNode(id="p1", type="premise", label="Support", span="Text", paraphrase="Para", confidence=0.9),
            GraphNode(id="cl1", type="claim", label="Claim", span="Text", paraphrase="Para", confidence=0.9),
        ]
        
        # Various invalid edges from conclusion
        edges = [
            GraphEdge(source="c1", target="p1", relation="support", confidence=0.8),
            GraphEdge(source="c1", target="cl1", relation="attack", confidence=0.8),
            GraphEdge(source="p1", target="c1", relation="support", confidence=0.8),  # Valid
            GraphEdge(source="cl1", target="c1", relation="support", confidence=0.8),  # Valid
        ]
        
        valid_edges = _validate_and_repair_edges(nodes, edges)
        
        # Only edges TO conclusion should remain
        assert len(valid_edges) == 2
        for edge in valid_edges:
            if edge.source == "c1":
                # This should never happen after validation
                pytest.fail(f"Found invalid edge from conclusion: {edge.source} -> {edge.target}")


# ============================================================================
# Integration Test (Mocked)
# ============================================================================

@pytest.mark.integration
class TestExtractionIntegration:
    """Integration tests with mocked LLM calls."""
    
    @patch('llm_extractor.get_client')
    @patch('llm_extractor.preprocess_text')
    def test_extract_arguments_real_full_flow(self, mock_preprocess, mock_get_client):
        """Test full extraction flow with mocked responses."""
        from llm_extractor import extract_arguments_real
        
        # Mock preprocessing
        from backend.preprocessing import PreprocessedDocument, SentenceUnit
        mock_preprocessed = PreprocessedDocument(
            original_text=SAMPLE_TEXT,
            sentences=[
                SentenceUnit(id="s1", text="The death penalty is wrong.", paragraph_id=0, 
                           start_char=0, end_char=28, markers=[], is_candidate=True),
                SentenceUnit(id="s2", text="This is because it violates human rights.", paragraph_id=0, 
                           start_char=29, end_char=70, markers=[], is_candidate=True),
                SentenceUnit(id="s3", text="Therefore, we must abolish capital punishment.", paragraph_id=0, 
                           start_char=72, end_char=118, markers=[], is_candidate=True),
            ],
            paragraph_count=1,
            metadata={"candidate_count": 3}
        )
        mock_preprocess.return_value = mock_preprocessed
        
        # Mock OpenAI client
        mock_client = Mock()
        
        # Mock classification response (call 1)
        mock_classification_response = Mock()
        mock_classification_response.choices = [Mock()]
        mock_classification_response.choices[0].message.parsed = Mock()
        mock_classification_response.choices[0].message.parsed.nodes = [
            GraphNode(id="Ss1", type="claim", label="Death penalty wrong", span="The death penalty is wrong.", 
                     paraphrase="Capital punishment is immoral", confidence=0.92),
            GraphNode(id="Ss2", type="premise", label="Violates rights", span="This is because it violates human rights.", 
                     paraphrase="Breaks human rights", confidence=0.88),
            GraphNode(id="Ss3", type="conclusion", label="Must abolish", span="Therefore, we must abolish capital punishment.", 
                     paraphrase="Should end capital punishment", confidence=0.90),
        ]
        
        # Mock relation response (call 2)
        mock_relation_response = Mock()
        mock_relation_response.choices = [Mock()]
        mock_relation_response.choices[0].message.parsed = Mock()
        mock_relation_response.choices[0].message.parsed.edges = [
            GraphEdge(source="Ss2", target="Ss1", relation="support", confidence=0.85),
            GraphEdge(source="Ss1", target="Ss3", relation="support", confidence=0.80),
        ]
        
        # Setup client mock to return different responses for each call
        mock_client.beta.chat.completions.parse.side_effect = [
            mock_classification_response,
            mock_relation_response
        ]
        
        mock_get_client.return_value = mock_client
        
        # Run extraction
        result = extract_arguments_real(SAMPLE_TEXT)
        
        # Verify result
        assert result is not None
        assert "nodes" in result
        assert "edges" in result
        assert "meta" in result
        
        # Check nodes
        assert len(result["nodes"]) == 3
        node_types = {node["type"] for node in result["nodes"]}
        assert "conclusion" in node_types
        assert "claim" in node_types
        assert "premise" in node_types
        
        # Check edges
        assert len(result["edges"]) >= 2
        
        # Check metadata
        assert result["meta"]["model_version"] == "gpt-4o-mini"
        assert result["meta"]["source"] == "llm_real"
        
        # Verify LLM was called twice
        assert mock_client.beta.chat.completions.parse.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
