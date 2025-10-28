# src/python_backend/chatbot_service.py
"""
Minimal Chatbot Service for Accessibility Scan Results
Supports: OpenAI, Gemini, Ollama (switchable via env var)
"""

import os
import json
import re

# Import based on available SDK
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class AccessibilityChatbot:
    """Minimal chatbot that answers questions about scan results"""
    
    def __init__(self):
        self.provider = os.environ.get('AI_PROVIDER', 'gemini').lower()
        self.api_key = os.environ.get('AI_KEY') or os.environ.get('GEMINI_API_KEY')
        self.model_name = self._get_model_name()
        self.client = self._initialize_client()
    
    def _get_model_name(self):
        """Get model name based on provider"""
        models = {
            'openai': os.environ.get('OPENAI_MODEL', 'gpt-4'),
            'gemini': os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp'),
            'ollama': os.environ.get('OLLAMA_MODEL', 'llama3:8b')
        }
        return models.get(self.provider, 'gemini-2.0-flash-exp')
    
    def _initialize_client(self):
        """Initialize AI client based on provider"""
        try:
            if self.provider == 'openai' and OPENAI_AVAILABLE:
                return OpenAI(api_key=self.api_key)
            
            elif self.provider == 'gemini' and GEMINI_AVAILABLE:
                genai.configure(api_key=self.api_key)
                return genai.GenerativeModel(self.model_name)
            
            elif self.provider == 'ollama' and OLLAMA_AVAILABLE:
                return None  # Ollama uses HTTP requests
            
            print(f"[CHATBOT-WARN] {self.provider} not available or not configured")
            return None
        
        except Exception as e:
            print(f"[CHATBOT-ERROR] Failed to initialize {self.provider}: {e}")
            return None
    
    def _build_context(self, scan_results):
        """Build context string from scan results"""
        if not scan_results:
            return "No scan results available."
        
        context_parts = []
        
        # Overall summary
        total_pages = len(scan_results)
        total_critical = sum(
            len(r.get('automatic_results', [])) 
            for r in scan_results.values() 
            if not r.get('error')
        )
        
        context_parts.append(f"SCAN SUMMARY:")
        context_parts.append(f"- Total Pages Scanned: {total_pages}")
        context_parts.append(f"- Total Critical Issues: {total_critical}")
        
        # Per-page breakdown
        context_parts.append("\nPER-PAGE RESULTS:")
        for url, report in scan_results.items():
            if report.get('error'):
                context_parts.append(f"\n{url}: ERROR - {report.get('error')}")
                continue
            
            summary = report.get('summary', {})
            critical = len(report.get('automatic_results', []))
            passed = len(report.get('passed_checks', []))
            manual = len(report.get('manual_audits_required', []))
            score = summary.get('audit_score', 'N/A')
            
            context_parts.append(f"\n{url}:")
            context_parts.append(f"  Score: {score}")
            context_parts.append(f"  Critical: {critical}, Passed: {passed}, Manual: {manual}")
            
            # Include top violations
            violations = report.get('automatic_results', [])[:3]
            if violations:
                context_parts.append("  Top violations:")
                for v in violations:
                    context_parts.append(f"    - {v.get('sc_id')}: {v.get('description', 'N/A')[:80]}")
        
        return "\n".join(context_parts)
    
    def _call_openai(self, question, context):
        """Call OpenAI API"""
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an accessibility expert. Answer questions about these WCAG scan results:\n\n{context}"
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[CHATBOT-ERROR] OpenAI call failed: {e}")
            return None
    
    def _call_gemini(self, question, context):
        """Call Gemini API"""
        if not self.client:
            return None
        
        try:
            prompt = f"""You are an accessibility expert. Answer questions about these WCAG scan results.

SCAN RESULTS:
{context}

USER QUESTION: {question}

Provide a concise, helpful answer referencing specific data from the scan results."""
            
            config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500
            )
            
            response = self.client.generate_content(
                prompt,
                generation_config=config
            )
            
            return response.text
        except Exception as e:
            print(f"[CHATBOT-ERROR] Gemini call failed: {e}")
            return None
    
    def _call_ollama(self, question, context):
        """Call Ollama API"""
        try:
            ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": f"""You are an accessibility expert. Answer questions about these WCAG scan results.

SCAN RESULTS:
{context}

USER QUESTION: {question}

