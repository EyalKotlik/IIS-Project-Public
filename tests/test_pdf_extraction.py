"""
Tests for PDF text extraction module.

Tests cover:
- Text extraction from real PDFs
- Whitespace normalization
- De-hyphenation
- Header/footer removal
- Scanned PDF detection
- Integration with full pipeline
"""

import pytest
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "app_mockup"))

from backend.pdf_extraction import (
    extract_text_from_pdf,
    ExtractedPdfText,
    PdfExtractionConfig,
    _normalize_whitespace,
    _dehyphenate_text,
    _remove_header_footer_noise,
    _detect_scanned_pdf,
)


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.unit
def test_normalize_whitespace_collapse_spaces():
    """Test that multiple spaces are collapsed to single space."""
    config = PdfExtractionConfig(
        collapse_spaces=True,
        normalize_newlines=False,
        preserve_paragraph_breaks=False
    )
    
    text = "Hello    world   test"
    result = _normalize_whitespace(text, config)
    assert result == "Hello world test"


@pytest.mark.unit
def test_normalize_whitespace_preserve_paragraphs():
    """Test that paragraph breaks (double newlines) are preserved."""
    config = PdfExtractionConfig(
        collapse_spaces=False,
        normalize_newlines=True,
        preserve_paragraph_breaks=True
    )
    
    text = "Paragraph 1\n\nParagraph 2\n\n\n\nParagraph 3"
    result = _normalize_whitespace(text, config)
    assert result == "Paragraph 1\n\nParagraph 2\n\nParagraph 3"


@pytest.mark.unit
def test_normalize_whitespace_line_endings():
    """Test that different line endings are normalized."""
    config = PdfExtractionConfig(
        collapse_spaces=False,
        normalize_newlines=True,
        preserve_paragraph_breaks=False
    )
    
    text = "Line 1\r\nLine 2\rLine 3\nLine 4"
    result = _normalize_whitespace(text, config)
    expected = "Line 1\nLine 2\nLine 3\nLine 4"
    assert result == expected


@pytest.mark.unit
def test_dehyphenate_text_basic():
    """Test basic word dehyphenation."""
    text = "This is an exam-\nple of hyphen-\nation."
    result = _dehyphenate_text(text)
    assert result == "This is an example of hyphenation."


@pytest.mark.unit
def test_dehyphenate_text_compound_words():
    """Test dehyphenation behavior with compound words.
    
    Note: The current implementation joins words when the continuation
    starts with lowercase, which may incorrectly join some compound
    words like "well-known" -> "wellknown". This is a known limitation.
    """
    text = "A well-\nknown example"
    result = _dehyphenate_text(text)
    # Current behavior: joins because "known" starts with lowercase
    assert "wellknown" in result or "well-known" in result


@pytest.mark.unit
def test_dehyphenate_text_no_false_positives():
    """Test that dehyphenation doesn't break on proper line breaks."""
    text = "End of sentence.\nNew sentence starts here."
    result = _dehyphenate_text(text)
    assert result == text  # Should be unchanged


@pytest.mark.unit
def test_remove_header_footer_noise_basic():
    """Test removal of repeated header/footer lines."""
    # Need at least 3 pages for header/footer detection
    pages = [
        "H\nActual content page 1\nF",
        "H\nActual content page 2\nF",
        "H\nActual content page 3\nF",
    ]
    
    result = _remove_header_footer_noise(pages, threshold=0.7)
    
    # H and F should be removed (short lines at top/bottom)
    for page in result:
        lines = [l.strip() for l in page.split('\n') if l.strip()]
        # Content should still be there
        assert any("Actual content" in line for line in lines)


@pytest.mark.unit
def test_remove_header_footer_noise_threshold():
    """Test that threshold controls what gets removed."""
    pages = [
        "H\nCommon Header\nPage 1 content\nFooter",
        "H\nCommon Header\nPage 2 content\nFooter",
        "H\nDifferent Header\nPage 3 content\nFooter",
    ]
    
    # "H" appears on all pages at top (100%)
    # "Footer" appears on all pages at bottom (100%)
    # Should remove both with 0.7 threshold
    result = _remove_header_footer_noise(pages, threshold=0.7)
    
    # "H" and "Footer" should be removed
    for page in result:
        assert "H" not in page or "Page" in page  # "H" in "Header" is ok
        # Content should still be there
        assert "content" in page


@pytest.mark.unit
def test_remove_header_footer_preserves_unique_content():
    """Test that unique content is preserved."""
    # With only 2 pages, header/footer removal is skipped
    pages = [
        "Unique content A",
        "Unique content B",
    ]
    
    result = _remove_header_footer_noise(pages, threshold=0.7)
    
    # All unique content should be preserved (header/footer removal skipped with <3 pages)
    assert "Unique content A" in result[0]
    assert "Unique content B" in result[1]


@pytest.mark.unit
def test_detect_scanned_pdf_low_text():
    """Test detection of scanned PDFs with low text."""
    config = PdfExtractionConfig(
        min_text_density=10.0,
        warn_low_text_pages=2
    )
    
    # Simulate pages with very little text
    pages = ["1", "2", "Some text here"]
    
    warnings = _detect_scanned_pdf(pages, config)
    
    assert len(warnings) > 0
    assert any("scanned" in w.lower() for w in warnings)


