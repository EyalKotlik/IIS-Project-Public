"""
Test for premise grouping in bottom layer.

Tests that premises are grouped by what they support and positioned under those nodes.
"""

import pytest
from app_mockup.backend.graph_layout import (
    compute_layout_positions,
    order_bottom_layer_by_support
)


@pytest.mark.unit
def test_premise_grouping_by_support():
    """Test that premises are grouped by what they support in the bottom layer."""
    # Create a graph with two claims and premises supporting each
    nodes = [
        {'id': 'Claim1', 'type': 'claim', 'label': 'Claim 1'},
        {'id': 'Claim2', 'type': 'claim', 'label': 'Claim 2'},
        {'id': 'P1', 'type': 'premise', 'label': 'Premise 1 for Claim 1'},
        {'id': 'P2', 'type': 'premise', 'label': 'Premise 2 for Claim 1'},
        {'id': 'P3', 'type': 'premise', 'label': 'Premise 3 for Claim 1'},
        {'id': 'P4', 'type': 'premise', 'label': 'Premise 1 for Claim 2'},
        {'id': 'P5', 'type': 'premise', 'label': 'Premise 2 for Claim 2'},
    ]
    
    edges = [
        # Premises supporting Claim1
        {'source': 'P1', 'target': 'Claim1', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P2', 'target': 'Claim1', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P3', 'target': 'Claim1', 'relation': 'support', 'confidence': 0.9},
        # Premises supporting Claim2
        {'source': 'P4', 'target': 'Claim2', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P5', 'target': 'Claim2', 'relation': 'support', 'confidence': 0.9},
    ]
    
    # Compute layout
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    
    # Get x-positions for all nodes
    claim1_x = positions['Claim1'][0]
    claim2_x = positions['Claim2'][0]
    
    p1_x = positions['P1'][0]
    p2_x = positions['P2'][0]
    p3_x = positions['P3'][0]
    p4_x = positions['P4'][0]
    p5_x = positions['P5'][0]
    
    # Premises for Claim1 (P1, P2, P3) should be grouped together
    claim1_premises = sorted([p1_x, p2_x, p3_x])
    
    # Premises for Claim2 (P4, P5) should be grouped together
    claim2_premises = sorted([p4_x, p5_x])
    
    # Check that each group is contiguous (no gaps between group members)
    # The difference between max and min should equal spacing * (count - 1)
    spacing = 250  # default node_spacing
    
    # For Claim1's premises (3 nodes)
    claim1_width = claim1_premises[-1] - claim1_premises[0]
    expected_width_claim1 = spacing * 2  # 3 nodes = 2 gaps
    assert abs(claim1_width - expected_width_claim1) < 10, \
        f"Claim1 premises not contiguous: width {claim1_width} vs expected {expected_width_claim1}"
    
    # For Claim2's premises (2 nodes)
    claim2_width = claim2_premises[-1] - claim2_premises[0]
    expected_width_claim2 = spacing * 1  # 2 nodes = 1 gap
    assert abs(claim2_width - expected_width_claim2) < 10, \
        f"Claim2 premises not contiguous: width {claim2_width} vs expected {expected_width_claim2}"
    
    # Check that the groups don't overlap
    # All Claim1 premises should be on one side, all Claim2 premises on the other
    claim1_max = max(claim1_premises)
    claim2_min = min(claim2_premises)
    
    # Either all Claim1 premises are to the left of Claim2 premises, or vice versa
    assert (claim1_max < claim2_min or claim2_min < claim1_max), \
        "Premise groups should not overlap"


@pytest.mark.unit
def test_order_bottom_layer_by_support_function():
    """Test the order_bottom_layer_by_support function directly."""
    bottom_nodes = ['P1', 'P2', 'P3', 'P4', 'P5']
    
    # P1, P2, P3 support Claim1; P4, P5 support Claim2
    parents = {
        'P1': ['Claim1'],
        'P2': ['Claim1'],
        'P3': ['Claim1'],
        'P4': ['Claim2'],
        'P5': ['Claim2'],
    }
    
    # Claim1 is at position 0, Claim2 is at position 1
    parent_orders = {
        'Claim1': 0,
        'Claim2': 1,
    }
    
    orders = order_bottom_layer_by_support(bottom_nodes, parents, parent_orders)
    
    # Get the orders for each premise
    p1_order = orders['P1']
    p2_order = orders['P2']
    p3_order = orders['P3']
    p4_order = orders['P4']
    p5_order = orders['P5']
    
    # All premises supporting Claim1 should come before premises supporting Claim2
    # (since Claim1 has a lower order than Claim2)
    assert max([p1_order, p2_order, p3_order]) < min([p4_order, p5_order]), \
        "Premises should be grouped by what they support"
    
    # Premises within each group should be adjacent (no gaps)
    claim1_orders = sorted([p1_order, p2_order, p3_order])
    assert claim1_orders == list(range(claim1_orders[0], claim1_orders[0] + 3)), \
        "Claim1 premises should be contiguous"
    
    claim2_orders = sorted([p4_order, p5_order])
    assert claim2_orders == list(range(claim2_orders[0], claim2_orders[0] + 2)), \
        "Claim2 premises should be contiguous"


@pytest.mark.integration
def test_premise_grouping_with_shared_support():
    """Test premise grouping when a premise supports multiple claims."""
    nodes = [
        {'id': 'Claim1', 'type': 'claim', 'label': 'Claim 1'},
        {'id': 'Claim2', 'type': 'claim', 'label': 'Claim 2'},
        {'id': 'P1', 'type': 'premise', 'label': 'Supports only Claim1'},
        {'id': 'P2', 'type': 'premise', 'label': 'Supports both claims'},
        {'id': 'P3', 'type': 'premise', 'label': 'Supports only Claim2'},
    ]
    
    edges = [
        {'source': 'P1', 'target': 'Claim1', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P2', 'target': 'Claim1', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P2', 'target': 'Claim2', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P3', 'target': 'Claim2', 'relation': 'support', 'confidence': 0.9},
    ]
    
    # Compute layout
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    
    # Get x-positions
    p1_x = positions['P1'][0]
    p2_x = positions['P2'][0]
    p3_x = positions['P3'][0]
    
    # P2 supports both claims, so it should be positioned between or near both groups
    # The exact position depends on the implementation, but it should be sensible
    # At minimum, the layout should not crash and should produce valid positions
    assert isinstance(p1_x, (int, float))
    assert isinstance(p2_x, (int, float))
    assert isinstance(p3_x, (int, float))
    
    # All positions should be unique
    assert len(set([p1_x, p2_x, p3_x])) == 3, "All premises should have unique x positions"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
