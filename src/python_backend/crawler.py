# crawler.py - ENHANCED WITH DYNAMIC CONFIG

import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading

from .config import AGGREGATED_RESULTS, GLOBAL_CONFIG

# 🆕 LOAD DEFAULT CONFIGURATION
AUDIT_SETTINGS = GLOBAL_CONFIG.get('AUDIT_SETTINGS', {})
DEFAULT_MAX_PAGES = AUDIT_SETTINGS.get('MAX_PAGES_TO_SCAN', 5)
DEFAULT_MAX_DEPTH = AUDIT_SETTINGS.get('MAX_CRAWL_DEPTH', 1)
DEFAULT_PAGE_TIMEOUT_MS = AUDIT_SETTINGS.get('CRAWL_TIMEOUT_SECONDS', 45) * 1000
DEFAULT_MAX_LINKS_PER_PAGE = AUDIT_SETTINGS.get('MAX_LINKS_PER_PAGE', 5)

MAX_WORKERS = 3


def fetch_page_html_sync(page, url, timeout_ms):
    """Fetch HTML with timeout"""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        html = page.content()
        print(f"[FETCH] {len(html)} bytes from {url[:50]}...")
        return html
    except PlaywrightTimeoutError:
        print(f"[TIMEOUT] {url}")
        return None
    except Exception as e:
        print(f"[ERROR] Fetch failed for {url}: {e}")
        return None


def extract_links_for_crawling(page_url, html_content, max_links):
    """Extract internal links"""
    base_netloc = urlparse(page_url).netloc
    found_links = set()
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            if len(found_links) >= max_links:
                break
                
            href = a_tag['href']
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            
            absolute_url = urljoin(page_url, href)
            absolute_url = urlparse(absolute_url)._replace(query='', fragment='').geturl()
            
            if urlparse(absolute_url).netloc == base_netloc:
                found_links.add(absolute_url)

    except Exception as e:
        print(f"[LINK ERROR] {page_url}: {e}")
    
    return list(found_links)


def audit_single_page_with_own_browser(url, is_seed, config):
    """
    Audit single page with custom configuration
    """
    from .ai_processor import generate_summary
    
    try:
        print(f"[START] {url[:60]} (Thread: {threading.current_thread().name})")
        start = time.time()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            raw_html = fetch_page_html_sync(page, url, config['timeout_ms'])
            
            if not raw_html:
                browser.close()
                return url, {
                    'error': 'Failed to fetch HTML',
                    'summary': {'scanned_url': url, 'error': 'Fetch Failed', 'audit_score': 'Error'}
                }, []
            
            # Run audit
            report = generate_summary({
                'summary': {'scanned_url': url, 'is_seed': is_seed},
                'raw_html_content': raw_html
            })
            
            # Extract links
            links = extract_links_for_crawling(url, raw_html, config['max_links_per_page'])
            
            browser.close()
            
            elapsed = time.time() - start
            critical_count = report.get('summary', {}).get('critical_count', 0)
            print(f"[DONE] {url[:60]} in {elapsed:.1f}s (Critical: {critical_count})")
            
            return url, report, links
        
    except Exception as e:
        print(f"[ERROR] Audit failed for {url}: {e}")
        import traceback
        traceback.print_exc()
        return url, {
            'error': str(e),
            'summary': {'scanned_url': url, 'error': 'Audit Exception', 'audit_score': 'Error'}
        }, []


def run_crawler(seed_urls, custom_config=None):
    """
    🆕 Enhanced crawler with dynamic configuration
    
    Args:
        seed_urls: List of URLs to crawl
        custom_config: Optional dict with custom settings
            - max_links_per_page: int (1-10)
    """
    
    # 🆕 BUILD CONFIGURATION
    config = {
        'max_pages': DEFAULT_MAX_PAGES,
        'max_depth': DEFAULT_MAX_DEPTH,
        'timeout_ms': DEFAULT_PAGE_TIMEOUT_MS,
        'max_links_per_page': DEFAULT_MAX_LINKS_PER_PAGE
    }
    
    # 🆕 APPLY CUSTOM CONFIG IF PROVIDED
    if custom_config:
        if 'max_links_per_page' in custom_config:
            max_links = custom_config['max_links_per_page']
            if 1 <= max_links <= 10:
                config['max_links_per_page'] = max_links
                print(f"[CONFIG] Using custom max_links_per_page: {max_links}")
    
    # 🆕 CALCULATE MAX PAGES BASED ON SEED COUNT
    # Each seed URL gets up to 5 pages (itself + 4 crawled)
    config['max_pages'] = len(seed_urls) * 5
    
    urls_to_visit = set(seed_urls)
    urls_visited = set()
    all_links_found = set(seed_urls)
    
    print(f"[CRAWL] Starting PARALLEL audit")
    print(f"[CRAWL] Seeds: {len(seed_urls)}, Workers: {MAX_WORKERS}")
    print(f"[CRAWL] Max Pages: {config['max_pages']}, Max Depth: {config['max_depth']}")
    print(f"[CRAWL] Max Links Per Page: {config['max_links_per_page']}")
    start_time = time.time()
    
    try:
        depth = 0
        
        while urls_to_visit and depth <= config['max_depth']:
            if len(urls_visited) >= config['max_pages']:
                print(f"[LIMIT] Reached {config['max_pages']} pages limit")
                break
            
            urls_batch = list(urls_to_visit)
            urls_to_visit.clear()
            
            remaining = config['max_pages'] - len(urls_visited)
            urls_batch = urls_batch[:remaining]
            
            print(f"\n[DEPTH {depth}] Processing {len(urls_batch)} pages in parallel...")
            
            with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="AuditWorker") as executor:
                futures = {
                    executor.submit(audit_single_page_with_own_browser, url, depth == 0, config): url
                    for url in urls_batch if url not in urls_visited
                }
                
                for future in as_completed(futures):
                    url = futures[future]
                    
                    try:
                        result_url, report, new_links = future.result()
                        
                        urls_visited.add(result_url)
                        AGGREGATED_RESULTS[result_url] = report
                        
                        # Queue links for next depth
                        if depth < config['max_depth']:
                            for link in new_links:
                                if link not in all_links_found and link not in urls_visited:
                                    all_links_found.add(link)
                                    urls_to_visit.add(link)
                                    
                    except Exception as e:
                        print(f"[TASK ERROR] Failed to process {url}: {e}")
                        urls_visited.add(url)
                        AGGREGATED_RESULTS[url] = {
                            'error': str(e),
                            'summary': {'scanned_url': url, 'error': 'Processing Failed'}
                        }
            
            depth += 1
        
        elapsed = time.time() - start_time
        print(f"\n[COMPLETE] Audited {len(urls_visited)} pages in {elapsed:.1f}s")
        print(f"[PERFORMANCE] Average: {elapsed/len(urls_visited):.1f}s per page")
        
        return AGGREGATED_RESULTS.copy()
        
    except Exception as e:
        print(f"[CRITICAL ERROR] Crawler failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}