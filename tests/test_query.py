"""
Tests for Query Pipeline (Phase 3)
"""

import pytest
from unittest.mock import MagicMock, patch
from retrieval.guardrails import detect_pii, classify_intent
from generation.prompt_templates import build_context_prompt
from generation.generator import generate_response

def test_detect_pii():
    """Test that regex patterns correctly identify PII."""
    assert detect_pii("My PAN is ABCDE1234F")["has_pii"] == True
    assert detect_pii("Is 1234 5678 9012 safe?")["has_pii"] == True
    assert detect_pii("Call me at 9876543210")["has_pii"] == True
    assert detect_pii("email me at test@example.com")["has_pii"] == True
    
    # Clean query
    assert detect_pii("What is the NAV of HDFC Large Cap?")["has_pii"] == False

def test_classify_intent():
    """Test that advisory queries are blocked while factual ones pass."""
    assert classify_intent("Should I invest in HDFC?")["should_refuse"] == True
    assert classify_intent("Which fund is best?")["should_refuse"] == True
    assert classify_intent("Recommend a good fund")["should_refuse"] == True
    
    # Clean queries
    assert classify_intent("Tell me the expense ratio")["should_refuse"] == False
    assert classify_intent("Who is the fund manager?")["should_refuse"] == False

def test_build_context_prompt():
    """Test that prompt injection works as expected."""
    prompt = build_context_prompt("CHUNK 1 INFO", "WHAT IS NAV?")
    assert "CHUNK 1 INFO" in prompt
    assert "WHAT IS NAV?" in prompt
    assert "INSTRUCTIONS:" in prompt

@patch("generation.generator.get_llm")
@patch("generation.generator.retrieve_context")
def test_generate_response_success(mock_retrieve, mock_get_llm):
    """Test full pipeline success path with mocked LLM."""
    mock_vector_store = MagicMock()
    
    # Mock retrieval to return 1 chunk
    mock_retrieve.return_value = [{"text": "Sample NAV is 100.", "metadata": {}}]
    
    # Mock LLM to return a valid string response
    mock_llm = MagicMock()
    mock_llm_response = MagicMock()
    mock_llm_response.content = "The NAV is 100."
    mock_llm.invoke.return_value = mock_llm_response
    mock_get_llm.return_value = mock_llm
    
    response = generate_response("What is the NAV?", mock_vector_store)
    
    assert response == "The NAV is 100."
    mock_retrieve.assert_called_once()
    mock_llm.invoke.assert_called_once()

@patch("generation.generator.retrieve_context")
def test_generate_response_fallback(mock_retrieve):
    """Test that empty retrieval correctly triggers fallback."""
    mock_vector_store = MagicMock()
    
    # Mock empty retrieval
    mock_retrieve.return_value = []
    
    response = generate_response("What is the NAV?", mock_vector_store)
    
    assert "I don't have this information" in response
    mock_retrieve.assert_called_once()

def test_generate_response_pii_blocked():
    """Test that PII causes an immediate abort."""
    mock_vector_store = MagicMock()
    response = generate_response("What is the NAV for my PAN ABCDE1234F?", mock_vector_store)
    assert "personal information" in response

def test_generate_response_advisory_blocked():
    """Test that advisory phrases cause an immediate abort."""
    mock_vector_store = MagicMock()
    response = generate_response("Should I buy this fund?", mock_vector_store)
    assert "SEBI-registered financial advisor" in response
