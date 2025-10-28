# ai_processor.py - OPTIMIZED VERSION (Drop-in Replacement)

import os
import json
import traceback
import requests
import re
from bs4 import BeautifulSoup

from .config import GLOBAL_CONFIG

# SDK Imports (same as before)
try:
    from openai import OpenAI 
except ImportError:
    OpenAI = None
    
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    from google.api_core import exceptions as google_exceptions
    APIError = google_exceptions.GoogleAPIError
    
    try:
        from google.generativeai.types import Schema, Type
        SCHEMA_AVAILABLE = True
    except ImportError:
        Schema = None
        Type = None
        SCHEMA_AVAILABLE = False
        
except ImportError as e:
    genai = None
    APIError = None
    SCHEMA_AVAILABLE = False
    Schema = None
    Type = None

# Configuration (same as before)
AI_SETTINGS = GLOBAL_CONFIG.get('AI_SETTINGS', {})
ACTIVE_PROVIDER = os.environ.get('AI_PROVIDER', AI_SETTINGS.get('ACTIVE_PROVIDER', 'gemini')).lower()
API_KEY_ENV_VAR_NAME = AI_SETTINGS.get('API_KEY_ENV_VAR', 'AI_KEY')
API_KEY = os.environ.get(API_KEY_ENV_VAR_NAME) or os.environ.get('GEMINI_API_KEY')

OPENAI_CLIENT = None
GEMINI_MODEL = None 
SELECTED_MODEL_NAME = None

# Initialize (use FLASH for speed)
if ACTIVE_PROVIDER == 'gemini' and API_KEY and genai:
    SELECTED_MODEL_NAME = AI_SETTINGS.get('GEMINI_MODEL_FLASH') or 'gemini-2.0-flash-exp'
    try:
        genai.configure(api_key=API_KEY)
        GEMINI_MODEL = genai.GenerativeModel(SELECTED_MODEL_NAME) 
        print(f"[AI-INIT] Initialized Gemini {SELECTED_MODEL_NAME} (optimized)")
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini: {e}")
        GEMINI_MODEL = None

MODEL_CONFIG = {
    'gemini': {
        'model': SELECTED_MODEL_NAME, 
        'client': GEMINI_MODEL,
    },
}

CONFIG = MODEL_CONFIG.get(ACTIVE_PROVIDER)

# WCAG Map Loading
WCAG_ALL_SC_IDS = set()
WCAG_RULE_MAP = {}

try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(script_dir, '..', 'wcag-map.JSON')
    
    if os.path.exists(map_path):
        with open(map_path, 'r') as f:
            WCAG_ALL_RULES = json.load(f)
            for rule in WCAG_ALL_RULES:
                sc_id = rule.get('sc_id')
                if sc_id:
                    WCAG_RULE_MAP[sc_id] = rule
                    WCAG_ALL_SC_IDS.add(sc_id)
        print(f"[AI-INIT] Loaded {len(WCAG_ALL_SC_IDS)} WCAG rules")
except Exception as e:
    print(f"[ERROR] Failed to load wcag-map.JSON: {e}")

# ============================================================
# 🔥 STATIC RULE CHECKS (NEW - Hybrid Approach)
# ============================================================

STATIC_CHECKS = {
    "1.1.1": {
        "name": "Images missing alt",
        "check_func": lambda soup: soup.find_all('img', alt=False),
        "fix": "Add alt attribute to images"
    },
    "2.4.2": {
        "name": "Page missing title",
        "check_func": lambda soup: not soup.find('title') or not soup.find('title').string,
        "fix": "Add <title> element to <head>"
    },
    "3.1.1": {
        "name": "HTML missing lang",
        "check_func": lambda soup: not soup.find('html', lang=True),
        "fix": "Add lang='en' to <html> tag"
    },
    "4.1.2": {
        "name": "Empty buttons",
        "check_func": lambda soup: [b for b in soup.find_all('button') if not b.get_text(strip=True) and not b.get('aria-label')],
        "fix": "Add text or aria-label to buttons"
    }
}

