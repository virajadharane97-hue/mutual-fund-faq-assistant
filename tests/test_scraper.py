"""
Tests for Web Scraper (Phase 2.1)
"""

import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException, Timeout

from ingestion.scraper import scrape_url, scrape_all_urls
from config.settings import GROWW_URLS, SCRAPER_MAX_RETRIES

@pytest.fixture
def mock_html_content():
    return "<html><head><title>Groww Test Page</title></head><body><h1>HDFC Large Cap</h1><p>Sample content over 1KB " + ("a" * 1024) + "</p></body></html>"

@patch("ingestion.scraper.requests.get")
def test_scrape_url_returns_200(mock_get, mock_html_content):
    """Each URL returns HTTP 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_html_content
    mock_get.return_value = mock_response

    test_url = GROWW_URLS[0]
    result = scrape_url(test_url)

    assert result["status"] == 200
    assert result["url"] == test_url
    assert "html" in result
    assert "scraped_at" in result
    mock_get.assert_called_once()

@patch("ingestion.scraper.requests.get")
def test_scrape_url_html_not_empty(mock_get, mock_html_content):
    """HTML content is >1KB per URL."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_html_content
    mock_get.return_value = mock_response

    test_url = GROWW_URLS[0]
    result = scrape_url(test_url)

    # Content length should be > 1024 bytes
    assert len(result["html"].encode('utf-8')) > 1024

@patch("ingestion.scraper.time.sleep")
@patch("ingestion.scraper.requests.get")
def test_scrape_url_retry_on_failure(mock_get, mock_sleep):
    """Retries up to max configured times on HTTP failure."""
    # Create an exception with a mock response attached
    mock_error_response = MagicMock()
    mock_error_response.status_code = 500
    exception = RequestException("500 Server Error")
    exception.response = mock_error_response
    mock_get.side_effect = exception

    test_url = GROWW_URLS[0]
    result = scrape_url(test_url)

    # Ensure it returns 500 status code
    assert result["status"] == 500
    # Ensure empty HTML on failure
    assert result["html"] == ""
    # Should have called requests.get SCRAPER_MAX_RETRIES times
    assert mock_get.call_count == SCRAPER_MAX_RETRIES
    # Should have slept (SCRAPER_MAX_RETRIES - 1) times for backoff
    assert mock_sleep.call_count == SCRAPER_MAX_RETRIES - 1

@patch("ingestion.scraper.time.sleep")
@patch("ingestion.scraper.requests.get")
def test_scrape_url_timeout(mock_get, mock_sleep):
    """Handles timeout properly and retries."""
    mock_get.side_effect = Timeout("Connection timed out")

    test_url = GROWW_URLS[0]
    result = scrape_url(test_url)

    # For timeouts where response is None, it defaults to 500
    assert result["status"] == 500
    assert result["html"] == ""
    assert mock_get.call_count == SCRAPER_MAX_RETRIES

@patch("ingestion.scraper.scrape_url")
def test_scrape_all_urls(mock_scrape_url):
    """Scrapes all 5 URLs."""
    mock_scrape_url.return_value = {
        "url": "test",
        "html": "test html",
        "scraped_at": "timestamp",
        "status": 200
    }

    results = scrape_all_urls()

    assert len(results) == len(GROWW_URLS)
    assert mock_scrape_url.call_count == len(GROWW_URLS)
