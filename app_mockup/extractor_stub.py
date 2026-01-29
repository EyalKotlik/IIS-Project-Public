"""
Extractor Stub for Argument Graph Builder Mockup

This module provides mock extraction functionality for the UI prototype.
In production, this would be replaced with actual NLP/LLM-based extraction.
"""

import json
import os
import time
import logging
from typing import Optional
from datetime import datetime

# Import preprocessing module
from backend.preprocessing import preprocess_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to sample data
SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")


def get_sample_texts() -> dict:
    """Return available sample texts for the dropdown."""
    return {
        "Death Penalty Argument": "sample_text_1.txt",
        "AI Regulation Argument": "sample_text_2.txt",
        "Conclusion Test": "sample_text_conclusion_test.txt",
    }


def load_sample_text(filename: str) -> str:
    """Load a sample text file."""
    filepath = os.path.join(SAMPLE_DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def load_sample_graph(graph_file: str) -> dict:
    """Load a pre-generated sample graph."""
    filepath = os.path.join(SAMPLE_DATA_DIR, graph_file)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_arguments(text: str, simulate_delay: bool = True) -> dict:
    """
    Mock extraction of argument components from text.
    
    In production, this would:
    1. Use preprocessing to segment sentences and detect discourse markers (IMPLEMENTED)
    2. Use LLM to classify components and determine relations
    3. Apply deterministic graph cleanup and layout
    
    For the mockup, we return a pre-generated sample graph based on text similarity,
    or generate a minimal placeholder graph for custom input.
    
    Args:
        text: Input text to analyze
        simulate_delay: Whether to simulate processing time
        
    Returns:
        Dictionary containing nodes, edges, and metadata
    """
    # STEP 1: Preprocessing (NEW - Real Implementation)
    logger.info("Starting preprocessing stage...")
    preprocessed = preprocess_text(text)
    logger.info(f"Preprocessing complete: {len(preprocessed.sentences)} sentences, "
                f"{preprocessed.metadata.get('candidate_count', 0)} candidates")
    
    if simulate_delay:
        # Simulate additional extraction time (LLM calls, etc.)
        time.sleep(2)
    
    # Check if text matches our samples
    sample_1 = load_sample_text("sample_text_1.txt")
    sample_2 = load_sample_text("sample_text_2.txt")
    
    # Simple matching - in production, this would be actual extraction
    if "conclusion test" in text.lower() or "test conclusion" in text.lower():
        graph = load_sample_graph("sample_graph_conclusion_test.json")
    elif "death penalty" in text.lower() or "capital punishment" in text.lower():
        graph = load_sample_graph("sample_graph_1.json")
    elif "artificial intelligence" in text.lower() or "AI" in text:
        graph = load_sample_graph("sample_graph_2.json")
    else:
        # Generate a placeholder graph for custom input using preprocessing results
        graph = generate_placeholder_graph_from_preprocessing(text, preprocessed)
    
    # Add preprocessing metadata to the graph
    graph["meta"]["preprocessing"] = {
        "sentence_count": len(preprocessed.sentences),
        "candidate_count": preprocessed.metadata.get('candidate_count', 0),
        "paragraph_count": preprocessed.paragraph_count,
        "marker_counts": preprocessed.metadata.get('marker_counts', {})
    }
    
    return graph




def generate_placeholder_graph_from_preprocessing(text: str, preprocessed) -> dict:
    """
    Generate a minimal placeholder graph using preprocessing results.
    This uses the actual candidate sentences detected by preprocessing.
    """
    from backend.preprocessing import get_candidates
    
    candidates = get_candidates(preprocessed)
    
    # If no candidates, fall back to the original method
    if not candidates:
        return generate_placeholder_graph(text)
    
    nodes = []
    edges = []
    
    # Use the first candidate as the main claim
    if len(candidates) > 0:
        main = candidates[0]
        nodes.append({
            "id": "n1",
            "type": "claim",
            "label": main.text[:50] + "..." if len(main.text) > 50 else main.text,
            "span": main.text,
            "paraphrase": "[LLM paraphrase would appear here. Preprocessing detected discourse markers: {}]".format(
                ", ".join([m.marker for m in main.markers]) if main.markers else "none"
            ),
            "confidence": 0.75
        })
    
    # Use remaining candidates as supporting premises
    for idx, candidate in enumerate(candidates[1:5], start=2):  # Up to 4 more nodes
        # Determine type based on discourse markers
        node_type = "premise"
        if candidate.markers:
            # Check marker types to infer node type
            marker_types = {m.signal_type for m in candidate.markers}
            if 'ATTACK_CUE' in marker_types:
                node_type = "objection"
            elif 'SUPPORT_CUE' in marker_types:
                node_type = "premise"
            elif 'ELAB_CUE' in marker_types:
                node_type = "other"
        
        nodes.append({
            "id": f"n{idx}",
            "type": node_type,
            "label": candidate.text[:50] + "..." if len(candidate.text) > 50 else candidate.text,
            "span": candidate.text,
            "paraphrase": "[LLM paraphrase would appear here. Discourse markers: {}]".format(
                ", ".join([m.marker for m in candidate.markers]) if candidate.markers else "none"
            ),
            "confidence": 0.65
        })
        
        # Add edge based on marker type
        relation = "attack" if node_type == "objection" else "support"
        edges.append({
            "source": f"n{idx}",
            "target": "n1",
            "relation": relation,
            "confidence": 0.60
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "source": "user_input_with_preprocessing",
            "created_at": datetime.now().isoformat(),
            "model_version": "mock-v1.1-with-preprocessing",
            "note": "This graph was generated using real preprocessing (sentence segmentation + discourse markers)."
        }
    }


def generate_placeholder_graph(text: str) -> dict:
    """
    Generate a minimal placeholder graph for custom input text.
    This demonstrates the UI even with arbitrary input.
    """
    # Extract first sentence as main claim
    sentences = text.replace("\n", " ").split(".")
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        sentences = ["No meaningful content detected"]
    
    nodes = [
        {
            "id": "n1",
            "type": "claim",
            "label": sentences[0][:50] + "..." if len(sentences[0]) > 50 else sentences[0],
            "span": sentences[0] + "." if sentences else "N/A",
            "paraphrase": "[LLM paraphrase would appear here]",
            "confidence": 0.75
        }
    ]
    
    edges = []
    
    # Add supporting premises from subsequent sentences
    for i, sent in enumerate(sentences[1:4], start=2):  # Up to 3 more nodes
        if len(sent) > 10:  # Only meaningful sentences
            nodes.append({
                "id": f"n{i}",
                "type": "premise" if i <= 3 else "other",
                "label": sent[:50] + "..." if len(sent) > 50 else sent,
                "span": sent + ".",
                "paraphrase": "[LLM paraphrase would appear here]",
                "confidence": 0.65
            })
            edges.append({
                "source": f"n{i}",
                "target": "n1",
                "relation": "support",
                "confidence": 0.60
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "source": "user_input",
            "created_at": datetime.now().isoformat(),
            "model_version": "mock-v1.0",
            "note": "This is a placeholder extraction. Full extraction requires the production backend."
        }
    }


def get_mock_qa_answer(question: str, node_ids: list, graph_data: dict) -> dict:
    """
    Generate a mock answer for the Q&A feature.
    
    In production, this would:
    1. Retrieve relevant nodes and their contexts
    2. Use LLM to generate an answer grounded in the source material
    3. Return source spans used for attribution
    
    Args:
        question: User's natural language question
        node_ids: IDs of selected nodes
        graph_data: Full graph data for context
        
    Returns:
        Dictionary with answer and supporting information
    """
    # Find selected nodes
    selected_nodes = [n for n in graph_data["nodes"] if n["id"] in node_ids]
    
    if not selected_nodes:
        return {
            "answer": "Please select at least one node to ask questions about.",
            "confidence": 0.0,
            "sources": [],
            "explanation": "No nodes selected."
        }
    
    # Generate mock answer based on node types and question
    node_labels = [n["label"] for n in selected_nodes]
    node_types = [n["type"] for n in selected_nodes]
    
    # Craft contextual mock answer
    if "why" in question.lower():
        answer = f"The argument about '{node_labels[0]}' is supported by the following reasoning: "
        answer += "The author presents this as a key point in their overall argument structure. "
        answer += "This connects to other elements in the argument graph through logical relationships."
    elif "how" in question.lower():
        answer = f"The node '{node_labels[0]}' functions as a {node_types[0]} in the argument. "
        answer += "It connects to other nodes through support and attack relations, "
        answer += "forming part of the overall argumentative structure."
    elif "what" in question.lower():
        answer = f"'{node_labels[0]}' represents a {node_types[0]} in this argument. "
        if len(selected_nodes) > 1:
            answer += f"Together with the other selected nodes, they form a coherent sub-argument."
    else:
        answer = f"Based on the selected node(s), the main point concerns '{node_labels[0]}'. "
        answer += "This element plays a key role in the argument's logical structure."
    
    return {
        "answer": answer,
        "confidence": 0.78,
        "sources": [
            {"node_id": n["id"], "span": n["span"][:100] + "..." if len(n["span"]) > 100 else n["span"]}
            for n in selected_nodes[:3]
        ],
        "explanation": f"This answer was generated based on {len(selected_nodes)} selected node(s) "
                      f"and their relationships in the argument graph. The LLM analyzed the original "
                      f"text spans and their argumentative roles."
    }
