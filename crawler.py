#src/python_backend/crawler.py
import os
import requests
from urllib.parse import urljoin, urlparse
import asyncio
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError 
from bs4 import BeautifulSoup 

# Import config and the shared result dictionary
from .config import AGGREGATED_RESULTS, GLOBAL_CONFIG 


# --- Configuration (Dynamically Loaded) ---
AUDIT_SETTINGS = GLOBAL_CONFIG.get('AUDIT_SETTINGS', {})
# Use configuration with safe fallbacks
MAX_PAGES = AUDIT_SETTINGS.get('MAX_PAGES_TO_SCAN', 5)
MAX_DEPTH = AUDIT_SETTINGS.get('MAX_CRAWL_DEPTH', 1)
# Convert seconds to milliseconds for Playwright, with a default of 45 seconds
PAGE_TIMEOUT_MS = AUDIT_SETTINGS.get('CRAWL_TIMEOUT_SECONDS', 45) * 1000 

# 💡 FIX 1: Correctly map the config variable name
MAX_LINKS_PER_PAGE = AUDIT_SETTINGS.get('SEEDS_PER_PAGE', 2)


# --- Helper Functions ---

def fetch_page_html_sync(page, url):
    """Navigates to a URL and returns the raw HTML content (SYNCHRONOUS)."""
    try:
        # Use configured timeout value
        page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS) 
        html_content = page.content()
        print(f"[DEBUG:HTML] Fetched raw HTML content for {url}. Size: {len(html_content)} bytes.")
        return html_content
    except PlaywrightTimeoutError as e:
        print(f"[AUDIT ERROR] Failed to load or audit {url}: Page failed to load or process: {e}")
        return None
    except Exception as e:
        print(f"[AUDIT ERROR] An unexpected error occurred while fetching {url}: {e}")
        return None


def extract_links_for_crawling(page_url, html_content):
    """
    A simple (non-Playwright) link extractor for found HTML content.
    Uses MAX_LINKS_PER_PAGE from config.
    
    💡 FIX 2: Standardized URL parsing for robustness and domain matching
    """
    base_netloc = urlparse(page_url).netloc
    found_links = set()
    
    max_links = MAX_LINKS_PER_PAGE 
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip fragments, mailto, tel
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(page_url, href)
            # Remove query parameters and fragments to canonicalize the URL
            absolute_url = urlparse(absolute_url)._replace(query='', fragment='').geturl()


            # Check if the link belongs to the same domain (internal link)
            if urlparse(absolute_url).netloc == base_netloc:
                if len(found_links) < max_links: # Use configured max_links
                    found_links.add(absolute_url)
                else:
                    # Stop once the maximum number of seeds is found
                    break 

    except Exception as e:
        print(f"[CRAWL ERROR] Link extraction failed for {page_url}: {e}")
    
    print(f"[CRAWL] Extracted {len(found_links)} internal links for the next depth.")
    return list(found_links)

# --- Main Synchronous Crawler Logic ---

def run_crawler(seed_urls):
    """
    Synchronous entry point called by Flask. Executes all steps synchronously.
    Uses configured MAX_DEPTH and MAX_PAGES.
    """
    # NOTE: Ensure you have 'from python_backend.ai_processor import generate_summary' 
    # in the Flask app or where run_crawler is called, or keep the import here if necessary.
    from python_backend.ai_processor import generate_summary
    
    urls_to_visit = set(seed_urls)
    urls_visited = set()
    all_links_found = set(seed_urls) # To track all discovered links to prevent duplicates

    print("[CRAWL] Starting audit process synchronously.")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            current_depth = 0
            
            # Loop runs until no more URLs to visit OR max depth reached
            while urls_to_visit and current_depth <= MAX_DEPTH: # Use <= to include MAX_DEPTH level
                
                urls_in_current_depth = list(urls_to_visit)
                urls_to_visit.clear()

                # 💡 FIX 3: Adjusted depth log for clarity
                print(f"[CRAWL] Starting audit for Depth {current_depth}. Pages to process: {len(urls_in_current_depth)}")

                for url in urls_in_current_depth:
                    # CRITICAL: Check against total audited pages BEFORE processing
                    if url in urls_visited:
                        continue
                    
                    # Use configured MAX_PAGES
                    if len(urls_visited) >= MAX_PAGES:
                        print(f"[CRAWL] Reached maximum audit page limit of {MAX_PAGES}. Stopping crawl.")
                        # urls_to_visit is already cleared, break inner loop
                        break

                    
                    print(f"[AUDIT] Starting: {url} (Seed: {'Yes' if current_depth == 0 else 'No'})")
                    
                    raw_html = fetch_page_html_sync(page, url)
                    urls_visited.add(url)
                    
                    # --- AI Processing and Aggregation ---
                    final_report = generate_summary({ 
                        'summary': {'scanned_url': url, 'is_seed': current_depth == 0},
                        'raw_html_content': raw_html
                    })
                    
                    AGGREGATED_RESULTS[url] = final_report

                    # --- Link Extraction for Next Depth ---
                    if raw_html and current_depth < MAX_DEPTH: # Check MAX_DEPTH here 
                        new_links = extract_links_for_crawling(url, raw_html) 
                        
                        for link in new_links:
                            if link not in all_links_found and link not in urls_visited:
                                all_links_found.add(link)
                                urls_to_visit.add(link)
                                
                current_depth += 1

            print("[BROWSER] Playwright browser closed.")
            print(f"[AUDIT COMPLETE] Pages audited: {len(urls_visited)}")
            
            return AGGREGATED_RESULTS.copy()
            
    except Exception as e:
        print(f"[CRITICAL CRAWLER ERROR] {str(e)}")
        return {"error": str(e)}