"""
Preprocessing Pipeline for Argument Extraction
================================================

This module provides deterministic text preprocessing for argument mining:
- Sentence segmentation with character offsets and paragraph boundaries
- Discourse marker detection (rule-based, argumentative cues)
- Candidate sentence flagging based on heuristics

The preprocessing stage is backend-only and does not use LLMs.
"""

import re
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# spaCy Import and Configuration
# ============================================================================

# Try to import spaCy
SPACY_AVAILABLE = False
SPACY_NLP = None

try:
    import spacy
    SPACY_AVAILABLE = True
    logger.info("spaCy is available for sentence segmentation")
except ImportError:
    logger.warning("spaCy not available, will use fallback regex segmentation")

# Configuration: Allow disabling spaCy via environment variable
USE_SPACY = os.environ.get('PREPROCESS_USE_SPACY', 'true').lower() in ('true', '1', 'yes')

def _get_spacy_nlp():
    """Get or initialize the spaCy NLP pipeline (lazy loading)."""
    global SPACY_NLP
    if SPACY_NLP is None and SPACY_AVAILABLE:
        try:
            # Use blank English model with sentencizer (no model download needed)
            SPACY_NLP = spacy.blank("en")
            SPACY_NLP.add_pipe("sentencizer")
            logger.info("Initialized spaCy sentencizer for English")
        except Exception as e:
            logger.error(f"Failed to initialize spaCy: {e}")
            return None
    return SPACY_NLP


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class DiscourseMarker:
    """A detected discourse marker in a sentence."""
    marker: str  # The matched marker text
    position: int  # Character offset within the sentence
    signal_type: str  # SUPPORT_CUE, ATTACK_CUE, ELAB_CUE, etc.


@dataclass
class SentenceUnit:
    """A single sentence with metadata for argument mining."""
    id: str  # Stable sentence ID (e.g., "s1", "s2")
    text: str  # The sentence text
    paragraph_id: int  # Paragraph/block index
    start_char: int  # Character offset in original text
    end_char: int  # End character offset in original text
    markers: List[DiscourseMarker] = field(default_factory=list)  # Detected discourse markers
    is_candidate: bool = False  # Whether this is an argument candidate
    candidate_reasons: List[str] = field(default_factory=list)  # Reasons for candidacy


@dataclass
class PreprocessedDocument:
    """The complete preprocessed document."""
    original_text: str  # The original input text
    sentences: List[SentenceUnit]  # List of sentence units
    paragraph_count: int  # Number of paragraphs detected
    metadata: dict = field(default_factory=dict)  # Additional metadata


# ============================================================================
# Discourse Marker Definitions
# ============================================================================

# Define discourse markers by category
# These are case-insensitive and will be matched with word boundaries
DISCOURSE_MARKERS = {
    'SUPPORT_CUE': [
        'because', 'since', 'therefore', 'thus', 'hence',
        'as a result', 'consequently', 'for this reason',
        'given that', 'it follows that', 'this shows that',
        'this means that', 'so', 'accordingly'
    ],
    'ATTACK_CUE': [
        'however', 'but', 'although', 'though', 'nevertheless',
        'nonetheless', 'on the other hand', 'in contrast',
        'conversely', 'yet', 'despite', 'while', 'whereas',
        'on the contrary'
    ],
    'ELAB_CUE': [
        'in fact', 'for example', 'for instance', 'specifically',
        'in particular', 'that is', 'namely', 'i.e.', 'e.g.',
        'in other words', 'to illustrate', 'indeed'
    ]
}


# ============================================================================
# Sentence Segmentation
# ============================================================================

