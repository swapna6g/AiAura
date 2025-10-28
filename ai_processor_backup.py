import os
import json
import traceback
import requests

# Import config file
from .config import GLOBAL_CONFIG

# Attempt to import all SDKs
try:
    from openai import OpenAI 
except ImportError:
    OpenAI = None
    
# Try to import Gemini with Schema support
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    from google.api_core import exceptions as google_exceptions
    APIError = google_exceptions.GoogleAPIError
    
    # Try to import Schema - it may not exist in older versions
    try:
        from google.generativeai.types import Schema, Type
        SCHEMA_AVAILABLE = True
    except ImportError:
        Schema = None
        Type = None
        SCHEMA_AVAILABLE = False
        print("Warning: Schema not available in this version of google-generativeai. Using prompt-based JSON mode.")
        
except ImportError as e:
    print(f"DEBUG: Failed to import google.generativeai: {e}")
    genai = None
    APIError = None
    SCHEMA_AVAILABLE = False
    Schema = None
    Type = None
    print("Warning: Google Generative AI SDK not found. Gemini features will be disabled.")

# --- Configuration and Initialization ---

AI_SETTINGS = GLOBAL_CONFIG.get('AI_SETTINGS', {})

# 1. Determine ACTIVE_PROVIDER: Env var overrides config file default
ACTIVE_PROVIDER = os.environ.get('AI_PROVIDER', AI_SETTINGS.get('ACTIVE_PROVIDER', 'gemini')).lower()
# 2. Determine API_KEY: Use env var specified in config
API_KEY_ENV_VAR_NAME = AI_SETTINGS.get('API_KEY_ENV_VAR', 'AI_KEY')
API_KEY = os.environ.get(API_KEY_ENV_VAR_NAME) or os.environ.get('GEMINI_API_KEY') 

# Global SDK Clients
OPENAI_CLIENT = None
GEMINI_MODEL = None 
SELECTED_MODEL_NAME = None 

# Dynamic Initialization
if ACTIVE_PROVIDER == 'openai' and API_KEY and OpenAI:
    SELECTED_MODEL_NAME = AI_SETTINGS.get('OPENAI_MODEL', 'gpt-4o')
    try:
        OPENAI_CLIENT = OpenAI(api_key=API_KEY)
        print(f"[AI-INIT] Successfully initialized OpenAI API using {SELECTED_MODEL_NAME}")
    except Exception as e:
        print(f"Warning: Failed to initialize OpenAI client. Error: {e}")

if ACTIVE_PROVIDER == 'gemini' and API_KEY and genai:
    SELECTED_MODEL_NAME = AI_SETTINGS.get('GEMINI_MODEL_FLASH') or AI_SETTINGS.get('GEMINI_MODEL_PRO') or 'gemini-2.0-flash-exp'
    try:
        genai.configure(api_key=API_KEY)
        GEMINI_MODEL = genai.GenerativeModel(SELECTED_MODEL_NAME) 
        print(f"[AI-INIT] Successfully initialized Gemini API using {SELECTED_MODEL_NAME}")
        if SCHEMA_AVAILABLE:
            print("[AI-INIT] Schema-based JSON mode is available")
        else:
            print("[AI-INIT] Using prompt-based JSON mode (Schema not available)")
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini client. Error: {e}")
        GEMINI_MODEL = None
        
if ACTIVE_PROVIDER == 'ollama':
    SELECTED_MODEL_NAME = AI_SETTINGS.get('OLLAMA_MODEL', 'llama3:8b')

# --- AUDIT REPORT SCHEMA DEFINITION (Conditional) ---
AUDIT_REPORT_SCHEMA = None

