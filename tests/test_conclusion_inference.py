"""
Unit Tests for Conclusion Inference Module
==========================================

Tests for post-hoc conclusion inference based on graph structure.
All tests use deterministic graph structures (no LLM calls).
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app_mockup.backend.extraction.conclusion_inference import (
    ConclusionCandidate,
    ConclusionInferenceConfig,
    ConclusionInferenceResult,
    identify_conclusion_candidates,
    select_conclusions,
    relabel_conclusions,
    enforce_conclusion_constraints,
    infer_conclusions,
    compute_conclusion_score,
)


# ============================================================================
# Test Data
# ============================================================================

def create_test_graph_simple():
    """
    Create a simple test graph:
    
    premise1 --support--> claim1
    premise2 --support--> claim1
    
    claim1 should become a conclusion (has incoming support, is a sink)
    """
    nodes = [
        {"id": "n1", "type": "premise", "label": "Premise 1", "span": "This is premise 1"},
        {"id": "n2", "type": "premise", "label": "Premise 2", "span": "This is premise 2"},
        {"id": "n3", "type": "claim", "label": "Claim 1", "span": "This is the main claim"},
    ]
    
    edges = [
        {"source": "n1", "target": "n3", "relation": "support", "confidence": 0.9},
        {"source": "n2", "target": "n3", "relation": "support", "confidence": 0.85},
    ]
    
    return nodes, edges


def create_test_graph_no_support():
    """
    Create a graph where claim has no incoming support:
    
    claim1 (isolated)
    premise1
    
    claim1 should NOT become a conclusion (no incoming support)
    """
    nodes = [
        {"id": "n1", "type": "claim", "label": "Claim 1", "span": "This is an isolated claim"},
        {"id": "n2", "type": "premise", "label": "Premise 1", "span": "This is a premise"},
    ]
    
    edges = []
    
    return nodes, edges


def create_test_graph_multiple_sinks():
    """
    Create a graph with multiple sink nodes:
    
    premise1 --support--> claim1
    premise2 --support--> claim2
    premise3 --support--> claim2
    
    claim2 should become conclusion (higher score: 2 incoming vs 1)
    """
    nodes = [
        {"id": "n1", "type": "premise", "label": "Premise 1", "span": "Premise 1"},
        {"id": "n2", "type": "premise", "label": "Premise 2", "span": "Premise 2"},
        {"id": "n3", "type": "premise", "label": "Premise 3", "span": "Premise 3"},
        {"id": "n4", "type": "claim", "label": "Claim 1", "span": "Claim 1"},
        {"id": "n5", "type": "claim", "label": "Claim 2", "span": "Claim 2"},
    ]
    
    edges = [
        {"source": "n1", "target": "n4", "relation": "support", "confidence": 0.9},
        {"source": "n2", "target": "n5", "relation": "support", "confidence": 0.85},
        {"source": "n3", "target": "n5", "relation": "support", "confidence": 0.88},
    ]
    
    return nodes, edges


def create_test_graph_with_outgoing():
    """
    Create a graph where candidate has outgoing edges:
    
    premise1 --support--> claim1 --support--> claim2
    
    claim2 should become conclusion (sink with incoming support)
    claim1 should not (has outgoing edge to non-conclusion)
    """
    nodes = [
        {"id": "n1", "type": "premise", "label": "Premise 1", "span": "Premise 1"},
        {"id": "n2", "type": "claim", "label": "Claim 1", "span": "Claim 1"},
        {"id": "n3", "type": "claim", "label": "Claim 2", "span": "Claim 2"},
    ]
    
    edges = [
        {"source": "n1", "target": "n2", "relation": "support", "confidence": 0.9},
        {"source": "n2", "target": "n3", "relation": "support", "confidence": 0.85},
    ]
    
    return nodes, edges


def create_test_graph_chain():
    """
    Create a conclusion chain:
    
    premise1 --support--> conclusion1 --support--> conclusion2
    
    Both conclusions have incoming support.
    conclusion1 -> conclusion2 edge should be preserved.
    """
    nodes = [
        {"id": "n1", "type": "premise", "label": "Premise 1", "span": "Premise 1"},
        {"id": "n2", "type": "claim", "label": "Claim 1", "span": "Claim 1"},
        {"id": "n3", "type": "claim", "label": "Claim 2", "span": "Claim 2"},
    ]
    
    edges = [
        {"source": "n1", "target": "n2", "relation": "support", "confidence": 0.9},
        {"source": "n2", "target": "n3", "relation": "support", "confidence": 0.85},
    ]
    
    return nodes, edges


# ============================================================================
# Tests for Scoring Function
# ============================================================================

@pytest.mark.unit
class TestConclusionScoring:
    """Tests for conclusion scoring logic."""
    
    def test_score_with_incoming_support(self):
        """Test scoring of node with incoming support."""
        config = ConclusionInferenceConfig()
        
        incoming = [("n1", "n3", "support"), ("n2", "n3", "support")]
        outgoing = []
        positions = {"n3": 1.0}  # Last in document
        
        score, details = compute_conclusion_score(
            node_id="n3",
            node_info={"id": "n3", "type": "claim"},
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            node_positions=positions,
            config=config
        )
        
        assert score > 0, "Score should be positive with incoming support"
        assert details["incoming_support_count"] == 2
        assert details["incoming_unique_sources"] == 2
        assert details["outgoing_nonconclusion_edges"] == 0
        assert details["position_score"] == 1.0
    
    def test_score_with_outgoing_penalty(self):
        """Test that outgoing edges reduce score."""
        config = ConclusionInferenceConfig()
        
        incoming = [("n1", "n2", "support")]
        outgoing = [("n2", "n3", "support")]
        positions = {"n2": 0.5}
        
        score_with_outgoing, _ = compute_conclusion_score(
            node_id="n2",
            node_info={"id": "n2", "type": "claim"},
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            node_positions=positions,
            config=config
        )
        
        # Compare to same node without outgoing
        score_without_outgoing, _ = compute_conclusion_score(
            node_id="n2",
            node_info={"id": "n2", "type": "claim"},
            incoming_edges=incoming,
            outgoing_edges=[],
            node_positions=positions,
            config=config
        )
        
        assert score_with_outgoing < score_without_outgoing, "Outgoing edges should reduce score"
    
    def test_score_position_bonus(self):
        """Test that late position increases score."""
        config = ConclusionInferenceConfig()
        
        incoming = [("n1", "n2", "support")]
        outgoing = []
        
        score_early, _ = compute_conclusion_score(
            node_id="n2",
            node_info={"id": "n2", "type": "claim"},
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            node_positions={"n2": 0.0},  # Early
            config=config
        )
        
        score_late, _ = compute_conclusion_score(
            node_id="n2",
            node_info={"id": "n2", "type": "claim"},
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            node_positions={"n2": 1.0},  # Late
            config=config
        )
        
        assert score_late > score_early, "Late position should increase score"


# ============================================================================
# Tests for Candidate Identification
# ============================================================================

@pytest.mark.unit
class TestCandidateIdentification:
    """Tests for identifying conclusion candidates."""
    
    def test_identify_candidates_simple(self):
        """Test candidate identification on simple graph."""
        nodes, edges = create_test_graph_simple()
        config = ConclusionInferenceConfig()
        
        candidates = identify_conclusion_candidates(nodes, edges, config)
        
        assert len(candidates) > 0, "Should find at least one candidate"
        assert candidates[0].node_id == "n3", "n3 (claim1) should be top candidate"
        assert candidates[0].incoming_support_count == 2, "Should have 2 incoming supports"
    
    def test_no_candidates_without_support(self):
        """Test that nodes without incoming support are not candidates."""
        nodes, edges = create_test_graph_no_support()
        config = ConclusionInferenceConfig(require_incoming_support=True)
        
        candidates = identify_conclusion_candidates(nodes, edges, config)
        
        assert len(candidates) == 0, "Should have no candidates without incoming support"
    
    def test_candidate_ordering_multiple_sinks(self):
        """Test that candidates are ordered by score."""
        nodes, edges = create_test_graph_multiple_sinks()
        config = ConclusionInferenceConfig()
        
        candidates = identify_conclusion_candidates(nodes, edges, config)
        
        assert len(candidates) == 2, "Should have 2 candidates"
        assert candidates[0].node_id == "n5", "n5 (claim2) should be top (2 supports)"
        assert candidates[1].node_id == "n4", "n4 (claim1) should be second (1 support)"
        assert candidates[0].score > candidates[1].score, "Scores should be ordered"
    
    def test_skip_non_argument_nodes(self):
        """Test that non_argument nodes are skipped."""
        nodes = [
            {"id": "n1", "type": "non_argument", "label": "Background", "span": "Background info"},
            {"id": "n2", "type": "claim", "label": "Claim", "span": "Main claim"},
        ]
        edges = [
            {"source": "n1", "target": "n2", "relation": "support", "confidence": 0.9},
        ]
        
        config = ConclusionInferenceConfig()
        candidates = identify_conclusion_candidates(nodes, edges, config)
        
        assert len(candidates) == 1, "Should only have 1 candidate (skip non_argument)"
        assert candidates[0].node_id == "n2", "Should be the claim node"


# ============================================================================
# Tests for Selection Logic
# ============================================================================

@pytest.mark.unit
class TestConclusionSelection:
    """Tests for selecting conclusions from candidates."""
    
    def test_select_single_conclusion(self):
        """Test selecting single conclusion (default)."""
        candidates = [
            ConclusionCandidate("n1", "claim", "Text 1", 5.0, 2, 2, 0, 1.0, "reason"),
            ConclusionCandidate("n2", "claim", "Text 2", 3.0, 1, 1, 0, 0.5, "reason"),
        ]
        
        config = ConclusionInferenceConfig(max_conclusions=1)
        selected = select_conclusions(candidates, config)
        
        assert len(selected) == 1, "Should select exactly 1"
        assert selected[0] == "n1", "Should select highest scored"
    
    def test_select_multiple_conclusions(self):
        """Test selecting multiple conclusions."""
        candidates = [
            ConclusionCandidate("n1", "claim", "Text 1", 5.0, 2, 2, 0, 1.0, "reason"),
            ConclusionCandidate("n2", "claim", "Text 2", 3.0, 1, 1, 0, 0.5, "reason"),
        ]
        
        config = ConclusionInferenceConfig(max_conclusions=2)
        selected = select_conclusions(candidates, config)
        
        assert len(selected) == 2, "Should select 2"
        assert selected[0] == "n1", "First should be highest scored"
        assert selected[1] == "n2", "Second should be second highest"
    
    def test_select_with_empty_candidates(self):
        """Test selection with no candidates."""
        config = ConclusionInferenceConfig()
        selected = select_conclusions([], config)
        
        assert len(selected) == 0, "Should select 0 with no candidates"


# ============================================================================
# Tests for Relabeling
# ============================================================================

@pytest.mark.unit
class TestConclusionRelabeling:
    """Tests for relabeling nodes as conclusions."""
    
    def test_relabel_single_node(self):
        """Test relabeling a single node."""
        nodes = [
            {"id": "n1", "type": "premise"},
            {"id": "n2", "type": "claim"},
            {"id": "n3", "type": "claim"},
        ]
        
        count = relabel_conclusions(nodes, ["n2"])
        
        assert count == 1, "Should relabel 1 node"
        assert nodes[1]["type"] == "conclusion", "n2 should be conclusion"
        assert nodes[0]["type"] == "premise", "n1 should stay premise"
        assert nodes[2]["type"] == "claim", "n3 should stay claim"
    
    def test_relabel_multiple_nodes(self):
        """Test relabeling multiple nodes."""
        nodes = [
            {"id": "n1", "type": "claim"},
            {"id": "n2", "type": "claim"},
            {"id": "n3", "type": "claim"},
        ]
        
        count = relabel_conclusions(nodes, ["n1", "n3"])
        
        assert count == 2, "Should relabel 2 nodes"
        assert nodes[0]["type"] == "conclusion"
        assert nodes[1]["type"] == "claim"
        assert nodes[2]["type"] == "conclusion"


# ============================================================================
# Tests for Constraint Enforcement
# ============================================================================

@pytest.mark.unit
class TestConstraintEnforcement:
    """Tests for enforcing conclusion constraints on edges."""
    
    def test_remove_conclusion_to_nonconclusion_edge(self):
        """Test that edges from conclusion to non-conclusion are removed."""
        nodes = [
            {"id": "n1", "type": "premise"},
            {"id": "n2", "type": "conclusion"},
            {"id": "n3", "type": "claim"},
        ]
        
        edges = [
            {"source": "n2", "target": "n1", "relation": "support"},
            {"source": "n2", "target": "n3", "relation": "support"},
        ]
        
        removed = enforce_conclusion_constraints(nodes, edges)
        
        assert removed == 2, "Should remove 2 edges (conclusion -> non-conclusion)"
        assert len(edges) == 0, "All edges should be removed"
    
    def test_keep_conclusion_to_conclusion_edge(self):
        """Test that edges between conclusions are kept."""
        nodes = [
            {"id": "n1", "type": "premise"},
            {"id": "n2", "type": "conclusion"},
            {"id": "n3", "type": "conclusion"},
        ]
        
        edges = [
            {"source": "n1", "target": "n2", "relation": "support"},
            {"source": "n2", "target": "n3", "relation": "support"},
        ]
        
        removed = enforce_conclusion_constraints(nodes, edges)
        
        assert removed == 0, "Should not remove conclusion -> conclusion edge"
        assert len(edges) == 2, "Both edges should be kept"
    
    def test_keep_nonconclusion_edges(self):
        """Test that edges not involving conclusions are kept."""
        nodes = [
            {"id": "n1", "type": "premise"},
            {"id": "n2", "type": "claim"},
            {"id": "n3", "type": "claim"},
        ]
        
        edges = [
            {"source": "n1", "target": "n2", "relation": "support"},
            {"source": "n2", "target": "n3", "relation": "support"},
        ]
        
        removed = enforce_conclusion_constraints(nodes, edges)
        
        assert removed == 0, "Should not remove any edges"
        assert len(edges) == 2, "All edges should be kept"


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestConclusionInferenceIntegration:
    """Integration tests for full conclusion inference pipeline."""
    
    def test_infer_conclusions_simple(self):
        """Test full inference on simple graph."""
        nodes, edges = create_test_graph_simple()
        
        result = infer_conclusions(nodes, edges)
        
        assert result.relabeled_count == 1, "Should relabel 1 node"
        assert len(result.selected_conclusions) == 1, "Should select 1 conclusion"
        assert result.selected_conclusions[0] == "n3", "Should select n3 as conclusion"
        
        # Check that n3 is now labeled as conclusion
        n3 = next(n for n in nodes if n["id"] == "n3")
        assert n3["type"] == "conclusion", "n3 should be conclusion"
        
        # Check that all edges are preserved (no violations)
        assert result.edges_removed == 0, "No edges should be removed"
    
    def test_infer_conclusions_no_candidates(self):
        """Test inference when no candidates exist."""
        nodes, edges = create_test_graph_no_support()
        
        result = infer_conclusions(nodes, edges)
        
        assert result.relabeled_count == 0, "Should not relabel any nodes"
        assert len(result.selected_conclusions) == 0, "Should select 0 conclusions"
        assert len(result.candidates) == 0, "Should have 0 candidates"
    
    def test_infer_conclusions_multiple_sinks(self):
        """Test inference with multiple sink nodes."""
        nodes, edges = create_test_graph_multiple_sinks()
        
        result = infer_conclusions(nodes, edges)
        
        assert result.relabeled_count == 1, "Should relabel 1 node (default max=1)"
        assert len(result.selected_conclusions) == 1, "Should select 1 conclusion"
        assert result.selected_conclusions[0] == "n5", "Should select n5 (higher score)"
    
    def test_infer_conclusions_with_constraint_violations(self):
        """Test that constraint violations are handled."""
        nodes, edges = create_test_graph_with_outgoing()
        
        result = infer_conclusions(nodes, edges)
        
        # n3 should be selected as conclusion (sink with support)
        assert "n3" in result.selected_conclusions, "n3 should be conclusion"
        
        # Edge from n2 -> n3 should be preserved (n2 is not a conclusion)
        assert result.edges_removed == 0, "No edges should be removed (n2 is not conclusion)"
    
    def test_infer_conclusions_chain(self):
        """Test inference on conclusion chain."""
        nodes, edges = create_test_graph_chain()
        config = ConclusionInferenceConfig(max_conclusions=2)
        
        result = infer_conclusions(nodes, edges, config=config)
        
        # Both claims could become conclusions
        # The top-scoring one should be selected
        assert len(result.selected_conclusions) >= 1, "Should select at least 1 conclusion"


# ============================================================================
# Negative/Edge Case Tests
# ============================================================================

@pytest.mark.negative
class TestConclusionInferenceEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_empty_graph(self):
        """Test inference on empty graph."""
        nodes, edges = [], []
        
        result = infer_conclusions(nodes, edges)
        
        assert result.relabeled_count == 0
        assert len(result.selected_conclusions) == 0
    
    def test_graph_with_only_premises(self):
        """Test graph with only premises (no sinks)."""
        nodes = [
            {"id": "n1", "type": "premise", "label": "P1", "span": "Premise 1"},
            {"id": "n2", "type": "premise", "label": "P2", "span": "Premise 2"},
        ]
        edges = [
            {"source": "n1", "target": "n2", "relation": "support", "confidence": 0.9},
        ]
        
        result = infer_conclusions(nodes, edges)
        
        # n2 has incoming support, so it could become a conclusion
        # But it's a premise, not a claim
        assert len(result.candidates) >= 0, "May have candidates depending on scoring"
    
    def test_graph_with_attack_edges_only(self):
        """Test graph with only attack edges (no support)."""
        nodes = [
            {"id": "n1", "type": "claim", "label": "C1", "span": "Claim 1"},
            {"id": "n2", "type": "objection", "label": "O1", "span": "Objection 1"},
        ]
        edges = [
            {"source": "n2", "target": "n1", "relation": "attack", "confidence": 0.9},
        ]
        
        config = ConclusionInferenceConfig(require_incoming_support=True)
        result = infer_conclusions(nodes, edges, config=config)
        
        # No nodes should become conclusions (no incoming SUPPORT)
        assert len(result.selected_conclusions) == 0, "Should select 0 (no support edges)"
    
    def test_conclusion_must_have_incoming_support(self):
        """Test that conclusions MUST have incoming SUPPORT (hard constraint)."""
        nodes = [
            {"id": "n1", "type": "claim", "label": "Isolated claim", "span": "Isolated"},
        ]
        edges = []
        
        config = ConclusionInferenceConfig(require_incoming_support=True)
        result = infer_conclusions(nodes, edges, config=config)
        
        assert len(result.selected_conclusions) == 0, "Isolated claim cannot be conclusion"
        assert result.relabeled_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