def segment_sentences_spacy(text: str) -> List[Tuple[str, int, int, int]]:
    """
    Segment text into sentences using spaCy with offsets and paragraph boundaries.
    
    This uses spaCy's sentencizer for industrial-grade sentence segmentation while:
    - Preserving paragraph detection (double newline / blank lines)
    - Computing accurate character offsets in the original text
    - Maintaining deterministic paragraph IDs
    
    Args:
        text: The input text to segment
        
    Returns:
        List of tuples: (sentence_text, start_offset, end_offset, paragraph_id)
    """
    nlp = _get_spacy_nlp()
    if nlp is None:
        # Fallback if spaCy initialization failed
        logger.warning("spaCy not available, falling back to regex segmentation")
        return segment_sentences_simple(text)
    
    # First, identify paragraph boundaries (double newline or blank lines)
    # We scan the text to find paragraph spans
    paragraphs = []
    current_para_start = 0
    para_id = 0
    
    # Split by double newline pattern
    paragraph_pattern = r'\n\s*\n'
    para_splits = list(re.finditer(paragraph_pattern, text))
    
    # Build paragraph spans
    for match in para_splits:
        para_end = match.start()
        para_text = text[current_para_start:para_end]
        if para_text.strip():
            paragraphs.append((para_text, current_para_start, para_id))
            para_id += 1
        current_para_start = match.end()
    
    # Don't forget the last paragraph
    if current_para_start < len(text):
        para_text = text[current_para_start:]
        if para_text.strip():
            paragraphs.append((para_text, current_para_start, para_id))
    
    # If no paragraph breaks found, treat entire text as one paragraph
    if not paragraphs:
        paragraphs = [(text, 0, 0)]
    
    # Now segment sentences within each paragraph using spaCy
    sentences = []
    
    for para_text, para_offset, para_id in paragraphs:
        # Process paragraph with spaCy
        doc = nlp(para_text)
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue
            
            # Compute offsets relative to original text
            # sent.start_char and sent.end_char are relative to para_text
            sent_start = para_offset + sent.start_char
            sent_end = para_offset + sent.end_char
            
            # Adjust for stripped whitespace
            # Find the actual stripped text position
            stripped_start = sent_start
            while stripped_start < sent_end and text[stripped_start].isspace():
                stripped_start += 1
            
            stripped_end = sent_end
            while stripped_end > stripped_start and text[stripped_end - 1].isspace():
                stripped_end -= 1
            
            sentences.append((sent_text, stripped_start, stripped_end, para_id))
    
    return sentences


def segment_sentences(text: str) -> List[Tuple[str, int, int, int]]:
    """
    Segment text into sentences with offsets and paragraph boundaries.
    
    This uses a simple but robust regex-based approach that handles:
    - Common abbreviations (Dr., Mr., etc.)
    - Decimal numbers
    - Quotes around sentences
    
    Args:
        text: The input text to segment
        
    Returns:
        List of tuples: (sentence_text, start_offset, end_offset, paragraph_id)
    """
    # Split text into paragraphs first (double newline or significant whitespace)
    paragraph_pattern = r'\n\s*\n'
    paragraphs = re.split(paragraph_pattern, text)
    
    sentences = []
    current_offset = 0
    
    for para_idx, paragraph in enumerate(paragraphs):
        # Find where this paragraph starts in the original text
        para_start = text.find(paragraph, current_offset)
        if para_start == -1:
            # Fallback if exact match not found
            para_start = current_offset
        
        # Sentence boundary detection with lookahead/lookbehind
        # Match: period/question/exclamation followed by space and capital letter
        # But not after common abbreviations
        sentence_pattern = r'(?<!\b(?:Dr|Mr|Mrs|Ms|Prof|Sr|Jr|vs|etc|i\.e|e\.g))\.\s+(?=[A-Z])|[.!?]+\s+(?=[A-Z])'
        
        # Split paragraph into sentences
        para_sentences = re.split(sentence_pattern, paragraph)
        
        # Process each sentence in the paragraph
        sentence_offset = para_start
        for sent_text in para_sentences:
            sent_text = sent_text.strip()
            if not sent_text:
                continue
            
            # Find the sentence in the paragraph
            sent_start = text.find(sent_text, sentence_offset)
            if sent_start == -1:
                sent_start = sentence_offset
            
            sent_end = sent_start + len(sent_text)
            
            sentences.append((sent_text, sent_start, sent_end, para_idx))
            sentence_offset = sent_end
        
        # Update offset for next paragraph
        current_offset = para_start + len(paragraph)
    
    return sentences