if SCHEMA_AVAILABLE and Schema and Type:
    try:
        AUDIT_REPORT_SCHEMA = Schema(
            type=Type.OBJECT, 
            properties={
                'summary_report': Schema(
                    type=Type.STRING, 
                    description="3-paragraph executive summary..."
                ),
                'automatic_results': Schema(
                    type=Type.ARRAY, 
                    description="List of critical violations found automatically.",
                    items=Schema(
                        type=Type.OBJECT, 
                        properties={
                            'sc_id': Schema(type=Type.STRING, description="WCAG SC ID (e.g., 1.1.1)."), 
                            'description': Schema(type=Type.STRING, description="The violation description."), 
                            'fix_tip': Schema(type=Type.STRING, description="Tip to fix the issue."), 
                            'element_snippet': Schema(type=Type.STRING, description="The HTML snippet (max 150 chars)."), 
                        },
                        required=['sc_id', 'description', 'fix_tip']
                    )
                ),
                'passed_checks': Schema(
                    type=Type.ARRAY, 
                    description="List of rules confirmed to be passing.",
                    items=Schema(
                        type=Type.OBJECT, 
                        properties={
                            'sc_id': Schema(type=Type.STRING), 
                            'description': Schema(type=Type.STRING), 
                        },
                        required=['sc_id', 'description']
                    )
                ),
                'manual_audits_required': Schema(
                    type=Type.ARRAY, 
                    description="List of rules requiring manual verification.",
                    items=Schema(
                        type=Type.OBJECT, 
                        properties={
                            'sc_id': Schema(type=Type.STRING), 
                            'description': Schema(type=Type.STRING), 
                            'fix_tip': Schema(type=Type.STRING), 
                        },
                        required=['sc_id', 'description']
                    )
                ),
            },
            required=['summary_report', 'automatic_results', 'passed_checks', 'manual_audits_required']
        )
        print("[AI-INIT] Audit report schema successfully defined")
    except Exception as e:
        print(f"[AI-INIT] Failed to create schema: {e}. Falling back to prompt-based mode.")
        AUDIT_REPORT_SCHEMA = None
        SCHEMA_AVAILABLE = False

# Dynamic Model Configuration Map
MODEL_CONFIG = {
    'ollama': {
        'url': 'http://localhost:11434/api/generate',
        'model': SELECTED_MODEL_NAME, 
        'headers': {'Content-Type': 'application/json'},
        'get_body': lambda prompt: {
            'model': SELECTED_MODEL_NAME, 
            'prompt': prompt,
            'stream': False,
            'format': 'json', 
            'options': {'temperature': 0.1, 'num_ctx': 8192}, 
        },
        'parse_response': lambda data: data.get('response', '').strip(),
    },
    'openai': {
        'model': SELECTED_MODEL_NAME, 
        'client': OPENAI_CLIENT,
        'get_call': lambda prompt: OPENAI_CLIENT.chat.completions.create(
            model=MODEL_CONFIG['openai']['model'],
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}, 
            max_tokens=4096,
        ).choices[0].message.content,
    },
    'gemini': {
        'model': SELECTED_MODEL_NAME, 
        'client': GEMINI_MODEL,
    },
}

CONFIG = MODEL_CONFIG.get(ACTIVE_PROVIDER)

# --- WCAG Map Loading ---
WCAG_ALL_SC_IDS = set()
WCAG_RULE_MAP = {}
WCAG_ALL_RULES = []

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
                    
        print(f"[AI-INIT] Loaded {len(WCAG_ALL_SC_IDS)} WCAG SC IDs for Not Applicable calculation.")
    else:
        print(f"[ERROR] wcag-map.JSON not found at expected path: {map_path}")
except Exception as e:
    print(f"[ERROR] Failed to load wcag-map.JSON: {e}")

# --- Helper Functions ---

def calculate_accessibility_score(report):
    """Calculates weighted accessibility score."""
    critical = len(report.get('automatic_results', []))
    passed = len(report.get('passed_checks', []))
    manual = len(report.get('manual_audits_required', []))
    
    total_checks_evaluated = critical + passed + manual
    
    if total_checks_evaluated == 0:
        return 'N/A', 'No checks evaluated'
    
    score_value = passed / total_checks_evaluated
    score_percentage = round(score_value * 100, 1)
    
    if score_percentage >= 90:
        grade = "Excellent"
    elif score_percentage >= 75:
        grade = "Good"
    elif score_percentage >= 50:
        grade = "Fair"
    else:
        grade = "Poor"
    
    return f"{score_percentage}%", grade

def calculate_not_applicable(ai_report):
    """Determines 'Not Applicable' rules."""
    if not WCAG_ALL_SC_IDS:
        return []

    evaluated_ids = set()
    
    for category in ['automatic_results', 'passed_checks', 'manual_audits_required']:
        for item in ai_report.get(category, []):
            evaluated_ids.add(item.get('sc_id'))

    evaluated_ids.discard(None)
    evaluated_ids.discard("")
    
    not_applicable_ids = WCAG_ALL_SC_IDS - evaluated_ids
    not_applicable_list = []
    
    for sc_id in sorted(list(not_applicable_ids)):
        rule_info = WCAG_RULE_MAP.get(sc_id)
        if rule_info:
            description = (
                rule_info.get('description') or
                rule_info.get('title') or
                rule_info.get('ui_description') or
                'Rule description not found in wcag-map.JSON.'
            )
        else:
            description = 'This rule was not reported by the AI, typically indicating it is Not Applicable.'

        not_applicable_list.append({
            "sc_id": sc_id,
            "description": description
        })
        
    return not_applicable_list

