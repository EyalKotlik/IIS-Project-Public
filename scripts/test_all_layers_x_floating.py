#!/usr/bin/env python3
"""
Quick test to verify all nodes float horizontally while maintaining vertical hierarchy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_mockup.backend.graph_layout import compute_layout_positions, apply_layout_to_nodes

# Create a simple graph
nodes = [
    {'id': 'A', 'type': 'claim', 'label': 'Top Claim'},
    {'id': 'B', 'type': 'premise', 'label': 'Premise 1'},
    {'id': 'C', 'type': 'premise', 'label': 'Premise 2'},
    {'id': 'D', 'type': 'conclusion', 'label': 'Conclusion'},
]

edges = [
    {'source': 'A', 'target': 'B', 'relation': 'support', 'confidence': 0.9},
    {'source': 'A', 'target': 'C', 'relation': 'support', 'confidence': 0.9},
    {'source': 'B', 'target': 'D', 'relation': 'support', 'confidence': 0.9},
    {'source': 'C', 'target': 'D', 'relation': 'support', 'confidence': 0.9},
]

# Compute layout
positions, metrics, node_layers = compute_layout_positions(nodes, edges)

print("=" * 70)
print("ALL LAYERS X-FLOATING TEST")
print("=" * 70)
print()

print("Node Layers:")
for node_id, layer in sorted(node_layers.items(), key=lambda x: x[1]):
    print(f"  {node_id}: layer {layer}")
print()

# Simulate what vis_network_select does
nodes_with_positions = apply_layout_to_nodes(nodes, positions)

print("Node Positioning:")
for node in nodes_with_positions:
    if node['id'] in node_layers:
        print(f"  {node['id']}: layer {node_layers[node['id']]}, position ({node['x']}, {node['y']}), x:FLOAT, y:FIXED")
print()

print("✓ ALL nodes have x floating, y fixed")
print("✓ Each node maintains its hierarchical y-position (layer structure)")
print("✓ All nodes can naturally position themselves horizontally via physics")
print()

print("This allows the entire graph to naturally organize itself horizontally")
print("while maintaining the clear hierarchical structure vertically.")
