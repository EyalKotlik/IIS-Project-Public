"""
Unit tests for the preprocessing pipeline.

Tests cover:
- Sentence segmentation with tricky punctuation
- Discourse marker detection (case, multi-word markers)
- Candidate flagging logic
- Edge cases and error handling
- Negative tests (empty, whitespace, unicode)
- Golden/regression tests with fixed snapshots
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app_mockup.backend.preprocessing import (
    preprocess_text,
    segment_sentences_simple,
    detect_discourse_markers,
    flag_candidate_sentence,
    get_candidates,
    get_sentences_with_markers,
    PreprocessedDocument,
    SentenceUnit,
    DiscourseMarker
)


# ============================================================================
# Sentence Segmentation Tests
# ============================================================================

@pytest.mark.unit
class TestSentenceSegmentation:
    """Test sentence segmentation functionality."""
    
    def test_basic_segmentation(self):
        """Test basic sentence splitting."""
        text = "This is sentence one. This is sentence two. This is sentence three."
        result = segment_sentences_simple(text)
        
        assert len(result) == 3
        assert result[0][0] == "This is sentence one."
        assert result[1][0] == "This is sentence two."
        assert result[2][0] == "This is sentence three."
    
    def test_paragraph_boundaries(self):
        """Test paragraph tracking."""
        text = "Paragraph one sentence one. Paragraph one sentence two.\n\nParagraph two sentence one."
        result = segment_sentences_simple(text)
        
        assert len(result) == 3
        # First two sentences should be in paragraph 0
        assert result[0][3] == 0
        assert result[1][3] == 0
        # Third sentence should be in paragraph 1
        assert result[2][3] == 1
    
    def test_question_marks(self):
        """Test segmentation with question marks."""
        text = "What is this? This is a test. Is this working? Yes it is."
        result = segment_sentences_simple(text)
        
        assert len(result) >= 3
    
    def test_exclamation_marks(self):
        """Test segmentation with exclamation marks."""
        text = "This is exciting! Really exciting! Very cool."
        result = segment_sentences_simple(text)
        
        assert len(result) >= 2
    
    def test_abbreviations(self):
        """Test handling of abbreviations (Dr., Mr., etc.)."""
        text = "Dr. Smith is here. Mr. Jones is there."
        result = segment_sentences_simple(text)
        
        # Should handle abbreviations without breaking sentences
        assert len(result) >= 1
    
    def test_quotes(self):
        """Test sentences with quotes."""
        text = 'He said "this is a test." She replied "yes it is."'
        result = segment_sentences_simple(text)
        
        assert len(result) >= 1
    
    def test_offsets(self):
        """Test that character offsets are correct."""
        text = "First sentence. Second sentence."
        result = segment_sentences_simple(text)
        
        for sent_text, start, end, _ in result:
            # Verify offset correctness
            assert text[start:end] == sent_text
    
    def test_empty_input(self):
        """Test handling of empty input."""
        result = segment_sentences_simple("")
        assert len(result) == 0
        
        result = segment_sentences_simple("   \n\n  ")
        assert len(result) == 0


# ============================================================================
# Discourse Marker Detection Tests
# ============================================================================

@pytest.mark.unit
class TestDiscourseMarkerDetection:
    """Test discourse marker detection."""
    
    def test_support_markers(self):
        """Test detection of support markers."""
        sentence = "This is true because of evidence."
        markers = detect_discourse_markers(sentence)
        
        assert len(markers) == 1
        assert markers[0].marker == "because"
        assert markers[0].signal_type == "SUPPORT_CUE"
    
    def test_attack_markers(self):
        """Test detection of attack/contrast markers."""
        sentence = "This seems true, however there is a problem."
        markers = detect_discourse_markers(sentence)
        
        assert len(markers) == 1
        assert markers[0].marker == "however"
        assert markers[0].signal_type == "ATTACK_CUE"
    
    def test_elab_markers(self):
        """Test detection of elaboration markers."""
        sentence = "This point is important, for example in this case."
        markers = detect_discourse_markers(sentence)
        
        assert len(markers) == 1
        assert markers[0].marker == "for example"
        assert markers[0].signal_type == "ELAB_CUE"
    
    def test_case_insensitive(self):
        """Test that marker detection is case-insensitive."""
        test_cases = [
            "Because this is true.",
            "BECAUSE this is true.",
            "because this is true."
        ]
        
        for sentence in test_cases:
            markers = detect_discourse_markers(sentence)
            assert len(markers) == 1, f"Failed for: {sentence}"
            assert markers[0].marker == "because"
    
    def test_multi_word_markers(self):
        """Test detection of multi-word markers."""
        sentence = "This is correct as a result of the evidence."
        markers = detect_discourse_markers(sentence)
        
        assert len(markers) == 1
        assert markers[0].marker == "as a result"
        assert markers[0].signal_type == "SUPPORT_CUE"
    
    def test_multiple_markers(self):
        """Test detection of multiple markers in one sentence."""
        sentence = "Because of this, however, we must reconsider."
        markers = detect_discourse_markers(sentence)
        
        assert len(markers) == 2
        marker_texts = {m.marker for m in markers}
        assert "because" in marker_texts
        assert "however" in marker_texts
    
    def test_punctuation_tolerance(self):
        """Test that markers are detected despite punctuation."""
        test_cases = [
            "However, this is wrong.",
            "However this is wrong.",
            "However; this is wrong."
        ]
        
        for sentence in test_cases:
            markers = detect_discourse_markers(sentence)
            assert len(markers) >= 1, f"Failed for: {sentence}"
    
    def test_no_markers(self):
        """Test sentence with no discourse markers."""
        sentence = "This is a simple statement with no special markers."
        markers = detect_discourse_markers(sentence)
        
        assert len(markers) == 0
    
    def test_word_boundary(self):
        """Test that markers respect word boundaries."""
        # "as" is not a marker on its own, only "as a result"
        sentence = "This is as simple as it gets."
        markers = detect_discourse_markers(sentence)
        
        # Should not detect "as" alone
        assert len(markers) == 0


# ============================================================================
# Candidate Flagging Tests
# ============================================================================

@pytest.mark.unit
class TestCandidateFlagging:
    """Test candidate sentence flagging logic."""
    
    def test_candidate_with_marker(self):
        """Test that sentences with markers are flagged as candidates."""
        sentence = "This is true because of the evidence we have."
        markers = detect_discourse_markers(sentence)
        is_candidate, reasons = flag_candidate_sentence(sentence, markers)
        
        assert is_candidate
        assert "has_1_discourse_markers" in reasons
    
    def test_too_short(self):
        """Test that very short sentences are not candidates."""
        sentence = "Yes."
        markers = detect_discourse_markers(sentence)
        is_candidate, reasons = flag_candidate_sentence(sentence, markers)
        
        assert not is_candidate
        assert "too_short" in reasons
    
    def test_too_long(self):
        """Test that extremely long sentences are not candidates."""
        sentence = "This is a very long sentence. " * 50  # Very long
        markers = detect_discourse_markers(sentence)
        is_candidate, reasons = flag_candidate_sentence(sentence, markers)
        
        assert not is_candidate
        assert "too_long" in reasons
    
    def test_sufficient_length_with_verb(self):
        """Test that sentences with verbs and sufficient length are candidates."""
        sentence = "This argument is very compelling and has strong support."
        markers = detect_discourse_markers(sentence)
        is_candidate, reasons = flag_candidate_sentence(sentence, markers)
        
        # Should be a candidate due to verb + length
        assert is_candidate
    
    def test_no_verb_pattern(self):
        """Test handling of sentences without clear verb patterns."""
        sentence = "Simple short text."
        markers = detect_discourse_markers(sentence)
        is_candidate, reasons = flag_candidate_sentence(sentence, markers)
        
        # Might not be a candidate without markers or verbs
        # This is expected behavior
        pass  # Just ensure it doesn't crash


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestPreprocessingIntegration:
    """Test the complete preprocessing pipeline."""
    
    def test_basic_preprocessing(self):
        """Test basic preprocessing workflow."""
        text = "Death penalty is wrong. This is because it violates human rights. However, some argue it deters crime."
        
        doc = preprocess_text(text)
        
        assert isinstance(doc, PreprocessedDocument)
        assert doc.original_text == text
        assert len(doc.sentences) > 0
        assert doc.paragraph_count > 0
    
    def test_multi_paragraph(self):
        """Test preprocessing with multiple paragraphs."""
        text = """First paragraph sentence one. First paragraph sentence two.