def segment_sentences_simple(text: str) -> List[Tuple[str, int, int, int]]:
    """
    Simplified sentence segmentation that's more reliable.
    
    Splits on sentence-ending punctuation followed by whitespace and uppercase.
    Tracks paragraphs based on double newlines.
    
    Args:
        text: The input text to segment
        
    Returns:
        List of tuples: (sentence_text, start_offset, end_offset, paragraph_id)
    """
    # First, identify paragraph boundaries
    paragraphs = []
    current_para = []
    current_para_start = 0
    
    lines = text.split('\n')
    line_offset = 0
    para_id = 0
    
    for line in lines:
        if line.strip():
            if not current_para:
                current_para_start = line_offset
            current_para.append(line)
        else:
            if current_para:
                para_text = '\n'.join(current_para)
                paragraphs.append((para_text, current_para_start, para_id))
                para_id += 1
                current_para = []
        line_offset += len(line) + 1  # +1 for newline
    
    # Don't forget the last paragraph
    if current_para:
        para_text = '\n'.join(current_para)
        paragraphs.append((para_text, current_para_start, para_id))
    
    # Now segment sentences within paragraphs
    sentences = []
    
    for para_text, para_offset, para_id in paragraphs:
        # Split on sentence boundaries
        # Pattern: sentence-ending punctuation + space + uppercase
        parts = re.split(r'([.!?]+)\s+(?=[A-Z])', para_text)
        
        current_pos = para_offset
        i = 0
        while i < len(parts):
            # Check if next part is punctuation (any sequence of .!? characters)
            if i + 1 < len(parts) and re.match(r'^[.!?]+$', parts[i + 1]):
                # This part ends with punctuation, combine it
                sent = parts[i] + parts[i + 1]
                i += 2
            else:
                sent = parts[i]
                i += 1
            
            sent = sent.strip()
            if not sent:
                continue
            
            # Find actual position in original text
            sent_start = text.find(sent, current_pos)
            if sent_start == -1:
                # If exact match not found, try to find it in the surrounding area
                # This can happen with whitespace variations
                window_start = max(0, current_pos - 10)
                window_end = min(len(text), current_pos + len(sent) + 10)
                sent_start = text.find(sent, window_start, window_end)
                if sent_start == -1:
                    # Last resort: use current position as approximation
                    # This should rarely happen with well-formed text
                    sent_start = current_pos
            
            sent_end = sent_start + len(sent)
            sentences.append((sent, sent_start, sent_end, para_id))
            current_pos = sent_end
    
    return sentences


def segment_sentences_auto(text: str) -> Tuple[List[Tuple[str, int, int, int]], str]:
    """
    Automatically choose the best available sentence segmentation method.
    
    Priority:
    1. spaCy-based segmentation (if available and enabled)
    2. Fallback to regex-based segmentation
    
    Args:
        text: The input text to segment
        
    Returns:
        Tuple of (sentences, engine_name) where:
        - sentences: List of (sentence_text, start_offset, end_offset, paragraph_id)
        - engine_name: "spacy_sentencizer" or "regex_fallback"
    """
    # Check if spaCy is available and enabled
    if SPACY_AVAILABLE and USE_SPACY:
        nlp = _get_spacy_nlp()
        if nlp is not None:
            try:
                sentences = segment_sentences_spacy(text)
                return sentences, "spacy_sentencizer"
            except Exception as e:
                logger.error(f"spaCy segmentation failed: {e}, falling back to regex")
    
    # Fallback to regex
    if not SPACY_AVAILABLE:
        logger.warning("spaCy not installed, using regex fallback segmentation")
    elif not USE_SPACY:
        logger.info("spaCy disabled via PREPROCESS_USE_SPACY=false, using regex fallback")
    
    sentences = segment_sentences_simple(text)
    return sentences, "regex_fallback"


# ============================================================================
# Discourse Marker Detection
# ============================================================================

def detect_discourse_markers(sentence: str) -> List[DiscourseMarker]:
    """
    Detect discourse markers in a sentence.
    
    Performs case-insensitive, punctuation-tolerant matching with word boundaries.
    
    Args:
        sentence: The sentence text to analyze
        
    Returns:
        List of detected DiscourseMarker objects
    """
    detected = []
    sentence_lower = sentence.lower()
    
    for signal_type, markers in DISCOURSE_MARKERS.items():
        for marker in markers:
            # Create pattern with word boundaries
            # Allow optional punctuation before/after
            pattern = r'\b' + re.escape(marker) + r'\b'
            
            for match in re.finditer(pattern, sentence_lower):
                detected.append(DiscourseMarker(
                    marker=marker,
                    position=match.start(),
                    signal_type=signal_type
                ))
    
    return detected


# ============================================================================
# Candidate Sentence Flagging
# ============================================================================

# Candidate thresholds
MIN_CANDIDATE_REASONS = 2  # Minimum number of positive signals to flag as candidate


