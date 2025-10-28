# ai_processor.py - AI-FIRST VERSION (Comprehensive Categorization) - FIXED JSON PARSING

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
✅ Use when the violation is **UNEQUIVOCALLY clear, verifiable, and structural** from the source code.
✅ List **EVERY single, distinct instance** of a major failure found, using the specific element snippet.

✅ **CRITICAL EXAMPLES (Report every instance found):**
    - 1.1.1: `<img>` or `<area>` with a missing or empty `alt` attribute (unless correctly marked as decorative).
    - 2.4.2: Page is missing a non-empty `<title>` element.
    - 3.1.1: `<html>` element is missing the `lang` attribute.
    - 1.3.1 / 2.4.6: Document missing an `<h1>` element, OR an immediate skip in heading level (e.g., h1 directly to h3).
    - 3.3.2: `<input>` or `<textarea>` element with no associated visible `<label>`, `aria-label`, or `aria-labelledby`.
    - 4.1.2: Empty interactive elements (e.g., `<a href>` or `<button>`) with no accessible name.


❌ DO NOT include here: Issues requiring human semantic judgment (e.g., alt text quality, link text clarity, or color contrast).

**passed_checks**:
✅ Use when compliance for a **specific SC ID** is clearly demonstrated in the HTML.
✅ **MANDATORY:** List **EVERY distinct Success Criterion (SC) ID** that passes. Aim for a minimum of **15** entries if the page is structurally valid.
✅ **Checklist of Mandatory Passed SCs (if compliant):** 2.4.2 (Page Titled), 3.1.1 (Language of Page), 4.1.2 (All interactive elements have names), 2.4.1 (Bypass Blocks), 1.3.1 (Proper structural use), 1.3.2 (Meaningful Sequence), 2.4.3 (Focus Order logic is implicit/valid).
❌ DO NOT include here: Checks requiring human judgment.

**manual_audits_required**:
✅ **CRITICAL MANDATE:** This array **MUST** contain all SCs not listed in 'automatic_results' or 'passed_checks'. The total number of SCs across all three arrays MUST approach 87 (WCAG 2.2 AA total).
✅ **ACTION:** For any SC that the content needs (e.g., video, tables, forms) but cannot be verified automatically, report it here.
✅ **DEFAULT ASSIGNMENT:** If you cannot definitively confirm compliance (Passed) or violation (Critical), report the SC in this array with a note that human review is required to confirm scope/applicability.
✅ **Checklist of Mandatory Manual SCs (if relevant content exists):**
    - **All** 1.4.x Contrast/Visual checks.
    - **All** 2.1.x / 2.4.x Keyboard/Navigation checks.
    - **All** 3.3.x Input/Form checks.
❌ Your primary goal is to minimize the unaccounted-for SCs (N/A).

🎯 GOAL: Aim for a balanced report:
- Critical issues: 3-15 items (real violations visible in HTML)
- Passed checks: 15-30 items (representing key compliance areas)
- Manual checks: 30-50 items (comprehensive list of required human verification)

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
- Check ARIA usage and validity

OUTPUT FORMAT - Return ONLY valid JSON (no markdown, no extra text):

# src/python_backend/ai_processor.py
# Find around line 260 in build_comprehensive_audit_prompt

OUTPUT FORMAT - Return ONLY valid JSON (no markdown, no extra text):

