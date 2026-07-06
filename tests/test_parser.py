"""
Tests for HTML Parser (Phase 2.2)
"""

import pytest
from bs4 import BeautifulSoup
from ingestion.parser import clean_text, extract_sections, parse_scheme_page

@pytest.fixture
def sample_html():
    return """
    <html>
        <head>
            <title>HDFC Large Cap Fund – Direct Plan Growth | Groww</title>
        </head>
        <body>
            <h1>HDFC Large Cap Fund</h1>
            
            <div class="metrics">
                <table>
                    <tr>
                        <td>NAV</td>
                        <td>₹ 345.67</td>
                    </tr>
                    <tr>
                        <th>Expense Ratio</th>
                        <td>1.04%</td>
                    </tr>
                </table>
            </div>
            
            <div class="details">
                <p>Exit Load: 1% if redeemed within 1 year.</p>
                <span>Minimum SIP</span>
                <span>₹ 500</span>
            </div>
            
            <h2>Fund Overview</h2>
            <p>This is a large cap fund managed by HDFC AMC.</p>
            <ul>
                <li>High risk</li>
                <li>Long term wealth creation</li>
            </ul>
            
            <h2>Download App</h2>
            <p>Get the Groww app now!</p>
        </body>
    </html>
    """

def test_clean_text():
    """Test text cleaning utility."""
    assert clean_text("  Hello \n  World  ") == "Hello World"
    assert clean_text(None) == ""
    assert clean_text("") == ""

def test_parse_scheme_name(sample_html):
    """Test scheme name extraction."""
    result = parse_scheme_page(sample_html, "http://example.com")
    assert result["scheme_name"] == "HDFC Large Cap Fund"

def test_parse_scheme_name_fallback():
    """Test scheme name extraction fallback to title."""
    html = "<html><head><title>Fallback Scheme Name | Groww</title></head><body><p>Content</p></body></html>"
    result = parse_scheme_page(html, "http://example.com")
    assert result["scheme_name"] == "Fallback Scheme Name"

def test_extract_sections_key_metrics(sample_html):
    """Test extraction of specific financial metrics."""
    soup = BeautifulSoup(sample_html, "html.parser")
    sections = extract_sections(soup)
    
    # Find the Key Metrics section
    metrics_sec = next((s for s in sections if s["heading"] == "Key Metrics"), None)
    assert metrics_sec is not None
    
    content = metrics_sec["content"]
    assert "NAV: ₹ 345.67" in content
    assert "Expense Ratio: 1.04%" in content
    assert "Exit Load: 1% if redeemed within 1 year." in content
    assert "Min SIP: ₹ 500" in content

def test_extract_sections_general(sample_html):
    """Test extraction of general paragraphs into sections."""
    soup = BeautifulSoup(sample_html, "html.parser")
    sections = extract_sections(soup)
    
    overview_sec = next((s for s in sections if s["heading"] == "Fund Overview"), None)
    assert overview_sec is not None
    assert "large cap fund managed by HDFC AMC" in overview_sec["content"]
    assert "High risk" in overview_sec["content"]

def test_extract_sections_ignores_noise(sample_html):
    """Test that boilerplate sections like 'Download App' are ignored."""
    soup = BeautifulSoup(sample_html, "html.parser")
    sections = extract_sections(soup)
    
    download_sec = next((s for s in sections if s["heading"] == "Download App"), None)
    assert download_sec is None
