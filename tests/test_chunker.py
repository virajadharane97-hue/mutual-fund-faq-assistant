"""
Tests for Text Chunker (Phase 2.3)
"""

import pytest
from ingestion.chunker import chunk_scheme_data

@pytest.fixture
def mock_parsed_data():
    return {
        "scheme_name": "HDFC Large Cap Fund",
        "source_url": "https://groww.in/test",
        "scraped_at": "2024-01-01T00:00:00Z",
        "sections": [
            {
                "heading": "Key Metrics",
                "content": "NAV: 120 | Expense Ratio: 1.04%"
            },
            {
                "heading": "Fund Overview",
                "content": "This is a very long text. " * 100  # Will trigger splitting
            }
        ]
    }

def test_chunk_output_schema(mock_parsed_data):
    """Each chunk must have 'text' and 'metadata' with required keys."""
    chunks = chunk_scheme_data(mock_parsed_data)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert "text" in chunk
        assert "metadata" in chunk
        
        meta = chunk["metadata"]
        assert "source_url" in meta
        assert "scheme_name" in meta
        assert "section_heading" in meta
        assert "scraped_at" in meta
        
        assert meta["scheme_name"] == "HDFC Large Cap Fund"

def test_key_metrics_kept_intact(mock_parsed_data):
    """Key Metrics section should not be split and should have context injected."""
    chunks = chunk_scheme_data(mock_parsed_data)
    
    metrics_chunks = [c for c in chunks if c["metadata"]["section_heading"] == "Key Metrics"]
    
    # Should be exactly 1 chunk
    assert len(metrics_chunks) == 1
    
    # Text should have the context injected
    assert metrics_chunks[0]["text"] == "HDFC Large Cap Fund - Key Metrics: NAV: 120 | Expense Ratio: 1.04%"

def test_general_text_split(mock_parsed_data):
    """Long general text should be split into multiple chunks, each with context injected."""
    chunks = chunk_scheme_data(mock_parsed_data)
    
    overview_chunks = [c for c in chunks if c["metadata"]["section_heading"] == "Fund Overview"]
    
    # Should be split into multiple chunks due to length
    assert len(overview_chunks) > 1
    
    # Each chunk should start with the context prefix
    for chunk in overview_chunks:
        assert chunk["text"].startswith("HDFC Large Cap Fund - Fund Overview: ")
        
def test_empty_parsed_data():
    """Empty or invalid data should return empty list."""
    assert chunk_scheme_data({}) == []
    assert chunk_scheme_data(None) == []
    assert chunk_scheme_data({"scheme_name": "Test"}) == [] # Missing sections