def flag_candidate_sentence(sentence_text: str, markers: List[DiscourseMarker]) -> Tuple[bool, List[str]]:
    """
    Determine if a sentence is an argument candidate using heuristics.
    
    Criteria:
    - Has discourse markers (strong signal)
    - Not too short (< 10 chars is likely a fragment)
    - Not too long (> 500 chars is likely malformed)
    - Contains at least one verb-like structure (basic heuristic)
    
    A sentence is flagged as a candidate if it has at least MIN_CANDIDATE_REASONS
    positive signals from the criteria above.
    
    Args:
        sentence_text: The sentence text
        markers: List of detected discourse markers
        
    Returns:
        Tuple of (is_candidate, list of reasons)
    """
    reasons = []
    
    # Length checks
    if len(sentence_text) < 10:
        return False, ["too_short"]
    
    if len(sentence_text) > 500:
        return False, ["too_long"]
    
    # Discourse marker presence (strong signal)
    if markers:
        reasons.append(f"has_{len(markers)}_discourse_markers")
    
    # Check for verb-like patterns (very basic heuristic)
    # Look for common verb patterns: is/are/was/were/has/have/can/should/must/will
    verb_pattern = r'\b(is|are|was|were|has|have|had|can|could|should|would|must|will|shall|may|might|do|does|did)\b'
    if re.search(verb_pattern, sentence_text.lower()):
        reasons.append("has_verb_pattern")
    
    # Word count check (reasonable argument length)
    word_count = len(sentence_text.split())
    if word_count >= 5:
        reasons.append(f"sufficient_length_{word_count}_words")
    
    # Decision: candidate if has at least MIN_CANDIDATE_REASONS positive signals
    is_candidate = len(reasons) >= MIN_CANDIDATE_REASONS
    
    return is_candidate, reasons


# ============================================================================
# Main Preprocessing Entry Point
# ============================================================================

def preprocess_text(text: str) -> PreprocessedDocument:
    """
    Main preprocessing entry point.
    
    Takes raw input text and returns a structured PreprocessedDocument with:
    - Sentence segmentation with offsets and paragraph IDs
    - Discourse marker detection per sentence
    - Candidate flagging per sentence
    
    Args:
        text: Raw input text
        
    Returns:
        PreprocessedDocument with all preprocessing results
    """
    logger.info("Starting text preprocessing...")
    
    # Validate input
    if not text or not text.strip():
        logger.warning("Empty input text provided")
        return PreprocessedDocument(
            original_text=text,
            sentences=[],
            paragraph_count=0,
            metadata={'error': 'empty_input'}
        )
    
    # Step 1: Sentence segmentation
    logger.info("Segmenting sentences...")
    raw_sentences, segmentation_engine = segment_sentences_auto(text)
    logger.info(f"Found {len(raw_sentences)} sentences using {segmentation_engine}")
    
    # Step 2: Process each sentence
    sentences = []
    marker_counts = {signal: 0 for signal in DISCOURSE_MARKERS.keys()}
    candidate_count = 0
    
    for idx, (sent_text, start, end, para_id) in enumerate(raw_sentences):
        # Detect discourse markers
        markers = detect_discourse_markers(sent_text)
        for marker in markers:
            marker_counts[marker.signal_type] += 1
        
        # Flag as candidate
        is_candidate, reasons = flag_candidate_sentence(sent_text, markers)
        if is_candidate:
            candidate_count += 1
        
        # Create sentence unit
        sentence_unit = SentenceUnit(
            id=f"s{idx + 1}",
            text=sent_text,
            paragraph_id=para_id,
            start_char=start,
            end_char=end,
            markers=markers,
            is_candidate=is_candidate,
            candidate_reasons=reasons
        )
        sentences.append(sentence_unit)
    
    # Determine paragraph count
    paragraph_count = max([s.paragraph_id for s in sentences], default=-1) + 1
    
    # Log statistics
    logger.info(f"Preprocessing complete:")
    logger.info(f"  - Paragraphs: {paragraph_count}")
    logger.info(f"  - Sentences: {len(sentences)}")
    logger.info(f"  - Candidates: {candidate_count}")
    logger.info(f"  - Marker counts: {marker_counts}")
    
    # Create result document
    result = PreprocessedDocument(
        original_text=text,
        sentences=sentences,
        paragraph_count=paragraph_count,
        metadata={
            'sentence_count': len(sentences),
            'candidate_count': candidate_count,
            'marker_counts': marker_counts,
            'preprocessing_version': 'v2.0',
            'segmentation_engine': segmentation_engine
        }
    )
    
    return result


# ============================================================================
# Utility Functions
# ============================================================================

def get_candidates(doc: PreprocessedDocument) -> List[SentenceUnit]:
    """Extract only candidate sentences from a preprocessed document."""
    return [s for s in doc.sentences if s.is_candidate]


def get_sentences_with_markers(doc: PreprocessedDocument, signal_type: Optional[str] = None) -> List[SentenceUnit]:
    """
    Extract sentences that have discourse markers.
    
    Args:
        doc: PreprocessedDocument
        signal_type: Optional filter by specific signal type (e.g., 'SUPPORT_CUE')
        
    Returns:
        List of sentences with matching markers
    """
    if signal_type:
        return [s for s in doc.sentences if any(m.signal_type == signal_type for m in s.markers)]
    else:
        return [s for s in doc.sentences if s.markers]
