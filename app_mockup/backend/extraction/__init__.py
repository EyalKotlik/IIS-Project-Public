"""
Extraction Module
=================

LLM-based extraction stages for argument mining:
1. Conclusion inference (identifies conclusion nodes)
2. Synthetic claims (generates implicit claims from premise clusters)
3. Premise clustering (groups related premises)
"""

from .conclusion_inference import (
    ConclusionCandidate,
    ConclusionInferenceConfig,
    ConclusionInferenceResult,
    infer_conclusions
)

from .synthetic_claims import (
    SynthesisConfig,
    add_synthetic_claims_to_graph
)

from .premise_clustering import (
    PremiseCluster,
    find_premise_clusters
)

__all__ = [
    # Conclusion inference
    'ConclusionCandidate',
    'ConclusionInferenceConfig',
    'ConclusionInferenceResult',
    'infer_conclusions',
    
    # Synthetic claims
    'SynthesisConfig',
    'add_synthetic_claims_to_graph',
    
    # Premise clustering
    'PremiseCluster',
    'find_premise_clusters',
]