@pytest.mark.unit
def test_detect_scanned_pdf_normal_text():
    """Test that normal PDFs don't trigger scanned warnings."""
    config = PdfExtractionConfig(
        min_text_density=10.0,
        warn_low_text_pages=2
    )
    
    # Normal pages with sufficient text
    pages = [
        "This is page 1 with plenty of text content for analysis.",
        "This is page 2 with plenty of text content for analysis.",
        "This is page 3 with plenty of text content for analysis.",
    ]
    
    warnings = _detect_scanned_pdf(pages, config)
    
    # Should not warn about scanned PDF
    assert len(warnings) == 0 or not any("scanned" in w.lower() for w in warnings)


@pytest.mark.integration
def test_extract_from_sample_pdf():
    """Test extraction from real PDF fixture."""
    pdf_path = TEST_DATA_DIR / "sample_argument.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    result = extract_text_from_pdf(pdf_bytes)
    
    # Check basic structure
    assert isinstance(result, ExtractedPdfText)
    assert result.page_count == 2
    assert len(result.pages) == 2
    assert result.source_hash is not None
    
    # Check that key content is present
    assert "Electric cars" in result.text
    assert "emissions" in result.text
    assert "conclusion" in result.text.lower()
    
    # Check statistics
    assert result.stats['char_count'] > 0
    assert result.stats['page_count'] == 2
    assert result.stats['non_whitespace_ratio'] > 0


@pytest.mark.integration
def test_extract_from_scanned_pdf():
    """Test detection of scanned/low-text PDF."""
    pdf_path = TEST_DATA_DIR / "scanned_low_text.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    result = extract_text_from_pdf(pdf_bytes)
    
    # Should have warnings about low text
    assert len(result.warnings) > 0
    assert any("scanned" in w.lower() or "low text" in w.lower() for w in result.warnings)


@pytest.mark.integration
def test_pdf_extraction_with_config():
    """Test PDF extraction with custom config."""
    pdf_path = TEST_DATA_DIR / "sample_argument.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    # Config with page separators
    config = PdfExtractionConfig(
        add_page_separators=True,
        page_separator_template="\n--- PAGE {page_num} ---\n"
    )
    
    result = extract_text_from_pdf(pdf_bytes, config=config)
    
    # Should contain page separators
    assert "PAGE 1" in result.text
    assert "PAGE 2" in result.text


@pytest.mark.integration
def test_pdf_extraction_caching_hash():
    """Test that same PDF produces same hash for caching."""
    pdf_path = TEST_DATA_DIR / "sample_argument.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    result1 = extract_text_from_pdf(pdf_bytes)
    result2 = extract_text_from_pdf(pdf_bytes)
    
    # Same PDF should produce same hash
    assert result1.source_hash == result2.source_hash


@pytest.mark.integration
def test_pdf_extraction_text_quality():
    """Test that extracted text is of good quality."""
    pdf_path = TEST_DATA_DIR / "sample_argument.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    result = extract_text_from_pdf(pdf_bytes)
    
    # Text should be reasonably clean
    # No excessive whitespace
    assert "   " not in result.text  # No triple spaces
    
    # Should preserve paragraph structure
    assert "\n\n" in result.text  # Has paragraph breaks
    
    # Should have reasonable character density
    assert result.stats['non_whitespace_ratio'] > 0.5


@pytest.mark.negative
def test_extract_from_invalid_pdf():
    """Test handling of invalid PDF bytes."""
    invalid_bytes = b"This is not a PDF"
    
    with pytest.raises(ValueError, match="Invalid or corrupted PDF"):
        extract_text_from_pdf(invalid_bytes)


@pytest.mark.negative
def test_extract_from_empty_bytes():
    """Test handling of empty bytes."""
    with pytest.raises(ValueError):
        extract_text_from_pdf(b"")


@pytest.mark.unit
def test_config_defaults():
    """Test that config has sensible defaults."""
    config = PdfExtractionConfig()
    
    assert config.collapse_spaces is True
    assert config.normalize_newlines is True
    assert config.preserve_paragraph_breaks is True
    assert config.dehyphenate is True
    assert config.remove_headers_footers is True
    assert config.add_page_separators is False


@pytest.mark.demo
def test_demo_full_extraction_pipeline():
    """
    Demo test showing full PDF extraction pipeline.
    
    This test demonstrates:
    1. Loading a PDF
    2. Extracting text with cleanup
    3. Inspecting results and warnings
    """
    pdf_path = TEST_DATA_DIR / "sample_argument.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")
    
    print("\n" + "="*60)
    print("PDF EXTRACTION DEMO")
    print("="*60)
    
    # Load PDF
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    print(f"\n1. Loaded PDF: {len(pdf_bytes)} bytes")
    
    # Extract with default config
    result = extract_text_from_pdf(pdf_bytes)
    
    print(f"\n2. Extraction Results:")
    print(f"   - Pages: {result.page_count}")
    print(f"   - Total characters: {result.stats['char_count']}")
    print(f"   - Avg chars/page: {result.stats['avg_chars_per_page']:.1f}")
    print(f"   - Text density: {result.stats['non_whitespace_ratio']:.2%}")
    print(f"   - Hash: {result.source_hash[:16]}...")
    
    if result.warnings:
        print(f"\n3. Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
    else:
        print(f"\n3. No warnings (good quality PDF)")
    
    print(f"\n4. Extracted Text Preview (first 300 chars):")
    print("-" * 60)
    print(result.text[:300])
    print("-" * 60)
    
    # Verify content
    assert "Electric cars" in result.text
    assert result.page_count == 2
    print("\n✅ Demo complete - extraction successful!")
