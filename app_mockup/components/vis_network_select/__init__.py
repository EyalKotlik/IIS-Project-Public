"""
Custom Streamlit Component: vis_network_select

A bidirectional Streamlit component that renders a vis-network graph
and returns selected node IDs back to the Python layer via declare_component.
"""

import streamlit.components.v1 as components
import streamlit as st
import os
import json

# Import node type configuration (single source of truth)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from node_type_config import get_node_color, get_edge_color


# Build path to the frontend files
_COMPONENT_PATH = os.path.dirname(os.path.abspath(__file__))

# Declare the component with path to the HTML file
_component_func = components.declare_component(
    "vis_network_select",
    path=_COMPONENT_PATH,
)


def vis_network_select(
    nodes: list,
    edges: list,
    selected_nodes: list = None,
    options: dict = None,
    key: str = None,
    height: int = 550,
    use_server_layout: bool = False,
) -> dict:
    """
    Render an interactive vis-network graph that supports click-to-select.
    
    Clicking nodes in the graph updates selection and returns to Python.
    
    Args:
        nodes: List of node dicts with keys: id, label, type, confidence, etc.
        edges: List of edge dicts with keys: source, target, relation, confidence
        selected_nodes: List of currently selected node IDs (for highlighting)
        options: vis-network options (if None, uses sensible defaults)
        key: Streamlit widget key for state management
        height: Height of the graph in pixels
        use_server_layout: If True, computes layout server-side to minimize crossings
        
    Returns:
        A dict with:
        - "selected": list of selected node IDs
        - "last_clicked": the ID of the last clicked node (or None)
    """
    selected_nodes = selected_nodes or []
    
    # If server-side layout is requested, compute optimized positions
    if use_server_layout:
        from app_mockup.backend.graph_layout import compute_layout_positions, apply_layout_to_nodes
        
        # Compute optimized layout
        positions, metrics, node_layers = compute_layout_positions(nodes, edges)
        
        # Apply positions to nodes
        nodes = apply_layout_to_nodes(nodes, positions)
        
        # Store layout metrics in session state for optional display
        if hasattr(st, 'session_state'):
            st.session_state['graph_layout_metrics'] = metrics
    
    # Default vis-network options matching original PyVis configuration
    if options is None:
        # Choose layout strategy based on server_layout flag
        if use_server_layout:
            # Use fixed positions computed server-side with physics for top layer
            options = {
                "nodes": {
                    "font": {"size": 14, "face": "Inter, sans-serif"},
                    "borderWidth": 2,
                    "borderWidthSelected": 4
                },
                "edges": {
                    "color": {"inherit": False},
                    "smooth": {"type": "cubicBezier", "forceDirection": "vertical"},
                    "arrows": {"to": {"enabled": True, "scaleFactor": 0.8}}
                },
                "physics": {
                    "enabled": True,  # Enable physics for top layer floating
                    "stabilization": {
                        "enabled": True,
                        "iterations": 200  # Fewer iterations since most nodes are fixed
                    },
                    "barnesHut": {
                        "gravitationalConstant": -2000,
                        "centralGravity": 0.1,
                        "springLength": 200,
                        "springConstant": 0.04,
                        "damping": 0.09,
                        "avoidOverlap": 0.5
                    }
                },
                "layout": {
                    "hierarchical": {
                        "enabled": False  # Positions are pre-computed
                    }
                },
                "interaction": {
                    "hover": True,
                    "tooltipDelay": 100,
                    "selectConnectedEdges": True,
                    "multiselect": True
                }
            }
        else:
            # Use client-side hierarchical layout
            options = {
                "nodes": {
                    "font": {"size": 14, "face": "Inter, sans-serif"},
                    "borderWidth": 2,
                    "borderWidthSelected": 4
                },
                "edges": {
                    "color": {"inherit": False},
                    "smooth": {"type": "cubicBezier", "forceDirection": "vertical"},
                    "arrows": {"to": {"enabled": True, "scaleFactor": 0.8}}
                },
                "physics": {
                    "enabled": True,
                    "hierarchicalRepulsion": {
                        "centralGravity": 0.0,
                        "springLength": 200,
                        "springConstant": 0.005,
                        "nodeDistance": 250,
                        "avoidOverlap": 0.5
                    },
                    "solver": "hierarchicalRepulsion",
                    "stabilization": {
                        "enabled": True,
                        "iterations": 1000
                    }
                },
                "layout": {
                    "hierarchical": {
                        "enabled": True,
                        "direction": "UD",
                        "sortMethod": "directed",
                        "levelSeparation": 200,
                        "nodeSpacing": 250,
                        "treeSpacing": 300,
                        "blockShifting": True,
                        "edgeMinimization": True,
                        "parentCentralization": True
                    }
                },
                "interaction": {
                    "hover": True,
                    "tooltipDelay": 100,
                    "selectConnectedEdges": True,
                    "multiselect": True
                }
            }
    
    # Transform nodes to vis-network format
    vis_nodes = []
    for node in nodes:
        is_selected = node["id"] in selected_nodes
        color = get_node_color(node["type"])  # Use shared config
        
        # Truncate label for display
        label = node["label"][:30] + "..." if len(node["label"]) > 30 else node["label"]
        
        # Create tooltip with node details
        title = f"<b>{node['type'].upper()}</b><br><i>{node['label']}</i><br>Confidence: {node['confidence']:.0%}"
        
        vis_node = {
            "id": node["id"],
            "label": label,
            "title": title,
            "color": "#8b5cf6" if is_selected else color,  # Purple if selected
            "size": 30 if node["type"] == "claim" else 25,
            "shape": "box",
            "borderWidth": 4 if is_selected else 2,
            "font": {"size": 12},
            "originalColor": color,
            "nodeType": node["type"],
        }
        
        # Add pre-computed positions if available (server-side layout)
        if "x" in node and "y" in node:
            vis_node["x"] = node["x"]
            vis_node["y"] = node["y"]
            
            # All layers: let x float naturally, fix y to maintain hierarchical structure
            vis_node["fixed"] = {"x": False, "y": True}
        
        vis_nodes.append(vis_node)
    
    # Transform edges to vis-network format
    vis_edges = []
    for edge in edges:
        color = get_edge_color(edge["relation"])  # Use shared config
        
        vis_edges.append({
            "from": edge["source"],
            "to": edge["target"],
            "color": color,
            "title": f"{edge['relation']} ({edge['confidence']:.0%})",
            "dashes": edge["relation"] == "attack",
            "width": 2,
        })
    
    # Call the component and pass data
    component_value = _component_func(
        nodes=vis_nodes,
        edges=vis_edges,
        selected=selected_nodes,
        options=options,
        height=height,
        key=key,
        default={"selected": selected_nodes, "last_clicked": None},
    )
    
    # Return the component value
    if component_value is None:
        return {"selected": selected_nodes, "last_clicked": None}
    
    return component_value

# _get_node_color is now imported from node_type_config.py (single source of truth)
