# Backend Modules

This directory contains backend processing modules for argument extraction.

## Modules

### preprocessing.py

Deterministic text preprocessing for argument mining:
- Sentence segmentation with offsets
- Discourse marker detection
- Candidate sentence flagging

See [docs/preprocessing.md](../../docs/preprocessing.md) for detailed documentation.

## Usage

```python
from app_mockup.backend.preprocessing import preprocess_text

text = "Your argumentative text here..."
result = preprocess_text(text)
```

## Testing

```bash
# Run unit tests
python -m unittest tests.test_preprocessing

# Run verification script
python scripts/verify_preprocessing.py
```