def build_full_audit_prompt(url, html_content):
    """Generates the prompt string requesting structured JSON output."""
    MAX_CHARS_FOR_AI = 75000 
    truncated_html = html_content[:MAX_CHARS_FOR_AI]
    
    return f"""
You are an expert WCAG 2.2 Level AA accessibility auditor. Perform a comprehensive audit on the provided HTML content.

CRITICAL INSTRUCTIONS:

1. **CATEGORY DEFINITIONS (MUST FOLLOW STRICTLY):**

    a) **automatic_results** (Critical Issues):
      - Violations you can DEFINITIVELY confirm from the HTML
      - Must have clear evidence in the code
      - Examples: Missing alt text, missing form labels, improper heading hierarchy
      - DO NOT include issues that require behavioral testing
    
    b) **passed_checks**:
      - Rules where you found POSITIVE evidence of compliance
      - Must have confirmable implementation in HTML
      - Examples: Images have alt attributes, form inputs have labels, proper semantic HTML
      - DO NOT assume passing - only report if you see implementation
    
    c) **manual_audits_required**:
      - Rules that REQUIRE human judgment or cannot be verified from static HTML
      - Examples: Alt text quality, link text clarity, color contrast, keyboard navigation
      - Include when element exists but quality needs human verification
    
    d) **not_applicable**:
      - You do NOT need to report these - they will be calculated automatically

2. **WCAG 2.2 FOCUS:**
    - Evaluate against WCAG 2.2 Level AA criteria
    - Use proper SC IDs format: "1.1.1", "2.4.6", "4.1.2", etc.
    - For general issues: "AXE:general-issue"

3. **EVIDENCE-BASED REPORTING:**
    - Only report what you can SEE in the HTML
    - Provide element_snippet for critical issues (max 150 chars)
    - DO NOT hallucinate issues

4. **OUTPUT FORMAT:**
    Return ONLY valid JSON (no markdown, no extra text):

{{
    "summary_report": "3-paragraph executive summary covering: (1) Critical findings count and severity, (2) Positive compliance observations, (3) Key manual checks needed and overall accessibility maturity",
    "automatic_results": [
      {{
        "sc_id": "1.1.1",
        "description": "Image missing alt attribute",
        "fix_tip": "Add descriptive alt text: <img src='logo.png' alt='Company Name Logo'>",
        "element_snippet": "<img src='images/logo.png' class='header-logo'>"
      }}
    ],
    "passed_checks": [
      {{
        "sc_id": "3.3.2",
        "description": "All form inputs have associated labels"
      }}
    ],
    "manual_audits_required": [
      {{
        "sc_id": "2.4.4",
        "description": "Link purposes: Verify links are understandable in context",
        "fix_tip": "Review links and update to descriptive text"
      }}
    ]
}}

---
AUDIT TARGET: {url}
HTML CONTENT ({len(truncated_html)} characters):
{truncated_html}

Remember: Be thorough but precise. Only report what you can verify from the HTML.
"""

# --- AI Logic ---

