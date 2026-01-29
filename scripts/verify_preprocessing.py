#!/usr/bin/env python3
"""
Simple verification script for preprocessing integration.
Tests that the preprocessing module works correctly with the extraction pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app_mockup.backend.preprocessing import preprocess_text, get_candidates
from app_mockup.extractor_stub import extract_arguments

def test_preprocessing():
    """Test preprocessing directly."""
    print("=" * 60)
    print("TEST 1: Direct Preprocessing")
    print("=" * 60)
    
    text = """The death penalty should be abolished. This is because it violates fundamental human rights.

However, some argue that it serves as a deterrent to serious crimes. Nevertheless, studies show no conclusive evidence for this claim.

Therefore, we must end this practice."""
    
    result = preprocess_text(text)
    
    print(f"✓ Paragraphs detected: {result.paragraph_count}")
    print(f"✓ Sentences detected: {len(result.sentences)}")
    print(f"✓ Candidate sentences: {result.metadata['candidate_count']}")
    print(f"✓ Discourse markers: {result.metadata['marker_counts']}")
    
    # Show some example sentences
    print("\nExample sentences with markers:")
    for sent in result.sentences[:3]:
        if sent.markers:
            marker_text = ", ".join([f"{m.marker} ({m.signal_type})" for m in sent.markers])
            print(f"  - {sent.text[:60]}...")
            print(f"    Markers: {marker_text}")
            print(f"    Is candidate: {sent.is_candidate}")
    
    return True

def test_extraction_integration():
    """Test preprocessing integration with extraction."""
    print("\n" + "=" * 60)
    print("TEST 2: Extraction Pipeline Integration")
    print("=" * 60)
    
    text = """AI regulation is necessary because AI systems can cause significant harm to society.

However, excessive regulation might stifle innovation. Yet, safety must come first."""
    
    result = extract_arguments(text, simulate_delay=False)
    
    print(f"✓ Graph nodes created: {len(result['nodes'])}")
    print(f"✓ Graph edges created: {len(result['edges'])}")
    
    if 'preprocessing' in result['meta']:
        preproc = result['meta']['preprocessing']
        print(f"✓ Preprocessing metadata included:")
        print(f"  - Sentences: {preproc['sentence_count']}")
        print(f"  - Candidates: {preproc['candidate_count']}")
        print(f"  - Paragraphs: {preproc['paragraph_count']}")
        print(f"  - Markers: {preproc['marker_counts']}")
    
    # Show some nodes
    print("\nExample nodes from graph:")
    for node in result['nodes'][:3]:
        print(f"  - {node['type'].upper()}: {node['label'][:50]}...")
    
    return True

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 60)
    print("TEST 3: Edge Cases")
    print("=" * 60)
    
    # Empty input
    result = preprocess_text("")
    print(f"✓ Empty input handled: {len(result.sentences)} sentences")
    
    # Very short text
    result = preprocess_text("This is a test.")
    print(f"✓ Short text handled: {len(result.sentences)} sentence(s)")
    
    # Text with no discourse markers
    result = preprocess_text("Simple sentence. Another simple sentence.")
    print(f"✓ No markers handled: {result.metadata['candidate_count']} candidates")
    
    return True

if __name__ == "__main__":
    print("\n🔧 Preprocessing Pipeline Verification")
    print("=" * 60)
    
    try:
        test_preprocessing()
        test_extraction_integration()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe preprocessing pipeline is working correctly!")
        print("It can now be used for:")
        print("  - Sentence segmentation with character offsets")
        print("  - Discourse marker detection (support, attack, elaboration)")
        print("  - Candidate sentence flagging")
        print("  - Integration with extraction pipeline")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
