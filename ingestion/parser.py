"""
HTML Parser for Groww Scheme Pages

Parses raw HTML from Groww and extracts structured sections
(scheme name, NAV, expense ratio, exit load, etc.).
"""

import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean whitespace and remove empty strings."""
    if not text:
        return ""
    return " ".join(text.split()).strip()

def extract_sections(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Extract individual fact sections from parsed HTML."""
    sections = []
    
    # Robust text-based extraction for known fields
    fields_to_find = {
        "NAV": ["NAV", "Net Asset Value"],
        "Expense Ratio": ["Expense Ratio", "TER"],
        "Exit Load": ["Exit Load"],
        "Min SIP": ["Min. SIP", "Minimum SIP"],
        "Min Lumpsum": ["Min. Lumpsum", "Minimum Lumpsum", "Min Lumpsum"],
        "Benchmark": ["Benchmark", "Index"],
        "Riskometer": ["Risk", "Riskometer"],
        "Fund Manager": ["Fund Manager", "Managed By"],
        "AUM": ["AUM", "Fund Size"],
        "Category": ["Category", "Fund Category"]
    }
    
    extracted_fields = {}
    
    # Look for specific fields via labels
    for element in soup.find_all(string=True):
        text = clean_text(element)
        if not text:
            continue
            
        for field, keywords in fields_to_find.items():
            if field in extracted_fields:
                continue
                
            for kw in keywords:
                if kw.lower() == text.lower() or text.lower().startswith(kw.lower() + ":"):
                    parent = element.parent
                    
                    # Check next sibling
                    next_node = parent.find_next_sibling()
                    if next_node:
                        val = clean_text(next_node.get_text())
                        if val and len(val) < 100:
                            extracted_fields[field] = val
                            break
                            
                    # Check table cells
                    if parent.name in ['td', 'th']:
                        next_td = parent.find_next('td')
                        if next_td:
                            val = clean_text(next_td.get_text())
                            if val and len(val) < 100:
                                extracted_fields[field] = val
                                break
                    
                    # Check next text element visually
                    next_text_el = element.find_next(string=True)
                    if next_text_el:
                        val = clean_text(next_text_el)
                        if val and len(val) < 100:
                            extracted_fields[field] = val
                            break
                    break
                    
    # Extract general text content grouped by headings
    headings = soup.find_all(['h2', 'h3'])
    general_sections = []
    
    for h in headings:
        heading_text = clean_text(h.get_text())
        if not heading_text:
            continue
            
        content = []
        node = h.find_next_sibling()
        while node and node.name not in ['h1', 'h2', 'h3']:
            if node.name in ['p', 'div', 'ul', 'ol', 'table', 'span']:
                text = clean_text(node.get_text(separator=" "))
                if text:
                    content.append(text)
            node = node.find_next_sibling()
            
        if content:
            general_sections.append({
                "heading": heading_text,
                "content": " ".join(content)
            })
            
    # Combine fields into a key metrics section
    if extracted_fields:
        metrics_content = " | ".join([f"{k}: {v}" for k, v in extracted_fields.items()])
        sections.append({
            "heading": "Key Metrics",
            "content": metrics_content
        })
        
    for sec in general_sections:
        # Filter out boilerplate / noise headings
        lower_heading = sec["heading"].lower()
        if any(noise in lower_heading for noise in ["download app", "about groww", "cookie", "similar funds", "customers also viewed"]):
            continue
        sections.append(sec)
        
    # Fallback if no sections extracted
    if not sections:
        paragraphs = soup.find_all('p')
        text = " ".join([clean_text(p.get_text()) for p in paragraphs])
        if text:
            sections.append({
                "heading": "General Information",
                "content": text
            })
            
    return sections

def parse_scheme_page(html: str, source_url: str) -> Dict[str, Any]:
    """Parse Groww scheme page HTML into structured sections."""
    if not html:
        return {"scheme_name": "Unknown", "source_url": source_url, "sections": []}
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Attempt to extract scheme name from h1 or title
    scheme_name = "Unknown Scheme"
    h1 = soup.find("h1")
    if h1:
        scheme_name = clean_text(h1.get_text())
    elif soup.title:
        title_text = clean_text(soup.title.get_text())
        scheme_name = title_text.split("|")[0].strip() if "|" in title_text else title_text
        
    return {
        "scheme_name": scheme_name,
        "source_url": source_url,
        "sections": extract_sections(soup)
    }

if __name__ == "__main__":
    import sys
    import os
    
    # Make sure we can import from ingestion
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ingestion.scraper import scrape_all_urls
    
    logging.basicConfig(level=logging.INFO)
    logger.info("Running parser directly to fetch and parse data...")
    
    # Scrape data
    raw_results = scrape_all_urls()
    
    # Parse data
    parsed_results = []
    for raw in raw_results:
        if raw["status"] == 200 and raw["html"]:
            parsed = parse_scheme_page(raw["html"], raw["url"])
            parsed_results.append(parsed)
            logger.info(f"Parsed {len(parsed['sections'])} sections for {parsed['scheme_name']}")
        else:
            logger.warning(f"Skipping {raw['url']} due to bad status or empty HTML")
            
    # Save parsed data to file
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    output_file = os.path.join(data_dir, "parsed_outputs.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parsed_results, f, indent=4, ensure_ascii=False)
        
    logger.info(f"Successfully saved parsed data to {output_file}")
