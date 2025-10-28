# ai_processor.py - AI-FIRST VERSION (Comprehensive Categorization)

import os
import json
import traceback
import requests
import re

from .config import GLOBAL_CONFIG

# SDK Imports
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

# Configuration
AI_SETTINGS = GLOBAL_CONFIG.get('AI_SETTINGS', {})
ACTIVE_PROVIDER = os.environ.get('AI_PROVIDER', AI_SETTINGS.get('ACTIVE_PROVIDER', 'gemini')).lower()
API_KEY_ENV_VAR_NAME = AI_SETTINGS.get('API_KEY_ENV_VAR', 'AI_KEY')
API_KEY = os.environ.get(API_KEY_ENV_VAR_NAME) or os.environ.get('GEMINI_API_KEY')

OPENAI_CLIENT = None
GEMINI_MODEL = None 
SELECTED_MODEL_NAME = None

# Initialize - Use FLASH for speed, PRO for quality
if ACTIVE_PROVIDER == 'gemini' and API_KEY and genai:
    # Try FLASH first for speed, fallback to PRO
    SELECTED_MODEL_NAME = AI_SETTINGS.get('GEMINI_MODEL_FLASH') or AI_SETTINGS.get('GEMINI_MODEL_PRO') or 'gemini-2.0-flash-exp'
    try:
        genai.configure(api_key=API_KEY)
        GEMINI_MODEL = genai.GenerativeModel(SELECTED_MODEL_NAME) 
        print(f"[AI-INIT] Initialized Gemini {SELECTED_MODEL_NAME}")
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
# 🔥 COMPREHENSIVE AI PROMPT (Full Audit)
# ============================================================

def build_comprehensive_audit_prompt(url, html_content):
    """
    🔥 AI-FIRST: Let AI do comprehensive categorization
    This prompt is designed to get better distribution across categories
    """
    
    # Optimize HTML size but keep enough context
    MAX_CHARS = 50000
    truncated_html = html_content[:MAX_CHARS]
    
    return f"""You are an expert WCAG 2.2 Level AA accessibility auditor. Perform a COMPREHENSIVE audit of this page.

🎯 YOUR MISSION: Evaluate as many WCAG 2.2 AA criteria as possible and categorize them correctly.

⚠️ CRITICAL CATEGORIZATION RULES:

**automatic_results** (CRITICAL VIOLATIONS):
✅ Use when you can DEFINITIVELY see a violation in the HTML
✅ Examples:
   - <img> without alt attribute
   - <input> without label/aria-label
   - Empty <button> without accessible name
   - Missing <title> element
   - <html> without lang attribute
   - Broken heading hierarchy (h1 → h3, skipping h2)
   - Form inputs without associated labels
   - Links with no href or text content
   - Duplicate IDs in the DOM
❌ DO NOT include here:
   - Issues requiring visual inspection (contrast, focus indicators)
   - Issues requiring behavioral testing (keyboard navigation)
   - Issues requiring semantic judgment (link text quality, alt text quality)

**passed_checks**:
✅ Use when you see POSITIVE evidence of compliance
✅ Examples:
   - All images HAVE alt attributes (even if quality needs manual review)
   - Page HAS a <title> element with text
   - HTML HAS lang attribute
   - Buttons HAVE text content or aria-label
   - Form inputs HAVE labels (even if association needs verification)
   - Proper heading structure exists (h1 → h2 → h3)
   - Semantic HTML elements used (nav, main, header, footer)
❌ DO NOT assume passing:
   - Only report if you actually SEE the implementation in HTML

**manual_audits_required**:
✅ Use for checks that REQUIRE human judgment or testing
✅ ALWAYS include these if relevant elements exist:
   - Alt text quality/appropriateness (1.1.1 quality check)
   - Color contrast verification (1.4.3, 1.4.11)
   - Keyboard accessibility (2.1.1, 2.1.2)
   - Focus order logic (2.4.3)
   - Link purpose clarity (2.4.4) - if generic links like "click here" exist
   - Focus visibility (2.4.7)
   - Consistent navigation across pages (3.2.3) - multi-page check
   - Form error handling (3.3.1, 3.3.3) - requires submission testing
   - Timing adjustments (2.2.1) - if timers/sessions exist
❌ DO NOT skip manual checks:
   - These are critical for comprehensive audits

🎯 GOAL: Aim for a balanced report:
- Critical issues: 3-10 items (real violations visible in HTML)
- Passed checks: 10-20 items (positive evidence of compliance)
- Manual checks: 8-15 items (requires human verification)

📋 COMPREHENSIVE EVALUATION CHECKLIST:

Images & Media (1.1.1, 1.2.x):
- Check all <img>, <input type="image">, <area> for alt attributes
- Check for <video>, <audio> elements

Structure & Semantics (1.3.x):
- Check heading hierarchy (h1-h6)
- Check for proper landmark usage (nav, main, header, footer, aside)
- Check form label associations
- Check table structure (if tables exist)
- Check list markup (ul, ol, dl)

Text & Contrast (1.4.x):
- Flag for manual contrast checks (always manual)
- Check for images of text

Keyboard & Navigation (2.1.x, 2.4.x):
- Flag keyboard accessibility for manual testing
- Check page <title>
- Check for skip links or landmarks
- Check link text (flag generic text for manual review)
- Check heading descriptiveness (manual)
- Flag focus visibility for manual testing

Forms & Input (3.3.x):
- Check input labels
- Check for autocomplete attributes (1.3.5)
- Flag error handling for manual testing

Language & Parsing (3.1.x, 4.1.x):
- Check <html lang> attribute
- Check for duplicate IDs
- Check ARIA usage and validity

OUTPUT FORMAT - Return ONLY valid JSON (no markdown, no extra text):

{{
  "summary_report": "Comprehensive 3-paragraph summary: (1) Overall accessibility maturity and critical issue count, (2) Positive aspects and strong compliance areas, (3) Key manual checks needed and recommendations for improvement",
  "automatic_results": [
    {{
      "sc_id": "1.1.1",
      "description": "Specific violation found (be precise)",
      "fix_tip": "Exact fix with code example",
      "element_snippet": "Actual HTML from page (max 150 chars)"
    }}
  ],
  "passed_checks": [
    {{
      "sc_id": "2.4.2",
      "description": "What passed and why (with evidence from HTML)"
    }}
  ],
  "manual_audits_required": [
    {{
      "sc_id": "1.4.3",
      "description": "What needs manual verification and why",
      "fix_tip": "How to manually verify and potential fixes"
    }}
  ]
}}

---
🌐 AUDIT TARGET: {url}
📄 HTML CONTENT ({len(truncated_html)} characters):

{truncated_html}

---
⚡ Remember:
1. Be THOROUGH - evaluate ALL applicable WCAG 2.2 AA criteria
2. Be PRECISE - only report definitive violations in automatic_results
3. Be COMPREHENSIVE - include manual checks for items requiring human judgment
4. Be EVIDENCE-BASED - reference actual HTML elements in your findings
5. Return ONLY the JSON object with no markdown formatting
"""