Second paragraph sentence one. Second paragraph sentence two."""
        
        doc = preprocess_text(text)
        
        assert doc.paragraph_count >= 2
        assert len(doc.sentences) > 2
        
        # Check that different paragraphs are tracked
        para_ids = {s.paragraph_id for s in doc.sentences}
        assert len(para_ids) > 1
    
    def test_sentence_ids(self):
        """Test that sentence IDs are stable and unique."""
        text = "Sentence one. Sentence two. Sentence three."
        
        doc = preprocess_text(text)
        
        ids = [s.id for s in doc.sentences]
        assert len(ids) == len(set(ids))  # All unique
        assert ids[0] == "s1"
        assert ids[1] == "s2"
    
    def test_discourse_marker_detection_integration(self):
        """Test that discourse markers are detected in the full pipeline."""
        text = "This is true because of evidence. However, there are objections."
        
        doc = preprocess_text(text)
        
        # Check that markers were detected
        total_markers = sum(len(s.markers) for s in doc.sentences)
        assert total_markers > 0
        
        # Check metadata
        assert 'marker_counts' in doc.metadata
    
    def test_candidate_flagging_integration(self):
        """Test that candidates are flagged in the full pipeline."""
        text = "Death penalty is wrong because it is irreversible. This violates human rights."
        
        doc = preprocess_text(text)
        
        # Should have some candidates
        candidates = get_candidates(doc)
        assert len(candidates) > 0
        
        # Check metadata
        assert 'candidate_count' in doc.metadata
        assert doc.metadata['candidate_count'] == len(candidates)
    
    def test_empty_input(self):
        """Test preprocessing with empty input."""
        doc = preprocess_text("")
        
        assert len(doc.sentences) == 0
        assert doc.paragraph_count == 0
        assert 'error' in doc.metadata
    
    def test_whitespace_only(self):
        """Test preprocessing with whitespace-only input."""
        doc = preprocess_text("   \n\n  \t  ")
        
        assert len(doc.sentences) == 0


# ============================================================================
# Utility Function Tests
# ============================================================================

@pytest.mark.unit
class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_get_candidates(self):
        """Test extracting candidate sentences."""
        text = "This is because of evidence. However there are issues. Simple statement."
        doc = preprocess_text(text)
        
        candidates = get_candidates(doc)
        
        # All candidates should have is_candidate=True
        for sent in candidates:
            assert sent.is_candidate
    
    def test_get_sentences_with_markers(self):
        """Test filtering sentences by marker presence."""
        text = "This is because of evidence. However there are issues. Simple statement."
        doc = preprocess_text(text)
        
        marked_sentences = get_sentences_with_markers(doc)
        
        # All should have markers
        for sent in marked_sentences:
            assert len(sent.markers) > 0
    
    def test_get_sentences_with_specific_marker_type(self):
        """Test filtering by specific marker type."""
        text = "This is because of evidence. However there are issues."
        doc = preprocess_text(text)
        
        support_sentences = get_sentences_with_markers(doc, signal_type='SUPPORT_CUE')
        attack_sentences = get_sentences_with_markers(doc, signal_type='ATTACK_CUE')
        
        assert len(support_sentences) > 0
        assert len(attack_sentences) > 0


# ============================================================================
# Real-World Example Tests
# ============================================================================

@pytest.mark.integration
class TestRealWorldExamples:
    """Test with realistic argumentative text examples."""
    
    def test_death_penalty_argument(self):
        """Test with death penalty argument."""
        text = """The death penalty should be abolished. This is because it violates the fundamental right to life. 
        
        However, some argue that it serves as a deterrent to serious crimes. Nevertheless, studies show no conclusive evidence for this claim.
        
        In fact, many innocent people have been executed. Therefore, we must end this practice."""
        
        doc = preprocess_text(text)
        
        # Should detect multiple paragraphs
        assert doc.paragraph_count >= 2
        
        # Should detect multiple sentences
        assert len(doc.sentences) > 3
        
        # Should detect discourse markers
        total_markers = sum(len(s.markers) for s in doc.sentences)
        assert total_markers > 3
        
        # Should have candidates
        candidates = get_candidates(doc)
        assert len(candidates) > 0
    
    def test_ai_regulation_argument(self):
        """Test with AI regulation argument."""
        text = """Artificial intelligence must be regulated. Since AI systems can make consequential decisions, oversight is necessary.
        
        On the other hand, excessive regulation might stifle innovation. Yet, the risks of unregulated AI are too great."""
        
        doc = preprocess_text(text)
        
        # Should process successfully
        assert len(doc.sentences) > 2
        
        # Should detect support and attack markers
        support_sents = get_sentences_with_markers(doc, 'SUPPORT_CUE')
        attack_sents = get_sentences_with_markers(doc, 'ATTACK_CUE')
        
        assert len(support_sents) + len(attack_sents) > 0


# ============================================================================
# Negative Tests (Edge Cases)
# ============================================================================

@pytest.mark.negative
class TestNegativeCases:
    """Test edge cases and negative scenarios."""
    
    def test_unicode_punctuation(self):
        """Test handling of unicode punctuation."""
        text = "This is a test… Another test？Final test！"
        doc = preprocess_text(text)
        
        # Should handle unicode punctuation gracefully
        assert len(doc.sentences) > 0
    
    def test_only_whitespace_variations(self):
        """Test various whitespace-only inputs."""
        test_cases = [
            "",
            " ",
            "   ",
            "\n",
            "\n\n",
            "\t",
            "  \n\n  \t  ",
            "\r\n\r\n"
        ]
        
        for text in test_cases:
            doc = preprocess_text(text)
            assert len(doc.sentences) == 0, f"Failed for: {repr(text)}"
    
    def test_very_long_paragraph(self):
        """Test processing of very long paragraphs."""
        # Create a long paragraph with many sentences
        sentences = [f"This is sentence number {i}." for i in range(100)]
        text = " ".join(sentences)
        
        doc = preprocess_text(text)
        
        # Should process successfully
        assert len(doc.sentences) > 90
        assert doc.paragraph_count >= 1
    
    def test_mixed_newline_types(self):
        """Test handling of mixed newline characters."""
        text = "Paragraph one.\r\n\r\nParagraph two.\n\nParagraph three."
        doc = preprocess_text(text)
        
        # Should detect multiple paragraphs
        assert doc.paragraph_count >= 2
    
    def test_special_characters(self):
        """Test handling of special characters in text."""
        text = "Test with @mentions #hashtags & special chars! Does it work properly?"
        doc = preprocess_text(text)
        
        assert len(doc.sentences) > 0
    
    def test_numbers_and_symbols(self):
        """Test text with numbers and mathematical symbols."""
        text = "The result is 42. We need 100% accuracy. The ratio is 3:1."
        doc = preprocess_text(text)
        
        assert len(doc.sentences) >= 2


# ============================================================================
# Regression Tests (Golden Outputs)
# ============================================================================

@pytest.mark.regression
class TestRegressionGolden:
    """Regression tests with fixed golden outputs."""
    
    def test_golden_example_1(self):
        """Test with fixed golden example 1 - Death penalty argument."""
        text = "The death penalty is wrong. This is because it violates human rights. However, some say it deters crime."
        
        doc = preprocess_text(text)
        
        # Golden assertions - these should remain stable
        assert len(doc.sentences) == 3
        assert doc.paragraph_count == 1
        
        # Check sentence texts
        assert doc.sentences[0].text == "The death penalty is wrong."
        assert doc.sentences[1].text == "This is because it violates human rights."
        assert doc.sentences[2].text == "However, some say it deters crime."
        
        # Check discourse markers
        assert len(doc.sentences[0].markers) == 0
        assert len(doc.sentences[1].markers) == 1
        assert doc.sentences[1].markers[0].marker == "because"
        assert len(doc.sentences[2].markers) == 1
        assert doc.sentences[2].markers[0].marker == "however"
        
        # Check offsets
        assert doc.sentences[0].start_char == 0
        assert doc.sentences[0].end_char == 27
        assert text[0:27] == "The death penalty is wrong."
    
    def test_golden_example_2(self):
        """Test with fixed golden example 2 - Multi-paragraph."""
        text = "First claim here. This is because of evidence.\n\nSecond paragraph. Therefore, we conclude."
        
        doc = preprocess_text(text)
        
        # Golden assertions
        assert len(doc.sentences) == 4
        assert doc.paragraph_count == 2
        
        # Check paragraph IDs
        assert doc.sentences[0].paragraph_id == 0
        assert doc.sentences[1].paragraph_id == 0
        assert doc.sentences[2].paragraph_id == 1
        assert doc.sentences[3].paragraph_id == 1
        
        # Check candidates - at least 1 should be flagged
        candidates = get_candidates(doc)
        assert len(candidates) >= 1
    
    def test_deterministic_behavior(self):
        """Test that preprocessing is deterministic across multiple runs."""
        text = "Because of evidence, this is true. However, there are objections. In fact, we need more research."
        
        # Run preprocessing multiple times
        results = [preprocess_text(text) for _ in range(3)]
        
        # All results should be identical
        for i in range(1, len(results)):
            assert len(results[0].sentences) == len(results[i].sentences)
            assert results[0].paragraph_count == results[i].paragraph_count
            
            for j in range(len(results[0].sentences)):
                s1 = results[0].sentences[j]
                s2 = results[i].sentences[j]
                assert s1.text == s2.text
                assert s1.start_char == s2.start_char
                assert s1.end_char == s2.end_char
                assert s1.is_candidate == s2.is_candidate
                assert len(s1.markers) == len(s2.markers)


# ============================================================================
# spaCy-Specific Tests
# ============================================================================

@pytest.mark.unit
class TestSpacySegmentation:
    """Test spaCy-based sentence segmentation."""
    
    def test_spacy_is_being_used(self):
        """Test that spaCy is actually being used when available."""
        from app_mockup.backend.preprocessing import SPACY_AVAILABLE
        
        if SPACY_AVAILABLE:
            text = "This is a test. Another sentence here."
            doc = preprocess_text(text)
            
            # Should use spaCy engine
            assert doc.metadata['segmentation_engine'] == 'spacy_sentencizer'
            assert doc.metadata['preprocessing_version'] == 'v2.0'
    
    def test_spacy_handles_abbreviations(self):
        """Test that spaCy handles abbreviations correctly."""
        text = "Dr. Smith met Mr. Jones. They discussed Prof. Brown's research."
        doc = preprocess_text(text)
        
        # Should segment correctly despite abbreviations
        assert len(doc.sentences) == 2
        assert doc.sentences[0].text == "Dr. Smith met Mr. Jones."
        assert doc.sentences[1].text == "They discussed Prof. Brown's research."
    
    def test_spacy_handles_decimals(self):
        """Test that spaCy handles decimal numbers correctly."""
        text = "The value is 3.14. Another value is 2.5."
        doc = preprocess_text(text)
        
        # Should not break on decimal points
        assert len(doc.sentences) == 2
        assert "3.14" in doc.sentences[0].text
        assert "2.5" in doc.sentences[1].text
    
    def test_spacy_offset_accuracy(self):
        """Test that spaCy produces accurate character offsets."""
        text = "First sentence here. Second sentence follows. Third one too."
        doc = preprocess_text(text)
        
        # Verify each sentence's offsets point to exact text
        for sent in doc.sentences:
            extracted = text[sent.start_char:sent.end_char]
            assert extracted == sent.text, f"Offset mismatch: '{extracted}' != '{sent.text}'"
    
    def test_spacy_multi_paragraph_offsets(self):
        """Test spaCy with multiple paragraphs maintains correct offsets."""
        text = "Paragraph one sentence one. Paragraph one sentence two.\n\nParagraph two sentence one."
        doc = preprocess_text(text)
        
        # Verify offsets for all sentences
        for sent in doc.sentences:
            extracted = text[sent.start_char:sent.end_char]
            assert extracted == sent.text
        
        # Verify paragraph IDs
        assert doc.sentences[0].paragraph_id == 0
        assert doc.sentences[1].paragraph_id == 0
        assert doc.sentences[2].paragraph_id == 1
    
    def test_spacy_complex_punctuation(self):
        """Test spaCy with complex punctuation scenarios."""
        text = 'He said "this is important." She replied "I agree!" It was decisive.'
        doc = preprocess_text(text)
        
        # Should handle quoted text correctly
        assert len(doc.sentences) >= 2
        
        # Verify offsets
        for sent in doc.sentences:
            extracted = text[sent.start_char:sent.end_char]
            assert extracted == sent.text


@pytest.mark.integration
class TestSpacyFallback:
    """Test fallback behavior when spaCy is unavailable."""
    
    def test_fallback_via_env_variable(self, monkeypatch):
        """Test that fallback works when spaCy is disabled via env variable."""
        # Disable spaCy via environment variable
        monkeypatch.setenv('PREPROCESS_USE_SPACY', 'false')
        
        # Need to reload the module to pick up the new env variable
        import importlib
        from app_mockup.backend import preprocessing
        importlib.reload(preprocessing)
        
        text = "First sentence. Second sentence."
        doc = preprocessing.preprocess_text(text)
        
        # Should use regex fallback
        assert doc.metadata['segmentation_engine'] == 'regex_fallback'
        
        # Reset for other tests
        monkeypatch.setenv('PREPROCESS_USE_SPACY', 'true')
        importlib.reload(preprocessing)
    
    def test_fallback_works_when_needed(self):
        """Test that regex fallback produces valid results."""
        # Directly test the fallback function
        from app_mockup.backend.preprocessing import segment_sentences_simple
        
        text = "First sentence. Second sentence."
        result = segment_sentences_simple(text)
        
        # Should segment correctly
        assert len(result) == 2
        assert result[0][0] == "First sentence."
        assert result[1][0] == "Second sentence."
        
        # Verify offsets are correct
        for sent_text, start, end, para_id in result:
            assert text[start:end] == sent_text


@pytest.mark.regression
class TestSpacyDeterminism:
    """Test that spaCy segmentation is deterministic."""
    
    def test_spacy_deterministic_segmentation(self):
        """Test that spaCy produces consistent results across runs."""
        text = "This is because of evidence. However, there are issues. Therefore, we must act."
        
        # Run preprocessing multiple times
        results = [preprocess_text(text) for _ in range(5)]
        
        # All results should be identical
        for i in range(1, len(results)):
            assert len(results[0].sentences) == len(results[i].sentences)
            
            for j in range(len(results[0].sentences)):
                s1 = results[0].sentences[j]
                s2 = results[i].sentences[j]
                assert s1.text == s2.text
                assert s1.start_char == s2.start_char
                assert s1.end_char == s2.end_char
                assert s1.paragraph_id == s2.paragraph_id
    
    def test_spacy_vs_regex_both_work(self):
        """Test that both spaCy and regex produce valid segmentation."""
        import os
        import importlib
        from app_mockup.backend import preprocessing
        
        text = "Simple sentence one. Simple sentence two."
        
        # Get spaCy result (default)
        doc_spacy = preprocessing.preprocess_text(text)
        
        # Get regex result (by disabling spaCy temporarily)
        old_use_spacy = preprocessing.USE_SPACY
        preprocessing.USE_SPACY = False
        doc_regex = preprocessing.preprocess_text(text)
        preprocessing.USE_SPACY = old_use_spacy
        
        # Both should segment correctly
        assert len(doc_spacy.sentences) == 2
        assert len(doc_regex.sentences) == 2
        
        # Both should have valid offsets
        for sent in doc_spacy.sentences:
            extracted = text[sent.start_char:sent.end_char]
            assert extracted == sent.text
        
        for sent in doc_regex.sentences:
            extracted = text[sent.start_char:sent.end_char]
            assert extracted == sent.text


@pytest.mark.integration
class TestEdgeCasesWithSpacy:
    """Test edge cases specifically with spaCy."""
    
    def test_spacy_with_ellipsis(self):
        """Test spaCy with ellipsis."""
        text = "This is a statement... And another one."
        doc = preprocess_text(text)
        
        # Should handle ellipsis
        assert len(doc.sentences) >= 1
        
        # Verify offsets
        for sent in doc.sentences:
            extracted = text[sent.start_char:sent.end_char]
            assert extracted == sent.text
    
    def test_spacy_with_multiple_blank_lines(self):
        """Test spaCy with multiple blank lines between paragraphs."""
        text = "Paragraph one.\n\n\n\nParagraph two."
        doc = preprocess_text(text)
        
        # Should detect two paragraphs
        assert doc.paragraph_count == 2
        assert doc.sentences[0].paragraph_id == 0
        assert doc.sentences[1].paragraph_id == 1
    
    def test_spacy_with_no_paragraph_breaks(self):
        """Test spaCy with text that has no paragraph breaks."""
        text = "Sentence one. Sentence two. Sentence three."
        doc = preprocess_text(text)
        
        # All sentences should be in the same paragraph
        assert doc.paragraph_count == 1
        for sent in doc.sentences:
            assert sent.paragraph_id == 0
    
    def test_spacy_preserves_whitespace_in_offsets(self):
        """Test that offsets correctly handle various whitespace."""
        text = "First.   Second."  # Multiple spaces
        doc = preprocess_text(text)
        
        # Verify offsets are accurate despite whitespace
        for sent in doc.sentences:
            extracted = text[sent.start_char:sent.end_char]
            assert extracted == sent.text
