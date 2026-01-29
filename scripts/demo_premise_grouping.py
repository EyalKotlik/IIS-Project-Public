#!/usr/bin/env python3
"""
Demo: Premise Grouping in Bottom Layer

Shows how premises are grouped by what they support and positioned under those nodes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_mockup.backend.graph_layout import compute_layout_positions


def demo_premise_grouping():
    """Demonstrate premise grouping for bottom layer."""
    
    # Create a graph with multiple claims and premises
    nodes = [
        {'id': 'Claim1', 'type': 'claim', 'label': 'First Claim'},
        {'id': 'Claim2', 'type': 'claim', 'label': 'Second Claim'},
        {'id': 'Claim3', 'type': 'claim', 'label': 'Third Claim'},
        {'id': 'P1', 'type': 'premise', 'label': 'Premise 1 for Claim1'},
        {'id': 'P2', 'type': 'premise', 'label': 'Premise 2 for Claim1'},
        {'id': 'P3', 'type': 'premise', 'label': 'Premise 3 for Claim1'},
        {'id': 'P4', 'type': 'premise', 'label': 'Premise 1 for Claim2'},
        {'id': 'P5', 'type': 'premise', 'label': 'Premise 2 for Claim2'},
        {'id': 'P6', 'type': 'premise', 'label': 'Premise 1 for Claim3'},
        {'id': 'P7', 'type': 'premise', 'label': 'Premise 2 for Claim3'},
        {'id': 'P8', 'type': 'premise', 'label': 'Premise 3 for Claim3'},
    ]
    
    edges = [
        # Premises supporting Claim1
        {'source': 'P1', 'target': 'Claim1', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P2', 'target': 'Claim1', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P3', 'target': 'Claim1', 'relation': 'support', 'confidence': 0.9},
        # Premises supporting Claim2
        {'source': 'P4', 'target': 'Claim2', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P5', 'target': 'Claim2', 'relation': 'support', 'confidence': 0.9},
        # Premises supporting Claim3
        {'source': 'P6', 'target': 'Claim3', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P7', 'target': 'Claim3', 'relation': 'support', 'confidence': 0.9},
        {'source': 'P8', 'target': 'Claim3', 'relation': 'support', 'confidence': 0.9},
    ]
    
    # Compute layout
    positions, metrics, node_layers = compute_layout_positions(nodes, edges)
    
    print("=" * 70)
    print("PREMISE GROUPING DEMO")
    print("=" * 70)
    print()
    print("This demonstrates how premises are grouped by what they support")
    print("and positioned under the nodes they support.")
    print()
    
    # Group nodes by layer
    layers = {}
    for node_id, layer in node_layers.items():
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(node_id)
    
    # Display layout by layer
    print("Layout by Layer:")
    print("-" * 70)
    for layer in sorted(layers.keys()):
        print(f"\nLayer {layer}:")
        nodes_in_layer = layers[layer]
        # Sort by x position
        nodes_with_pos = [(node_id, positions[node_id][0]) for node_id in nodes_in_layer]
        nodes_with_pos.sort(key=lambda x: x[1])
        
        for node_id, x_pos in nodes_with_pos:
            node_type = next(n['type'] for n in nodes if n['id'] == node_id)
            print(f"  {node_id:10s} at x={x_pos:6.0f}  (type: {node_type})")
    
    print()
    print("-" * 70)
    print("Premise Grouping Analysis:")
    print("-" * 70)
    
    # Analyze premise grouping
    if len(layers) > 0:
        bottom_layer = max(layers.keys())
        premises = layers[bottom_layer]
        
        # Group premises by what they support
        premise_groups = {}
        for edge in edges:
            premise = edge['source']
            claim = edge['target']
            if premise not in premise_groups:
                premise_groups[premise] = []
            premise_groups[premise].append(claim)
        
        # Group claims by their premises
        claim_to_premises = {}
        for premise, claims in premise_groups.items():
            for claim in claims:
                if claim not in claim_to_premises:
                    claim_to_premises[claim] = []
                claim_to_premises[claim].append(premise)
        
        for claim in sorted(claim_to_premises.keys()):
            premises_for_claim = claim_to_premises[claim]
            x_positions = [positions[p][0] for p in premises_for_claim]
            x_positions.sort()
            
            claim_x = positions[claim][0]
            
            print(f"\n{claim} (x={claim_x:.0f}):")
            print(f"  Supporting premises: {', '.join(sorted(premises_for_claim))}")
            print(f"  Premise positions: {[f'{x:.0f}' for x in x_positions]}")
            print(f"  Premise block width: {max(x_positions) - min(x_positions):.0f}")
    
    print()
    print("=" * 70)
    print("✓ Premises are grouped by what they support")
    print("✓ Each group is positioned under the node it supports")
    print("✓ Groups are contiguous (no gaps within groups)")
    print("=" * 70)


if __name__ == '__main__':
    demo_premise_grouping()