# ============================================================
# 🔥 ROBUST JSON EXTRACTION
# ============================================================

def extract_json_robust(text):
    """Enhanced JSON extraction with better error handling"""
    if not text:
        print("[JSON ERROR] Empty response from AI")
        return None
    
    original_text = text
    text = text.strip()
    
    # Remove markdown code fencing
    if text.startswith('```'):
        # Find JSON block
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            text = text[json_start:json_end]
        else:
            # Try removing just the first and last line
            lines = text.split('\n')
            if len(lines) > 2:
                text = '\n'.join(lines[1:-1])
    
    # Fix common JSON issues
    # Remove trailing commas before closing braces/brackets
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Try to parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[JSON ERROR] Failed to parse at position {e.pos}: {e.msg}")
        print(f"[JSON ERROR] Context around error: ...{text[max(0, e.pos-50):min(len(text), e.pos+50)]}...")
        
        # Last resort: try to find and extract just the JSON object
        try:
            # Find outermost braces
            first_brace = text.find('{')
            last_brace = text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                extracted = text[first_brace:last_brace+1]
                # Try fixing trailing commas again
                extracted = re.sub(r',(\s*[}\]])', r'\1', extracted)
                return json.loads(extracted)
        except:
            pass
        
        print(f"[JSON ERROR] Full problematic response (first 1000 chars): {original_text[:1000]}")
        return None

# ============================================================
# 🔥 SCORING ALGORITHM
# ============================================================

def calculate_accessibility_score(report):
    """
    Improved scoring that considers both quantity and severity
    
    Score = (Passed / Total Evaluated) * 100
    But adjusted based on critical issue severity
    """
    critical = len(report.get('automatic_results', []))
    passed = len(report.get('passed_checks', []))
    manual = len(report.get('manual_audits_required', []))
    
    total = critical + passed + manual
    
    if total == 0:
        return 'N/A', 'No checks evaluated', 'secondary'
    
    # Base score: percentage of passed checks
    base_score = (passed / total) * 100
    
    # Critical issue penalty (each critical issue reduces score)
    if critical > 0:
        # Penalty: reduce score by up to 30 points based on critical density
        critical_density = critical / total
        penalty = min(30, critical_density * 60)  # Max 30 point reduction
        base_score = max(0, base_score - penalty)
    
    score = round(base_score, 1)
    
    # Grading thresholds
    if score >= 90:
        grade = "Excellent"
        color = "success"
    elif score >= 75:
        grade = "Good"
        color = "info"
    elif score >= 60:
        grade = "Fair"
        color = "warning"
    elif score >= 40:
        grade = "Poor"
        color = "warning"
    else:
        grade = "Critical"
        color = "danger"
    
    # Override grade if too many critical issues
    if critical >= 10:
        grade = "Critical Issues"
        color = "danger"
    elif critical >= 5:
        grade = "Needs Improvement"
        color = "warning"
    
    return f"{score}%", grade, color

