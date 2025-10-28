# crawler.py - FIXED PARALLEL VERSION

import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading

from .config import AGGREGATED_RESULTS, GLOBAL_CONFIG

# Configuration
AUDIT_SETTINGS = GLOBAL_CONFIG.get('AUDIT_SETTINGS', {})
MAX_PAGES = AUDIT_SETTINGS.get('MAX_PAGES_TO_SCAN', 5)
MAX_DEPTH = AUDIT_SETTINGS.get('MAX_CRAWL_DEPTH', 1)
PAGE_TIMEOUT_MS = AUDIT_SETTINGS.get('CRAWL_TIMEOUT_SECONDS', 45) * 1000
MAX_LINKS_PER_PAGE = AUDIT_SETTINGS.get('SEEDS_PER_PAGE', 2)

MAX_WORKERS = 2  # 🔥 Reduced to 2 for stability


def fetch_page_html_sync(page, url):
    """Fetch HTML with timeout"""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
        html = page.content()
        print(f"[FETCH] {len(html)} bytes from {url[:50]}...")
        return html
    except PlaywrightTimeoutError:
        print(f"[TIMEOUT] {url}")
        return None
    except Exception as e:
        print(f"[ERROR] Fetch failed for {url}: {e}")
        return None


def extract_links_for_crawling(page_url, html_content):
    """Extract internal links"""
    base_netloc = urlparse(page_url).netloc
    found_links = set()
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            if len(found_links) >= MAX_LINKS_PER_PAGE:
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


def audit_single_page_with_own_browser(url, is_seed=False):
    """
    🔥 FIX: Each thread gets its own Playwright instance
    This avoids the "cannot switch to a different thread" error
    """
    from .ai_processor import generate_summary
    
    try:
        print(f"[START] {url[:60]} (Thread: {threading.current_thread().name})")
        start = time.time()
        
        # 🔥 Create a new Playwright instance per thread
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            raw_html = fetch_page_html_sync(page, url)
            
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
            links = extract_links_for_crawling(url, raw_html)
            
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


def run_crawler(seed_urls):
    """🔥 Parallel crawler with thread-safe Playwright"""
    
    urls_to_visit = set(seed_urls)
    urls_visited = set()
    all_links_found = set(seed_urls)
    
    print(f"[CRAWL] Starting PARALLEL audit")
    print(f"[CRAWL] Seeds: {len(seed_urls)}, Workers: {MAX_WORKERS}, Max Pages: {MAX_PAGES}, Max Depth: {MAX_DEPTH}")
    start_time = time.time()
    
    try:
        depth = 0
        
        while urls_to_visit and depth <= MAX_DEPTH:
            if len(urls_visited) >= MAX_PAGES:
                print(f"[LIMIT] Reached {MAX_PAGES} pages limit")
                break
            
            urls_batch = list(urls_to_visit)
            urls_to_visit.clear()
            
            remaining = MAX_PAGES - len(urls_visited)
            urls_batch = urls_batch[:remaining]
            
            print(f"\n[DEPTH {depth}] Processing {len(urls_batch)} pages in parallel...")
            
            # 🔥 PARALLEL EXECUTION - Each thread gets its own browser
            with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="AuditWorker") as executor:
                futures = {
                    executor.submit(audit_single_page_with_own_browser, url, depth == 0): url
                    for url in urls_batch if url not in urls_visited
                }
                
                for future in as_completed(futures):
                    url = futures[future]
                    
                    try:
                        result_url, report, new_links = future.result()
                        
                        urls_visited.add(result_url)
                        AGGREGATED_RESULTS[result_url] = report
                        
                        # Queue links for next depth
                        if depth < MAX_DEPTH:
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