# Preprocessing Pipeline Documentation

## Overview

The preprocessing pipeline is a deterministic, rule-based module that prepares raw text for argument mining. It does not use any LLMs or non-deterministic components, ensuring consistent results across runs.

## Components

### 1. Sentence Segmentation

**Purpose:** Split input text into individual sentences while preserving structure.

**Features:**
- Detects sentence boundaries using regex patterns
- Tracks paragraph boundaries (via double newlines)
- Preserves character offsets (`start_char`, `end_char`) for each sentence
- Assigns stable sentence IDs (`s1`, `s2`, etc.)

**Example:**
```python
from app_mockup.backend.preprocessing import preprocess_text

text = "The death penalty is wrong. This is because it violates human rights."
result = preprocess_text(text)

for sentence in result.sentences:
    print(f"{sentence.id}: {sentence.text}")
    print(f"  Offset: {sentence.start_char}-{sentence.end_char}")
    print(f"  Paragraph: {sentence.paragraph_id}")
```

### 2. Discourse Marker Detection

**Purpose:** Identify argumentative cue phrases that signal reasoning patterns.

**Marker Categories:**

- **SUPPORT_CUE**: Indicates support/justification
  - Examples: `because`, `since`, `therefore`, `thus`, `as a result`
  
- **ATTACK_CUE**: Indicates objection/contrast
  - Examples: `however`, `but`, `although`, `on the other hand`
  
- **ELAB_CUE**: Indicates elaboration/clarification
  - Examples: `in fact`, `for example`, `specifically`

**Features:**
- Case-insensitive matching
- Punctuation-tolerant
- Word boundary enforcement (won't match "as" inside "class")
- Supports multi-word markers ("as a result")

**Example:**
```python
result = preprocess_text("AI is dangerous because it's unpredictable. However, it has benefits.")

for sentence in result.sentences:
    if sentence.markers:
        print(f"{sentence.text}")
        for marker in sentence.markers:
            print(f"  - {marker.marker} ({marker.signal_type})")
```

### 3. Candidate Sentence Flagging

**Purpose:** Mark sentences that are likely to be argument components.

**Heuristics:**
- Length check (not too short < 10 chars, not too long > 500 chars)
- Discourse marker presence (strong positive signal)
- Verb pattern detection (basic grammatical check)
- Word count threshold (≥ 5 words for "sufficient length")

**Decision Logic:**
A sentence is flagged as a candidate if it has at least `MIN_CANDIDATE_REASONS` (2) positive signals.

**Example:**
```python
result = preprocess_text("The death penalty is wrong because it's irreversible.")

for sentence in result.sentences:
    if sentence.is_candidate:
        print(f"✓ {sentence.text}")
        print(f"  Reasons: {sentence.candidate_reasons}")
```

## Data Structures

### SentenceUnit
```python
@dataclass
class SentenceUnit:
    id: str                              # e.g., "s1", "s2"
    text: str                            # Sentence text
    paragraph_id: int                    # Paragraph index
    start_char: int                      # Character offset (start)
    end_char: int                        # Character offset (end)
    markers: List[DiscourseMarker]       # Detected markers
    is_candidate: bool                   # Is argument candidate?
    candidate_reasons: List[str]         # Reasons for candidacy
```

### PreprocessedDocument
```python
@dataclass
class PreprocessedDocument:
    original_text: str                   # Input text
    sentences: List[SentenceUnit]        # Processed sentences
    paragraph_count: int                 # Number of paragraphs
    metadata: dict                       # Statistics and info
```

## Usage

### Basic Preprocessing
```python
from app_mockup.backend.preprocessing import preprocess_text

text = """Your argumentative text here..."""
result = preprocess_text(text)

print(f"Sentences: {len(result.sentences)}")
print(f"Candidates: {result.metadata['candidate_count']}")
print(f"Markers: {result.metadata['marker_counts']}")
```

### Filter Candidates
```python
from app_mockup.backend.preprocessing import get_candidates

candidates = get_candidates(result)
for candidate in candidates:
    print(candidate.text)
```

### Filter by Marker Type
```python
from app_mockup.backend.preprocessing import get_sentences_with_markers

# Get only sentences with support markers
support_sentences = get_sentences_with_markers(result, signal_type='SUPPORT_CUE')
```

## Integration with Extraction Pipeline

The preprocessing module is automatically called by both the mock and real extractors:

1. **extractor_stub.py** - Mock extraction uses preprocessing to improve graph generation
2. **llm_extractor.py** - Real LLM extraction uses preprocessing as first stage

The preprocessing results are included in the graph metadata:
```python
graph["meta"]["preprocessing"] = {
    "sentence_count": 10,
    "candidate_count": 7,
    "paragraph_count": 3,
    "marker_counts": {
        "SUPPORT_CUE": 3,
        "ATTACK_CUE": 2,
        "ELAB_CUE": 1
    }
}
```

## Testing

Run the unit tests:
```bash
python -m unittest tests.test_preprocessing -v
```

Run the verification script:
```bash
python scripts/verify_preprocessing.py
```

## Future Enhancements

Potential improvements not in scope for current implementation:

1. **Coreference Resolution** - Resolve pronouns to their referents
2. **Named Entity Recognition** - Identify key entities in arguments
3. **Advanced Sentence Splitting** - Better handling of abbreviations
4. **Context Window** - Track surrounding sentences for better classification
5. **Custom Marker Dictionaries** - Allow domain-specific marker additions

## Logging

The module logs at INFO level:
```
INFO: Starting text preprocessing...
INFO: Segmenting sentences...
INFO: Found 10 sentences
INFO: Preprocessing complete:
INFO:   - Paragraphs: 3
INFO:   - Sentences: 10
INFO:   - Candidates: 7
INFO:   - Marker counts: {'SUPPORT_CUE': 3, 'ATTACK_CUE': 2, 'ELAB_CUE': 0}
```

Configure logging level as needed:
```python
import logging
logging.basicConfig(level=logging.INFO)
```