Provide a concise, helpful answer.""",
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            return None
        except Exception as e:
            print(f"[CHATBOT-ERROR] Ollama call failed: {e}")
            return None
    
    def _get_fallback_response(self, question, scan_results):
        """Simple pattern-matching fallback (no API needed)"""
        q = question.lower()
        
        if not scan_results:
            return "No scan results available. Please run a scan first."
        
        # Calculate stats
        pages_with_issues = []
        for url, report in scan_results.items():
            if not report.get('error'):
                critical_count = len(report.get('automatic_results', []))
                score = report.get('summary', {}).get('audit_score', 'N/A')
                pages_with_issues.append((url, critical_count, score))
        
        pages_with_issues.sort(key=lambda x: x[1], reverse=True)
        
        # Pattern matching
        if 'most' in q and ('issue' in q or 'critical' in q or 'problem' in q):
            if not pages_with_issues:
                return "No pages with critical issues found."
            
            worst = pages_with_issues[0]
            response = f"**Page with most critical issues:**\n\n"
            response += f"URL: {worst[0]}\n"
            response += f"Critical Issues: {worst[1]}\n"
            response += f"Score: {worst[2]}"
            return response
        
        if 'top' in q and ('violation' in q or 'issue' in q):
            all_violations = []
            for url, report in scan_results.items():
                if not report.get('error'):
                    all_violations.extend(report.get('automatic_results', []))
            
            if not all_violations:
                return "No critical violations found."
            
            # Count by SC ID
            violation_counts = {}
            for v in all_violations:
                sc_id = v.get('sc_id', 'Unknown')
                if sc_id not in violation_counts:
                    violation_counts[sc_id] = {
                        'count': 0,
                        'description': v.get('description', 'N/A')
                    }
                violation_counts[sc_id]['count'] += 1
            
            # Get top 3
            top_violations = sorted(
                violation_counts.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:3]
            
            response = "**Top 3 Violations:**\n\n"
            for i, (sc_id, data) in enumerate(top_violations, 1):
                response += f"{i}. **{sc_id}**: {data['description'][:100]}\n"
                response += f"   Found {data['count']} times\n\n"
            
            return response
        
        if 'summary' in q or 'overview' in q:
            total_pages = len(scan_results)
            total_critical = sum(
                len(r.get('automatic_results', []))
                for r in scan_results.values()
                if not r.get('error')
            )
            
            response = f"**Scan Summary:**\n\n"
            response += f"- Pages Scanned: {total_pages}\n"
            response += f"- Total Critical Issues: {total_critical}\n\n"
            
            if pages_with_issues:
                response += f"**Pages with Issues:**\n"
                for url, critical, score in pages_with_issues[:3]:
                    response += f"- {url}: {critical} issues (Score: {score})\n"
            
            return response
        
        if 'score' in q:
            if not pages_with_issues:
                return "No scored pages available."
            
            response = "**Accessibility Scores:**\n\n"
            for url, critical, score in pages_with_issues:
                response += f"- {url}: {score}\n"
            
            return response
        
        # Default response
        return """I can help you with questions like:
- Which pages have the most critical issues?
- What are the top violations?
- Give me a summary of the scan
- What are the accessibility scores?

Ask me anything about your scan results!"""
    
    def answer_question(self, question, scan_results):
        """
        Main method to answer questions
        
        Args:
            question (str): User's question
            scan_results (dict): The AGGREGATED_RESULTS dictionary
        
        Returns:
            str: Answer to the question
        """
        if not question or not question.strip():
            return "Please ask a question about your accessibility scan."
        
        # Build context
        context = self._build_context(scan_results)
        
        # Try AI first
        answer = None
        
        if self.provider == 'openai':
            answer = self._call_openai(question, context)
        elif self.provider == 'gemini':
            answer = self._call_gemini(question, context)
        elif self.provider == 'ollama':
            answer = self._call_ollama(question, context)
        
        # Fallback to pattern matching if AI fails
        if not answer:
            print(f"[CHATBOT] Using fallback for: {question}")
            answer = self._get_fallback_response(question, scan_results)
        
        return answer


# Global instance
_chatbot = None

def get_chatbot():
    """Get or create chatbot instance"""
    global _chatbot
    if _chatbot is None:
        _chatbot = AccessibilityChatbot()
    return _chatbot