def generate_summary(audit_result):
    """Calls the active AI provider to generate the full audit report."""
    
    url = audit_result.get('summary', {}).get('scanned_url', 'Unknown URL')
    default_failure_report = {
        'error': 'AI Audit failed before execution.', 
        'summary': {'scanned_url': url, 'error': 'AI Pre-check Failure', 'audit_score': 'Error'}
    }
    
    # Pre-Execution Validation
    if not CONFIG:
        default_failure_report['error'] = f"AI Integration Failed: Provider '{ACTIVE_PROVIDER}' is not configured."
        return default_failure_report
    
    if ACTIVE_PROVIDER != 'ollama' and not API_KEY:
        default_failure_report['error'] = f"AI Integration Failed: API_KEY missing for '{ACTIVE_PROVIDER}'."
        return default_failure_report

    html_content = audit_result.get('raw_html_content', '')

    if not html_content:
        default_failure_report['error'] = f"AI Audit failed: No HTML content for {url}."
        return default_failure_report

    prompt = build_full_audit_prompt(url, html_content)
    ai_report_text = None

    try:
        print(f"[AI-API] Starting audit using {ACTIVE_PROVIDER} with model {CONFIG.get('model', 'N/A')}...")

        # Execute AI Call
        if ACTIVE_PROVIDER == 'gemini':
            if not GEMINI_MODEL:
                raise ValueError("Gemini client not initialized.")
            
            # Base generation config
            config_with_json = genai.types.GenerationConfig(
                temperature=0.05,
                candidate_count=1,
                top_k=40,
                top_p=0.95,
                max_output_tokens=8192,
            )
            
            # Use Schema mode if available, otherwise rely on prompt
            if SCHEMA_AVAILABLE and AUDIT_REPORT_SCHEMA:
                print("[AI-API] Using structured JSON schema mode")
                response = GEMINI_MODEL.generate_content(
                    prompt, 
                    generation_config=config_with_json,
                    response_mime_type="application/json",
                    response_schema=AUDIT_REPORT_SCHEMA,
                )
            else:
                print("[AI-API] Using prompt-based JSON mode")
                # Enhance prompt to request JSON
                json_prompt = prompt + "\n\nIMPORTANT: Respond with ONLY the JSON object, no other text."
                response = GEMINI_MODEL.generate_content(
                    json_prompt,
                    generation_config=config_with_json,
                )
            
            ai_report_text = response.text
            
        elif ACTIVE_PROVIDER == 'openai':
            ai_report_text = CONFIG['get_call'](prompt)
            
        elif ACTIVE_PROVIDER == 'ollama':
            response = requests.post(
                CONFIG['url'], 
                headers=CONFIG['headers'], 
                json=CONFIG['get_body'](prompt), 
                timeout=180
            )
            response.raise_for_status()
            data = response.json()
            ai_report_text = CONFIG['parse_response'](data)

        # Parse and Process Response
        print(f"[AI-DEBUG] RAW AI RESPONSE (First 500 chars): {ai_report_text[:500] if ai_report_text else 'None'}...") 

        if not ai_report_text:
            raise ValueError("AI returned empty response.")

        # Strip potential Markdown fencing
        if ai_report_text and ai_report_text.strip().startswith('```'):
            ai_report_text = ai_report_text.strip()
            json_start = ai_report_text.find('{')
            json_end = ai_report_text.rfind('}') + 1 
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                ai_report_text = ai_report_text[json_start:json_end]
            else:
                ai_report_text = ai_report_text.strip('```json').strip('```').strip()
        
        ai_report = json.loads(ai_report_text) 
        
        # Map to Frontend Structure
        calculated_score, grade = calculate_accessibility_score(ai_report)
        not_applicable_results = calculate_not_applicable(ai_report)

        final_audit_result = {
            'summary': {
                'scanned_url': url,
                'audit_score': calculated_score,
                'grade': grade,
                'critical_count': len(ai_report.get('automatic_results', [])),
                'manual_count': len(ai_report.get('manual_audits_required', [])),
                'passed_count': len(ai_report.get('passed_checks', [])),
                'ai_summary': ai_report.get('summary_report', 'AI Summary not generated.'), 
            },
            'automatic_results': ai_report.get('automatic_results', []),
            'passed_checks': ai_report.get('passed_checks', []),
            'manual_audits_required': ai_report.get('manual_audits_required', []),
            'not_applicable': not_applicable_results,
        }
        
        print(f"[AI-API] Audit complete. Critical: {final_audit_result['summary']['critical_count']}, Grade: {grade}")
        return final_audit_result

    except (requests.exceptions.RequestException, APIError, ValueError) as e:
        error_msg = f"AI connectivity error ({ACTIVE_PROVIDER}): {e}"
        print(f"[AI ERROR] {error_msg}")
        default_failure_report['error'] = error_msg
        default_failure_report['summary']['error'] = 'AI Connectivity Error'
        return default_failure_report
    
    except json.JSONDecodeError as e:
        error_msg = f"AI JSON parsing failed: {e}. Raw: {ai_report_text[:200] if ai_report_text else 'N/A'}"
        print(f"[AI ERROR] {error_msg}")
        default_failure_report['error'] = error_msg
        default_failure_report['summary']['error'] = 'AI JSON Parse Error'
        return default_failure_report
    
    except Exception as e:
        error_msg = f"Unknown error for {url}: {e}\n{traceback.format_exc()}"
        print(f"[AI ERROR] {error_msg}")
        default_failure_report['error'] = error_msg
        default_failure_report['summary']['error'] = 'AI Critical Error'
        return default_failure_report