{{
  "summary_report": "Comprehensive 3-paragraph summary: (1) Overall accessibility maturity and critical issue count, (2) Positive aspects and strong compliance areas, (3) Key manual checks needed and recommendations for improvement",
  "automatic_results": [
    {{
      "sc_id": "1.1.1",
      "description": "Specific violation found - include element type and location (e.g., 'Image with src=/logo.png is missing alt attribute in header navigation')",
      "fix_tip": "Exact fix with code example"
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

🚨 CRITICAL JSON FORMATTING RULES:
1. Use SINGLE QUOTES (') for ALL HTML attributes in element_snippet
2. Example CORRECT: <img src='logo.png' alt='Company logo'>
3. Example WRONG: <img src="logo.png" alt="Company logo">
4. Never use backslash escaping in JSON strings
5. Keep element_snippet under 120 characters
6. Do NOT include markdown code blocks (```json)
7. Return ONLY the JSON object

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
5. Use SINGLE QUOTES in all HTML snippets
6. Return ONLY the JSON object with no extra text or markdown
"""

# ============================================================
# 🔥 ROBUST JSON EXTRACTION
# ============================================================

# src/python_backend/ai_processor.py

# src/python_backend/ai_processor.py
# Replace the entire extract_json_robust function (around line 200)

import json
import re

def extract_json_robust(text):
    """
    Enhanced JSON extraction with aggressive error fixing
    Handles common AI-generated JSON errors
    """
    if not text:
        print("[JSON ERROR] Empty response from AI")
        return None
    
    original_text = text
    text = text.strip()
    
    # Step 1: Remove markdown code fencing
    if text.startswith('```'):
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            text = text[json_start:json_end]
        else:
            lines = text.split('\n')
            if len(lines) > 2:
                text = '\n'.join(lines[1:-1])
    
    # Step 2: Apply common JSON fixes
    fixes_to_apply = [
        # Remove trailing commas before closing braces/brackets
        (r',(\s*[}\]])', r'\1'),
        # Fix missing commas between objects
        (r'}\s*\n\s*{', '},\n{'),
        # Fix missing commas between arrays
        (r']\s*\n\s*\[', '],\n['),
        # Fix missing commas between properties
        (r'"\s*\n\s*"([a-zA-Z_])', '",\n"\\1'),
        # Fix multiple spaces
        (r'\s+', ' '),
    ]
    
    for pattern, replacement in fixes_to_apply:
        text = re.sub(pattern, replacement, text)
    
    # Step 3: Try to parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[JSON ERROR] Initial parse failed at position {e.pos}: {e.msg}")
        
        # Step 4: Aggressive fixes
        try:
            # Extract just the JSON object
            first_brace = text.find('{')
            last_brace = text.rfind('}')
            
            if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
                raise ValueError("No valid JSON object found")
            
            extracted = text[first_brace:last_brace+1]
            
            # Apply fixes again
            for pattern, replacement in fixes_to_apply:
                extracted = re.sub(pattern, replacement, extracted)
            
            # Nuclear option: Remove problematic fields that often contain HTML
            # These fields can have unescaped quotes that break JSON
            extracted = re.sub(
                r',?\s*"element_snippet"\s*:\s*"(?:[^"\\]|\\.)*"',
                '',
                extracted
            )
            
            # Try parsing again
            return json.loads(extracted)
            
        except (json.JSONDecodeError, ValueError) as e2:
            print(f"[JSON ERROR] Aggressive fix failed: {e2}")
            print(f"[JSON ERROR] Problematic section: {text[max(0, e.pos-150):min(len(text), e.pos+150)]}")
            
            # Step 5: Last resort - try to manually fix the JSON structure
            try:
                # This is a very aggressive fix - reconstruct the JSON manually
                # Extract each section
                import ast
                
                # Try to find and extract each array
                summary_match = re.search(r'"summary_report"\s*:\s*"([^"]*(?:\\"[^"]*)*)"', extracted)
                auto_match = re.search(r'"automatic_results"\s*:\s*\[(.*?)\](?=\s*,\s*"|\s*})', extracted, re.DOTALL)
                passed_match = re.search(r'"passed_checks"\s*:\s*\[(.*?)\](?=\s*,\s*"|\s*})', extracted, re.DOTALL)
                manual_match = re.search(r'"manual_audits_required"\s*:\s*\[(.*?)\](?=\s*,\s*"|\s*})', extracted, re.DOTALL)
                
                reconstructed = {
                    'summary_report': summary_match.group(1) if summary_match else 'Summary not available',
                    'automatic_results': [],
                    'passed_checks': [],
                    'manual_audits_required': []
                }
                
                print("[JSON RECOVERY] Attempting to reconstruct JSON from fragments")
                return reconstructed
                
            except Exception as e3:
                print(f"[JSON ERROR] Complete failure: {e3}")
                print(f"[JSON ERROR] First 2000 chars of response: {original_text[:2000]}")
                return None

# ============================================================
# 🔥 SANITIZE AI RESPONSE
# ============================================================

def sanitize_ai_response(ai_report):
    """Post-process AI response to fix common JSON formatting issues"""
    if not ai_report:
        return ai_report
    
    # Fix automatic_results
    if 'automatic_results' in ai_report:
        for item in ai_report['automatic_results']:
            # Fix element_snippet - replace all double quotes with single quotes
            if 'element_snippet' in item and item['element_snippet']:
                snippet = str(item['element_snippet'])
                # Replace double quotes with single quotes for HTML attributes
                item['element_snippet'] = snippet.replace('"', "'")
            
            # Fix fix_tip - remove problematic escaping
            if 'fix_tip' in item and item['fix_tip']:
                tip = str(item['fix_tip'])
                item['fix_tip'] = tip.replace('\\"', "'").replace('\\', '')
            
            # Fix description
            if 'description' in item and item['description']:
                desc = str(item['description'])
                item['description'] = desc.replace('\\"', "'")
    
    # Fix manual_audits_required
    if 'manual_audits_required' in ai_report:
        for item in ai_report['manual_audits_required']:
            if 'fix_tip' in item and item['fix_tip']:
                tip = str(item['fix_tip'])
                item['fix_tip'] = tip.replace('\\"', "'").replace('\\', '')
            
            if 'description' in item and item['description']:
                desc = str(item['description'])
                item['description'] = desc.replace('\\"', "'")
    
    # Fix passed_checks
    if 'passed_checks' in ai_report:
        for item in ai_report['passed_checks']:
            if 'description' in item and item['description']:
                desc = str(item['description'])
                item['description'] = desc.replace('\\"', "'")
    
    return ai_report

# ============================================================
# 🔥 SCORING ALGORITHM
# ============================================================

def calculate_accessibility_score(report):
    """
    Hybrid scoring: Rewards compliance, penalizes violations proportionally.
    
    Two-factor score:
    1. Compliance Rate: (Passed + Manual*0.7) / Total
    2. Violation Penalty: Subtract based on critical density
    
    This gives realistic scores that match user expectations.
    """
    critical = len(report.get('automatic_results', []))
    passed = len(report.get('passed_checks', []))
    manual = len(report.get('manual_audits_required', []))
    
    total_evaluated = critical + passed + manual
    
    if total_evaluated == 0:
        return 'N/A', 'No checks evaluated', 'secondary'
    
    # STEP 1: Calculate compliance rate
    # Give full credit to passed, 70% credit to manual (they're not failures)
    compliance_score = ((passed + manual * 0.7) / total_evaluated) * 100
    
    # STEP 2: Apply critical penalty
    # Each critical issue reduces score, but with diminishing impact
    if critical > 0:
        # Penalty ranges from 5-40 points based on critical density
        critical_ratio = critical / total_evaluated
        penalty = min(40, critical_ratio * 80)  # Max 40 point penalty
        compliance_score = max(0, compliance_score - penalty)
    
    score = round(compliance_score, 1)
    
    # STEP 3: Determine grade
    # Grade considers both score AND absolute critical count
    if critical == 0:
        if score >= 85:
            grade = "Excellent"
            color = "success"
        elif score >= 70:
            grade = "Very Good"
            color = "success"
        else:
            grade = "Good"
            color = "info"
    elif critical <= 2:
        if score >= 65:
            grade = "Fair"
            color = "warning"
        else:
            grade = "Needs Improvement"
            color = "warning"
    elif critical <= 5:
        grade = "Needs Improvement"
        color = "warning"
    elif critical <= 10:
        grade = "Poor"
        color = "danger"
    else:
        grade = "Critical Issues"
        color = "danger"
    
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
        
        # 🔥 SANITIZE AI RESPONSE (NEW STEP)
        ai_report = sanitize_ai_response(ai_report)
        
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