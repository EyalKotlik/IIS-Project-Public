"""
Graph Construction Module (Simplified)
======================================

Core data structures for argument graphs:
- GraphNode: represents argument components (claims, premises, objections, etc.)
- GraphEdge: represents relations between components (support, attack)

These classes are used by:
- llm_extractor.py: for converting extraction results to graph format
- synthetic_claims.py: for adding implicit claims to the graph
- premise_clustering.py: for grouping related premises

This simplified version removes the full pipeline-based graph construction
functions that were designed for an alternative extraction approach.
"""

import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Try to import RapidFuzz for text similarity
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


# ============================================================================
# Graph Schema (matches UI format)
# ============================================================================

@dataclass
class GraphNode:
    """
    Graph node matching UI schema.
    
    Schema fields:
    - id: unique node identifier
    - type: component type (claim, premise, objection, reply, conclusion)
    - label: short title/paraphrase
    - span: original text
    - paraphrase: LLM-generated paraphrase (or fallback)
    - confidence: classification confidence
    - is_synthetic: whether this is an LLM-generated synthetic claim
    - source_premise_ids: list of premise node IDs that support this synthetic claim
    - synthesis_method: how the synthetic claim was created (e.g., "llm")
    """
    id: str
    type: str  # claim, premise, objection, reply, conclusion
    label: str  # short title
    span: str  # original text
    paraphrase: str  # LLM paraphrase or fallback
    confidence: float
    
    # Optional provenance metadata (not in UI, but useful)
    sentence_id: Optional[str] = None
    paragraph_id: Optional[int] = None
    
    # Synthetic claim metadata
    is_synthetic: bool = False
    source_premise_ids: Optional[List[str]] = None
    synthesis_method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to UI-compatible dictionary."""
        result = {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "span": self.span,
            "paraphrase": self.paraphrase,
            "confidence": self.confidence,
        }
        # Include synthetic metadata if present
        if self.is_synthetic:
            result["is_synthetic"] = True
            result["source_premise_ids"] = self.source_premise_ids or []
            result["synthesis_method"] = self.synthesis_method
        return result


@dataclass
class GraphEdge:
    """
    Graph edge matching UI schema.
    
    Schema fields:
    - source: source node ID
    - target: target node ID
    - relation: relation type (support, attack)
    - confidence: relation confidence
    """
    source: str
    target: str
    relation: str  # support, attack
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to UI-compatible dictionary."""
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "confidence": self.confidence,
        }
    
    def __hash__(self):
        """Make hashable for deduplication."""
        return hash((self.source, self.target, self.relation))
    
    def __eq__(self, other):
        """Equality check for deduplication."""
        if not isinstance(other, GraphEdge):
            return False
        return (self.source == other.source and 
                self.target == other.target and 
                self.relation == other.relation)


# ============================================================================
# Utility Functions
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for similarity comparison.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text (lowercase, stripped, compressed whitespace)
    """
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)     # Compress whitespace
    return text.strip()


def compute_text_similarity(text1: str, text2: str) -> float:
    """
    Compute similarity between two texts.
    
    Uses RapidFuzz token_sort_ratio if available, otherwise simple Jaccard.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0-1)
    """
    if RAPIDFUZZ_AVAILABLE:
        # Use RapidFuzz token sort ratio (handles word order differences)
        return fuzz.token_sort_ratio(text1, text2) / 100.0
    else:
        # Fallback to simple Jaccard similarity
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0


def generate_node_id(sentence_id: str, text: str) -> str:
    """
    Generate stable, deterministic node ID.
    
    Uses MD5 for fast, non-cryptographic hashing. This is safe for ID generation
    as we don't need cryptographic security (not used for authentication/passwords).
    
    Args:
        sentence_id: Sentence ID
        text: Node text
        
    Returns:
        Stable node ID (e.g., "n_<hash>")
    """
    content = f"{sentence_id}:{text}"
    # MD5 is sufficient for non-cryptographic ID generation
    hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"n_{hash_val}"


def generate_edge_id(source_id: str, target_id: str, relation: str) -> str:
    """
    Generate stable edge ID.
    
    Uses MD5 for fast, non-cryptographic hashing. This is safe for ID generation
    as we don't need cryptographic security (not used for authentication/passwords).
    
    Args:
        source_id: Source node ID
        target_id: Target node ID
        relation: Relation type
        
    Returns:
        Stable edge ID
    """
    content = f"{source_id}:{target_id}:{relation}"
    # MD5 is sufficient for non-cryptographic ID generation
    hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"e_{hash_val}"