def calculate_not_applicable(ai_report):
    """Calculate N/A rules by set difference"""
    if not WCAG_ALL_SC_IDS:
        return []

    evaluated = set()
    for cat in ['automatic_results', 'passed_checks', 'manual_audits_required']:
        for item in ai_report.get(cat, []):
            sc_id = item.get('sc_id')
            if sc_id and not sc_id.startswith('AXE:'):  # Exclude AXE custom rules
                evaluated.add(sc_id)
    
    evaluated.discard(None)
    evaluated.discard("")
    
    not_applicable = []
    for sc_id in sorted(WCAG_ALL_SC_IDS - evaluated):
        rule = WCAG_RULE_MAP.get(sc_id, {})
        not_applicable.append({
            "sc_id": sc_id,
            "description": rule.get('ui_description', 'Not applicable to this page')
        })
    
    return not_applicable

# ============================================================
# 🔥 MAIN GENERATION FUNCTION
# ============================================================

def generate_summary(audit_result):
    """
    🔥 AI-FIRST: Comprehensive AI-driven audit with proper categorization
    """
    
    url = audit_result.get('summary', {}).get('scanned_url', 'Unknown')
    html = audit_result.get('raw_html_content', '')
    
    if not html:
        return {
            'error': 'No HTML content',
            'summary': {
                'scanned_url': url,
                'error': 'No HTML',
                'audit_score': 'Error',
                'grade': 'Error',
                'color': 'danger'
            }
        }
    
    if not GEMINI_MODEL or not CONFIG:
        return {
            'error': 'AI not configured',
            'summary': {
                'scanned_url': url,
                'error': 'AI Not Configured',
                'audit_score': 'Error',
                'grade': 'Error',
                'color': 'danger'
            }
        }
    
    try:
        print(f"[AI-AUDIT] Comprehensive analysis: {url}")
        
        # Build comprehensive prompt
        prompt = build_comprehensive_audit_prompt(url, html)
        
        # Configure AI for comprehensive analysis
        config = genai.types.GenerationConfig(
            temperature=0.15,  # Slightly higher for more varied responses
            max_output_tokens=8192,  # Full output for comprehensive audit
            top_k=40,
            top_p=0.95,
        )
        
        # Call AI with timeout
        print(f"[AI-API] Sending request to {SELECTED_MODEL_NAME}...")
        response = GEMINI_MODEL.generate_content(
            prompt,
            generation_config=config,
            request_options={'timeout': 60}  # Increased timeout for comprehensive audit
        )
        
        # Extract and parse response
        ai_text = response.text
        print(f"[AI-API] Received response ({len(ai_text)} chars)")
        
        ai_report = extract_json_robust(ai_text)
        
        if not ai_report:
            raise ValueError("Failed to parse AI response as JSON")
        
        # Validate required fields
        required_fields = ['automatic_results', 'passed_checks', 'manual_audits_required', 'summary_report']
        for field in required_fields:
            if field not in ai_report:
                print(f"[AI-WARN] Missing field: {field}")
                ai_report[field] = [] if field != 'summary_report' else 'Summary not generated'
        
        # Calculate metrics
        score, grade, color = calculate_accessibility_score(ai_report)
        not_applicable = calculate_not_applicable(ai_report)
        
        critical_count = len(ai_report.get('automatic_results', []))
        passed_count = len(ai_report.get('passed_checks', []))
        manual_count = len(ai_report.get('manual_audits_required', []))
        na_count = len(not_applicable)
        
        print(f"[AI-COMPLETE] {url}")
        print(f"  ├─ Critical: {critical_count}")
        print(f"  ├─ Passed: {passed_count}")
        print(f"  ├─ Manual: {manual_count}")
        print(f"  ├─ N/A: {na_count}")
        print(f"  └─ Score: {score} ({grade})")
        
        return {
            'summary': {
                'scanned_url': url,
                'audit_score': score,
                'grade': grade,
                'color': color,
                'critical_count': critical_count,
                'manual_count': manual_count,
                'passed_count': passed_count,
                'ai_summary': ai_report.get('summary_report', 'Comprehensive audit completed'),
            },
            'automatic_results': ai_report.get('automatic_results', []),
            'passed_checks': ai_report.get('passed_checks', []),
            'manual_audits_required': ai_report.get('manual_audits_required', []),
            'not_applicable': not_applicable,
        }
    
    except Exception as e:
        error_msg = f"AI audit failed: {e}"
        print(f"[AI-ERROR] {url}: {error_msg}")
        print(traceback.format_exc())
        
        return {
            'error': error_msg,
            'summary': {
                'scanned_url': url,
                'error': 'Audit Failed',
                'audit_score': 'Error',
                'grade': 'Error',
                'color': 'danger',
                'critical_count': 0,
                'manual_count': 0,
                'passed_count': 0,
            }
        }