def run_static_checks(html_content):
    """🔥 Fast pre-screening using BeautifulSoup"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    automatic_results = []
    passed_checks = []
    
    for sc_id, check in STATIC_CHECKS.items():
        try:
            result = check["check_func"](soup)
            
            if isinstance(result, bool):
                # Boolean check (like title check)
                if result:  # True means violation
                    automatic_results.append({
                        "sc_id": sc_id,
                        "description": check["name"],
                        "fix_tip": check["fix"],
                        "element_snippet": "N/A"
                    })
                else:
                    passed_checks.append({
                        "sc_id": sc_id,
                        "description": f"Passed: {check['name']}"
                    })
            elif isinstance(result, list) and result:
                # Element list (like images)
                for elem in result[:3]:  # Max 3 examples
                    automatic_results.append({
                        "sc_id": sc_id,
                        "description": check["name"],
                        "fix_tip": check["fix"],
                        "element_snippet": str(elem)[:150]
                    })
            elif isinstance(result, list):
                # Empty list means passed
                passed_checks.append({
                    "sc_id": sc_id,
                    "description": f"Passed: {check['name']}"
                })
        except Exception as e:
            print(f"[STATIC ERROR] {sc_id}: {e}")
    
    # Add standard manual checks
    manual_checks = [
        {"sc_id": "1.4.3", "description": "Verify color contrast (4.5:1)", "fix_tip": "Use contrast checker tool"},
        {"sc_id": "2.1.1", "description": "Test keyboard accessibility", "fix_tip": "Navigate with Tab/Enter keys"},
        {"sc_id": "2.4.4", "description": "Verify link text clarity", "fix_tip": "Ensure links are descriptive"},
    ]
    
    print(f"[STATIC] Found {len(automatic_results)} issues, {len(passed_checks)} passed")
    
    return {
        "automatic_results": automatic_results,
        "passed_checks": passed_checks,
        "manual_audits_required": manual_checks
    }

# ============================================================
# 🔥 FOCUSED AI PROMPT (Smaller, Faster)
# ============================================================

def build_focused_prompt(url, html_content, static_results):
    """🔥 Reduced prompt size for speed"""
    
    truncated_html = html_content[:25000]  # Reduced from 75000
    
    return f"""WCAG 2.2 Quick Audit

Static checks found:
- {len(static_results['automatic_results'])} critical issues
- {len(static_results['passed_checks'])} passed checks

Find ADDITIONAL issues not caught by static checks.

Focus: Semantic HTML, ARIA, form labels, headings

Return ONLY JSON (no markdown):
{{
    "summary_report": "1-2 sentence summary",
    "additional_automatic_results": [{{"sc_id": "X.X.X", "description": "Issue", "fix_tip": "Fix", "element_snippet": "HTML"}}],
    "additional_passed_checks": [{{"sc_id": "X.X.X", "description": "Passed check"}}]
}}

