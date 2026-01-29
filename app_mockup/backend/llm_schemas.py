"""
Structured Output Schemas for LLM
===================================

Pydantic models for structured outputs from LLM calls.
These ensure that LLM responses are properly validated and typed.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ComponentClassificationResult(BaseModel):
    """Result of classifying an argumentative component."""
    
    sentence_id: str = Field(
        description="ID of the sentence being classified (e.g., 's1', 's2')"
    )
    label: Literal["claim", "premise", "objection", "reply", "non_argument"] = Field(
        description="The type of argumentative component (conclusion will be inferred post-hoc)"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for this classification (0.0 to 1.0)"
    )
    rationale_short: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Brief explanation for the classification (1-2 sentences max)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "sentence_id": "s2",
                "label": "premise",
                "confidence": 0.85,
                "rationale_short": "Contains evidence supporting the main claim"
            }
        }


class RelationExtractionResult(BaseModel):
    """Result of extracting a relation between two components."""
    
    source_id: str = Field(
        description="ID of the source component"
    )
    target_id: str = Field(
        description="ID of the target component"
    )
    relation_type: Literal["support", "attack"] = Field(
        description="Type of relation between components"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for this relation (0.0 to 1.0)"
    )
    rationale_short: Optional[str] = Field(
        default=None,
        description="Brief explanation for why this relation exists"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "s2",
                "target_id": "s1",
                "relation_type": "support",
                "confidence": 0.78,
                "rationale_short": "Provides evidence for the main claim"
            }
        }


class BatchComponentClassification(BaseModel):
    """Batch classification results for multiple components."""
    
    classifications: List[ComponentClassificationResult] = Field(
        description="List of classification results"
    )


class BatchRelationExtraction(BaseModel):
    """Batch relation extraction results."""
    
    relations: List[RelationExtractionResult] = Field(
        description="List of extracted relations"
    )


class ParaphraseResult(BaseModel):
    """Result of paraphrasing an argumentative component."""
    
    sentence_id: str = Field(
        description="ID of the sentence being paraphrased (e.g., 's1', 's2')"
    )
    paraphrase: str = Field(
        max_length=120,
        description="Short paraphrase of the original (≤120 chars or ≤20 words)"
    )
    quality_flags: Optional[List[str]] = Field(
        default=None,
        description="Optional quality flags (e.g., 'TOO_LONG', 'MEANING_DRIFT')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "sentence_id": "s2",
                "paraphrase": "Research strongly backs up this idea.",
                "quality_flags": []
            }
        }


class BatchParaphrase(BaseModel):
    """Batch paraphrase results for multiple components."""
    
    paraphrases: List[ParaphraseResult] = Field(
        description="List of paraphrase results"
    )


class SyntheticClaimResult(BaseModel):
    """Result of synthesizing an intermediate claim from a premise cluster."""
    
    cluster_id: str = Field(
        description="Identifier for the premise cluster"
    )
    synthetic_claim_text: str = Field(
        max_length=150,
        description="Short synthetic claim text (≤20 words preferred, max 150 chars)"
    )
    label: Optional[str] = Field(
        default=None,
        max_length=80,
        description="Optional short label/title (≤10 words)"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the synthesis quality (0.0 to 1.0)"
    )
    coherent: bool = Field(
        description="Whether the premise cluster is coherent enough for synthesis"
    )
    justification: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Brief justification referencing premises (not external knowledge)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cluster_id": "cluster_0",
                "synthetic_claim_text": "Facial recognition can amplify discriminatory policing outcomes.",
                "label": "Discriminatory outcomes",
                "confidence": 0.85,
                "coherent": True,
                "justification": "Synthesizes premises about error rates and biased enforcement."
            }
        }


class BatchSyntheticClaims(BaseModel):
    """Batch synthesis results for multiple premise clusters."""
    
    synthetic_claims: List[SyntheticClaimResult] = Field(
        description="List of synthetic claim results"
    )
