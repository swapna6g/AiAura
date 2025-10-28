import os
import json
from functools import lru_cache

# Aggregator for results (shared by crawler.py and the main app)
AGGREGATED_RESULTS = {}

# --- Configuration Loading ---

@lru_cache(maxsize=1) 
def get_global_config():
    """Loads configuration from config.json located in the parent directory (src/)."""
    try:
        # Resolve path to config.json (assuming it's in the 'src' directory, parent of 'python_backend')
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, '..', 'config.json') 
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            print(f"[CONFIG] Successfully loaded configuration from {config_path}")
            return config_data
        else:
            print(f"[ERROR] config.json not found at {config_path}. Using hardcoded fallback defaults.")
            # Fallback structure (should match your expected config.json structure)
            return {
                    "AUDIT_SETTINGS": {
                    "MAX_PAGES_TO_SCAN": 100,
                    "MAX_CRAWL_DEPTH": 1,
                    "MAX_LINKS_PER_PAGE": 5,
                    "CRAWL_TIMEOUT_SECONDS": 45
                },
                 "AI_SETTINGS": {
                    "ACTIVE_PROVIDER": "gemini",
                    "GEMINI_MODEL_PRO": "gemini-2.5-pro",
                    "GEMINI_MODEL_FLASH": "gemini-2.0-flash-exp",
                    "OPENAI_MODEL": "gpt-4o",
                    "OLLAMA_MODEL": "llama3:8b",
                    "API_KEY_ENV_VAR": "AI_KEY"
                }
            }
    except Exception as e:
        print(f"[CRITICAL CONFIG ERROR] Failed to load or parse config.json: {e}")
        return {} 

# Expose the configuration dictionary for easy import
GLOBAL_CONFIG = get_global_config()