URL: {url}
HTML ({len(truncated_html)} chars):
{truncated_html}
"""

# ============================================================
# 🔥 ROBUST JSON PARSER
# ============================================================

def extract_json(text):
    """🔥 Fixed JSON extraction"""
    if not text:
        return None
    
    text = text.strip()
    
    # Remove markdown
    if text.startswith('```'):
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            text = text[start:end]
    
    # Fix trailing commas
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[JSON ERROR] {e}: {text[:300]}")
        return None

# ============================================================
# 🔥 IMPROVED SCORING
# ============================================================

def calculate_accessibility_score(report):
    """🔥 Better scoring formula"""
    critical = len(report.get('automatic_results', []))
    passed = len(report.get('passed_checks', []))
    manual = len(report.get('manual_audits_required', []))
    
    total = critical + passed + manual
    
    if total == 0:
        return 'N/A', 'No checks', 'secondary'
    
    score = round((passed / total) * 100, 1)
    
    if score >= 95:
        return f"{score}%", "Excellent", "success"
    elif score >= 80:
        return f"{score}%", "Good", "info"
    elif score >= 60:
        return f"{score}%", "Fair", "warning"
    else:
        return f"{score}%", "Poor", "danger"

def calculate_not_applicable(ai_report):
    """Calculate N/A rules"""
    if not WCAG_ALL_SC_IDS:
        return []

    evaluated = set()
    for cat in ['automatic_results', 'passed_checks', 'manual_audits_required']:
        for item in ai_report.get(cat, []):
            evaluated.add(item.get('sc_id'))
    
    evaluated.discard(None)
    evaluated.discard("")
    
    not_applicable = []
    for sc_id in sorted(WCAG_ALL_SC_IDS - evaluated):
        rule = WCAG_RULE_MAP.get(sc_id, {})
        not_applicable.append({
            "sc_id": sc_id,
            "description": rule.get('ui_description', 'Not applicable')
        })
    
    return not_applicable

# ============================================================
# 🔥 MAIN FUNCTION (Optimized)
# ============================================================

def generate_summary(audit_result):
    """🔥 Hybrid: Static checks + AI validation"""
    
    url = audit_result.get('summary', {}).get('scanned_url', 'Unknown')
    html = audit_result.get('raw_html_content', '')
    
    if not html:
        return {'error': 'No HTML', 'summary': {'scanned_url': url, 'audit_score': 'Error'}}
    
    try:
        # Step 1: Fast static checks
        print(f"[AUDIT] Static checks: {url}")
        static = run_static_checks(html)
        
        # Step 2: Optional AI validation
        ai_extra = {"additional_automatic_results": [], "additional_passed_checks": [], "summary_report": ""}
        
        if GEMINI_MODEL:
            try:
                print(f"[AI] Requesting validation...")
                prompt = build_focused_prompt(url, html, static)
                
                config = genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=3072,
                )
                
                response = GEMINI_MODEL.generate_content(
                    prompt,
                    generation_config=config,
                    request_options={'timeout': 25}
                )
                
                ai_extra = extract_json(response.text) or ai_extra
                print(f"[AI] Found {len(ai_extra.get('additional_automatic_results', []))} extra issues")
            except Exception as e:
                print(f"[AI WARN] Validation failed: {e}")
        
        # Step 3: Merge results
        all_auto = static['automatic_results'] + ai_extra.get('additional_automatic_results', [])
        all_passed = static['passed_checks'] + ai_extra.get('additional_passed_checks', [])
        all_manual = static['manual_audits_required']
        
        # Deduplicate
        seen = set()
        unique_auto = []
        for item in all_auto:
            if item['sc_id'] not in seen:
                unique_auto.append(item)
                seen.add(item['sc_id'])
        
        seen_passed = set()
        unique_passed = []
        for item in all_passed:
            if item['sc_id'] not in seen_passed:
                unique_passed.append(item)
                seen_passed.add(item['sc_id'])
        
        # Calculate score
        report = {
            'automatic_results': unique_auto,
            'passed_checks': unique_passed,
            'manual_audits_required': all_manual
        }
        
        score, grade, color = calculate_accessibility_score(report)
        not_app = calculate_not_applicable(report)
        
        return {
            'summary': {
                'scanned_url': url,
                'audit_score': score,
                'grade': grade,
                'color': color,
                'critical_count': len(unique_auto),
                'manual_count': len(all_manual),
                'passed_count': len(unique_passed),
                'ai_summary': ai_extra.get('summary_report', 'Audit completed'),
            },
            'automatic_results': unique_auto,
            'passed_checks': unique_passed,
            'manual_audits_required': all_manual,
            'not_applicable': not_app,
        }
    
    except Exception as e:
        print(f"[ERROR] {url}: {e}\n{traceback.format_exc()}")
        return {
            'error': str(e),
            'summary': {
                'scanned_url': url,
                'error': 'Failed',
                'audit_score': 'Error',
                'grade': 'Error',
                'color': 'danger'
            }
        }