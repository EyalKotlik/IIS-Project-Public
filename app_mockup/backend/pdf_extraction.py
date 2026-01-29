"""
PDF Text Extraction Module
===========================

Provides robust PDF text extraction with cleanup and quality detection.

Main entry point:
    extract_text_from_pdf(pdf_bytes, config) -> ExtractedPdfText

Uses PyMuPDF (fitz) for reliable text extraction from non-scanned PDFs.
Includes heuristics for:
- Whitespace normalization
- De-hyphenation
- Header/footer removal
- Scanned PDF detection
"""

import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import logging

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PdfExtractionConfig:
    """Configuration for PDF text extraction."""
    
    # Whitespace normalization
    collapse_spaces: bool = True
    normalize_newlines: bool = True
    preserve_paragraph_breaks: bool = True
    
    # De-hyphenation
    dehyphenate: bool = True
    
    # Header/footer removal
    remove_headers_footers: bool = True
    header_footer_threshold: float = 0.7  # If line appears on >70% of pages
    
    # Page separators
    add_page_separators: bool = False
    page_separator_template: str = "\n\n[PAGE {page_num}]\n\n"
    
    # Scanned PDF detection
    min_text_density: float = 10.0  # chars per page minimum
    warn_low_text_pages: int = 2  # warn if this many pages have low text


@dataclass
class ExtractedPdfText:
    """Result of PDF text extraction."""
    
    text: str
    """Final cleaned text ready for processing."""
    
    pages: List[str] = field(default_factory=list)
    """Raw text per page (before cleanup)."""
    
    page_count: int = 0
    """Total number of pages in PDF."""
    
    warnings: List[str] = field(default_factory=list)
    """Warnings about extraction quality."""
    
    stats: Dict = field(default_factory=dict)
    """Extraction statistics (char_count, non_whitespace_ratio, etc.)."""
    
    source_hash: Optional[str] = None
    """SHA256 hash of source PDF bytes for caching."""


def _compute_pdf_hash(pdf_bytes: bytes) -> str:
    """Compute SHA256 hash of PDF bytes for caching."""
    return hashlib.sha256(pdf_bytes).hexdigest()


def _normalize_whitespace(text: str, config: PdfExtractionConfig) -> str:
    """Normalize whitespace while preserving paragraph structure."""
    
    if not config.collapse_spaces and not config.normalize_newlines:
        return text
    
    result = text
    
    if config.normalize_newlines:
        # Normalize line endings
        result = result.replace('\r\n', '\n').replace('\r', '\n')
    
    if config.collapse_spaces:
        # Collapse multiple spaces to single space
        result = re.sub(r' +', ' ', result)
    
    if config.preserve_paragraph_breaks:
        # Preserve double newlines (paragraph breaks)
        # But collapse 3+ newlines to just 2
        result = re.sub(r'\n{3,}', '\n\n', result)
    else:
        # Collapse all multiple newlines to single newline
        result = re.sub(r'\n+', '\n', result)
    
    return result


def _dehyphenate_text(text: str) -> str:
    """
    Remove hyphenation artifacts from line breaks.
    
    Joins words split across lines like "exam-\nple" -> "example".
    Only joins if the continuation starts with a lowercase letter.
    
    Note: This heuristic may incorrectly join some compound words like
    "well-known" -> "wellknown". It's a best-effort approach that works
    for most common hyphenation patterns but isn't perfect.
    """
    # Pattern: word ending with hyphen at end of line, followed by word continuation
    
    def replace_hyphen(match):
        before = match.group(1)
        after = match.group(2)
        
        # If continuation starts with lowercase, likely a split word
        if after[0].islower():
            return before + after
        # Otherwise keep the hyphen and line break
        return match.group(0)
    
    # Pattern: word chars + hyphen + newline + lowercase word chars
    pattern = r'(\w+)-\n(\w+)'
    result = re.sub(pattern, replace_hyphen, text)
    
    return result


def _remove_header_footer_noise(pages: List[str], threshold: float = 0.7) -> List[str]:
    """
    Remove repeated lines that appear on many pages (likely headers/footers).
    
    Only considers lines at the top/bottom of pages and short lines (< 50 chars)
    like page numbers, to avoid removing legitimate content.
    
    Args:
        pages: List of page texts
        threshold: Remove lines appearing on this fraction of pages or more
    
    Returns:
        List of cleaned page texts
    """
    if len(pages) <= 2:  # Need at least 3 pages to reliably detect headers/footers
        return pages
    
    # Collect potential header/footer candidates
    # Only consider first 2 and last 2 NON-EMPTY lines from each page
    line_counts = {}
    for page_text in pages:
        lines = [l.strip() for l in page_text.split('\n') if l.strip()]
        if not lines:
            continue
        
        # Check first 2 non-empty lines (potential headers)
        for i, line in enumerate(lines[:2]):
            if len(line) < 50:  # Only short lines like page numbers, headers
                key = (line, 'top')  # Track position to avoid double-counting
                line_counts[key] = line_counts.get(key, 0) + 1
        
        # Check last 2 non-empty lines (potential footers)
        # Only count if they're NOT in the first 2 (avoid double-counting for short pages)
        for i, line in enumerate(lines[-2:]):
            line_idx = len(lines) - 2 + i
            if line_idx >= 2 and len(line) < 50:  # Not in first 2
                key = (line, 'bottom')
                line_counts[key] = line_counts.get(key, 0) + 1
    
    # Find lines that appear on many pages
    min_pages = int(len(pages) * threshold)
    header_footer_lines = {}  # Map line text to position (top/bottom)
    for (line, position), count in line_counts.items():
        if count >= min_pages:
            if line not in header_footer_lines:
                header_footer_lines[line] = set()
            header_footer_lines[line].add(position)
    
    if not header_footer_lines:
        return pages
    
    # Remove those lines from each page (only from appropriate positions)
    cleaned_pages = []
    for page_text in pages:
        lines = page_text.split('\n')
        non_empty_indices = [i for i, l in enumerate(lines) if l.strip()]
        
        if not non_empty_indices:
            cleaned_pages.append(page_text)
            continue
        
        # Determine which line indices to keep
        keep_indices = set(range(len(lines)))
        
        # Check first 2 non-empty lines (remove if marked as 'top' header)
        for i, idx in enumerate(non_empty_indices[:2]):
            line_text = lines[idx].strip()
            if line_text in header_footer_lines and 'top' in header_footer_lines[line_text]:
                keep_indices.discard(idx)
        
        # Check last 2 non-empty lines (remove if marked as 'bottom' footer)
        for i, idx in enumerate(non_empty_indices[-2:]):
            line_idx_in_non_empty = len(non_empty_indices) - 2 + i
            if line_idx_in_non_empty >= 2:  # Not in first 2
                line_text = lines[idx].strip()
                if line_text in header_footer_lines and 'bottom' in header_footer_lines[line_text]:
                    keep_indices.discard(idx)
        
        filtered_lines = [lines[i] for i in sorted(keep_indices)]
        cleaned_pages.append('\n'.join(filtered_lines))
    
    logger.info(f"Removed {len(header_footer_lines)} unique header/footer patterns")
    return cleaned_pages


