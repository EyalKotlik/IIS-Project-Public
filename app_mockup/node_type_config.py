"""
Node Type Configuration - Single Source of Truth
==================================================

Centralized configuration for node type styling used across:
- Graph rendering (vis-network)
- Legend display
- Node detail panels
- Filters and dropdowns

This ensures consistency and prevents duplicate color mappings.
"""

# Node type definitions with colors and descriptions
NODE_TYPE_CONFIG = {
    "claim": {
        "color": "#3b82f6",      # Blue
        "label": "Claim",
        "description": "Main position or assertion",
    },
    "premise": {
        "color": "#10b981",      # Green
        "label": "Premise",
        "description": "Supporting reason or evidence",
    },
    "objection": {
        "color": "#ef4444",      # Red
        "label": "Objection",
        "description": "Counter-argument or challenge",
    },
    "reply": {
        "color": "#f59e0b",      # Amber
        "label": "Reply",
        "description": "Response to objection",
    },
    "conclusion": {
        "color": "#8b5cf6",      # Purple
        "label": "Conclusion",
        "description": "Final takeaway or inference",
    },
}

# Fallback for unknown node types
FALLBACK_CONFIG = {
    "color": "#6b7280",          # Gray
    "label": "Other",
    "description": "Unrecognized type",
}

# Edge/Arrow relation colors
EDGE_RELATION_CONFIG = {
    "support": {
        "color": "#10b981",      # Green
        "label": "Support",
        "description": "Supports or strengthens",
    },
    "attack": {
        "color": "#ef4444",      # Red
        "label": "Attack",
        "description": "Challenges or opposes",
    },
}


def get_node_color(node_type: str) -> str:
    """
    Get color for a node type.
    
    Args:
        node_type: The node type (e.g., "claim", "premise")
        
    Returns:
        Hex color code (e.g., "#3b82f6")
    """
    config = NODE_TYPE_CONFIG.get(node_type, FALLBACK_CONFIG)
    return config["color"]


def get_node_label(node_type: str) -> str:
    """
    Get human-readable label for a node type.
    
    Args:
        node_type: The node type (e.g., "claim", "premise")
        
    Returns:
        Display label (e.g., "Claim")
    """
    config = NODE_TYPE_CONFIG.get(node_type, FALLBACK_CONFIG)
    return config["label"]


def get_node_description(node_type: str) -> str:
    """
    Get description for a node type.
    
    Args:
        node_type: The node type (e.g., "claim", "premise")
        
    Returns:
        Brief description (e.g., "Main position or assertion")
    """
    config = NODE_TYPE_CONFIG.get(node_type, FALLBACK_CONFIG)
    return config["description"]


def get_all_node_types() -> list:
    """
    Get list of all recognized node types.
    
    Returns:
        List of node type strings (e.g., ["claim", "premise", ...])
    """
    return list(NODE_TYPE_CONFIG.keys())


def get_edge_color(relation: str) -> str:
    """
    Get color for an edge relation.
    
    Args:
        relation: The edge relation type (e.g., "support", "attack")
        
    Returns:
        Hex color code (e.g., "#10b981")
    """
    if relation in EDGE_RELATION_CONFIG:
        return EDGE_RELATION_CONFIG[relation]["color"]
    return "#6b7280"  # Fallback gray


def get_edge_label(relation: str) -> str:
    """
    Get human-readable label for an edge relation.
    
    Args:
        relation: The edge relation type (e.g., "support", "attack")
        
    Returns:
        Display label (e.g., "Support")
    """
    if relation in EDGE_RELATION_CONFIG:
        return EDGE_RELATION_CONFIG[relation]["label"]
    return "Unknown"


def get_edge_description(relation: str) -> str:
    """
    Get description for an edge relation.
    
    Args:
        relation: The edge relation type (e.g., "support", "attack")
        
    Returns:
        Brief description (e.g., "Supports or strengthens")
    """
    if relation in EDGE_RELATION_CONFIG:
        return EDGE_RELATION_CONFIG[relation]["description"]
    return "Unknown relation"


def get_all_edge_relations() -> list:
    """
    Get list of all edge relation types.
    
    Returns:
        List of relation type strings (e.g., ["support", "attack"])
    """
    return list(EDGE_RELATION_CONFIG.keys())


def get_node_config(node_type: str) -> dict:
    """
    Get full configuration for a node type.
    
    Args:
        node_type: The node type
        
    Returns:
        Dictionary with color, label, and description
    """
    return NODE_TYPE_CONFIG.get(node_type, FALLBACK_CONFIG)