def _detect_scanned_pdf(pages: List[str], config: PdfExtractionConfig) -> List[str]:
    """
    Detect if PDF is likely scanned (low extractable text).
    
    Returns list of warnings if issues detected.
    """
    warnings = []
    
    if not pages:
        warnings.append("No pages extracted from PDF")
        return warnings
    
    # Check text density per page
    low_text_pages = 0
    for page_text in pages:
        char_count = len(page_text.strip())
        if char_count < config.min_text_density:
            low_text_pages += 1
    
    if low_text_pages >= config.warn_low_text_pages:
        warnings.append(
            f"Likely scanned PDF: {low_text_pages}/{len(pages)} pages have very low text. "
            "OCR not available - try a text-based PDF."
        )
    
    # Check if entire document has very little text
    total_chars = sum(len(page.strip()) for page in pages)
    avg_chars_per_page = total_chars / len(pages) if pages else 0
    
    if avg_chars_per_page < config.min_text_density:
        warnings.append(
            f"Low text density detected: {avg_chars_per_page:.1f} chars/page average. "
            "PDF may be image-based or poorly formatted."
        )
    
    return warnings


def extract_text_from_pdf(
    pdf_bytes: bytes,
    config: Optional[PdfExtractionConfig] = None
) -> ExtractedPdfText:
    """
    Extract text from PDF with cleanup and quality detection.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        config: Optional extraction configuration
    
    Returns:
        ExtractedPdfText with cleaned text and metadata
    
    Raises:
        RuntimeError: If PyMuPDF is not available
        ValueError: If PDF cannot be opened
    """
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError(
            "PyMuPDF (fitz) is not installed. "
            "Install with: pip install pymupdf"
        )
    
    config = config or PdfExtractionConfig()
    
    # Compute hash for caching
    source_hash = _compute_pdf_hash(pdf_bytes)
    
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except fitz.FileDataError as e:
        raise ValueError(f"Invalid or corrupted PDF file: {e}")
    except fitz.FitzError as e:
        raise ValueError(f"Failed to open PDF (PyMuPDF error): {e}")
    except Exception as e:
        # Log the full exception for debugging
        logger.exception("Unexpected error opening PDF")
        raise ValueError(f"Failed to open PDF: {e}")
    
    # Extract text per page
    raw_pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        raw_pages.append(page_text)
    
    page_count = len(raw_pages)
    doc.close()
    
    # Clean up pages
    cleaned_pages = raw_pages.copy()
    
    # Remove headers/footers
    if config.remove_headers_footers:
        cleaned_pages = _remove_header_footer_noise(
            cleaned_pages,
            threshold=config.header_footer_threshold
        )
    
    # Combine pages with optional separators
    if config.add_page_separators:
        text_parts = []
        for i, page_text in enumerate(cleaned_pages, start=1):
            separator = config.page_separator_template.format(page_num=i)
            text_parts.append(separator)
            text_parts.append(page_text)
        combined_text = ''.join(text_parts)
    else:
        combined_text = '\n\n'.join(cleaned_pages)
    
    # Apply text cleanup
    if config.dehyphenate:
        combined_text = _dehyphenate_text(combined_text)
    
    if config.collapse_spaces or config.normalize_newlines:
        combined_text = _normalize_whitespace(combined_text, config)
    
    # Detect scanned PDFs and add warnings
    warnings = _detect_scanned_pdf(raw_pages, config)
    
    # Compute statistics
    char_count = len(combined_text)
    non_whitespace_count = len(re.sub(r'\s', '', combined_text))
    non_whitespace_ratio = non_whitespace_count / char_count if char_count > 0 else 0
    
    stats = {
        'char_count': char_count,
        'non_whitespace_count': non_whitespace_count,
        'non_whitespace_ratio': non_whitespace_ratio,
        'page_count': page_count,
        'avg_chars_per_page': char_count / page_count if page_count > 0 else 0
    }
    
    return ExtractedPdfText(
        text=combined_text,
        pages=raw_pages,
        page_count=page_count,
        warnings=warnings,
        stats=stats,
        source_hash=source_hash
    )
