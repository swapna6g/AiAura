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


def get_wcag_category_name(sc_id):
    """Get friendly category name from SC ID"""
    if not sc_id or not isinstance(sc_id, str):
        return 'Other'
    
    categories = {
        '1.1': 'Text Alternatives',
        '1.2': 'Time-based Media',
        '1.3': 'Adaptable Content',
        '1.4': 'Distinguishable (Color/Contrast)',
        '2.1': 'Keyboard Accessible',
        '2.2': 'Enough Time',
        '2.3': 'Seizures',
        '2.4': 'Navigable',
        '2.5': 'Input Modalities',
        '3.1': 'Readable',
        '3.2': 'Predictable',
        '3.3': 'Input Assistance',
        '4.1': 'Compatible'
    }
    
    try:
        prefix = '.'.join(sc_id.split('.')[:2])
        return categories.get(prefix, 'Other')
    except:
        return 'Other'


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
        """Build comprehensive context string from scan results"""
        if not scan_results:
            return "No scan results available."
        
        context_parts = []
        
        # Overall summary
        total_pages = len(scan_results)
        total_critical = 0
        total_passed = 0
        total_manual = 0
        total_na = 0
        
        for report in scan_results.values():
            if not report.get('error'):
                total_critical += len(report.get('automatic_results', []))
                total_passed += len(report.get('passed_checks', []))
                total_manual += len(report.get('manual_audits_required', []))
                total_na += len(report.get('not_applicable', []))
        
        context_parts.append("=" * 60)
        context_parts.append("OVERALL SCAN SUMMARY")
        context_parts.append("=" * 60)
        context_parts.append(f"Total Pages Scanned: {total_pages}")
        context_parts.append(f"Total Critical Issues: {total_critical}")
        context_parts.append(f"Total Passed Checks: {total_passed}")
        context_parts.append(f"Total Manual Checks Required: {total_manual}")
        context_parts.append(f"Total Not Applicable: {total_na}")
        context_parts.append("")
        
        # Collect all unique WCAG categories
        all_critical_by_sc = {}
        all_passed_by_sc = {}
        all_manual_by_sc = {}
        
        for url, report in scan_results.items():
            if report.get('error'):
                continue
            
            # Group critical issues by SC ID
            for item in report.get('automatic_results', []):
                sc_id = item.get('sc_id', 'Unknown')
                if sc_id not in all_critical_by_sc:
                    all_critical_by_sc[sc_id] = {
                        'count': 0,
                        'description': item.get('description', 'N/A'),
                        'pages': []
                    }
                all_critical_by_sc[sc_id]['count'] += 1
                all_critical_by_sc[sc_id]['pages'].append(url)
            
            # Group passed checks by SC ID
            for item in report.get('passed_checks', []):
                sc_id = item.get('sc_id', 'Unknown')
                if sc_id not in all_passed_by_sc:
                    all_passed_by_sc[sc_id] = {
                        'count': 0,
                        'description': item.get('description', 'N/A')
                    }
                all_passed_by_sc[sc_id]['count'] += 1
            
            # Group manual checks by SC ID
            for item in report.get('manual_audits_required', []):
                sc_id = item.get('sc_id', 'Unknown')
                if sc_id not in all_manual_by_sc:
                    all_manual_by_sc[sc_id] = {
                        'count': 0,
                        'description': item.get('description', 'N/A')[:100]
                    }
                all_manual_by_sc[sc_id]['count'] += 1
        
        # WCAG Categories Summary
        context_parts.append("=" * 60)
        context_parts.append("WCAG CATEGORIES TESTED")
        context_parts.append("=" * 60)
        
        if all_critical_by_sc:
            context_parts.append("\nCRITICAL VIOLATIONS:")
            for sc_id, data in sorted(all_critical_by_sc.items(), key=lambda x: x[1]['count'], reverse=True):
                context_parts.append(f"  • {sc_id}: {data['count']} violations across {len(set(data['pages']))} pages")
                context_parts.append(f"    Description: {data['description'][:100]}")
        
        if all_passed_by_sc:
            context_parts.append("\nPASSED CHECKS:")
            top_passed = sorted(all_passed_by_sc.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
            for sc_id, data in top_passed:
                context_parts.append(f"  • {sc_id}: Passed on {data['count']} pages")
        
        if all_manual_by_sc:
            context_parts.append("\nMANUAL CHECKS REQUIRED:")
            top_manual = sorted(all_manual_by_sc.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
            for sc_id, data in top_manual:
                context_parts.append(f"  • {sc_id}: Requires manual review on {data['count']} pages")
                context_parts.append(f"    What to check: {data['description']}")
        
        # Per-page breakdown
        context_parts.append("\n" + "=" * 60)
        context_parts.append("PER-PAGE DETAILED RESULTS")
        context_parts.append("=" * 60)
        
        for url, report in scan_results.items():
            if report.get('error'):
                context_parts.append(f"\n{url}")
                context_parts.append(f"  ERROR: {report.get('error')}")
                continue
            
            summary = report.get('summary', {})
            critical = len(report.get('automatic_results', []))
            passed = len(report.get('passed_checks', []))
            manual = len(report.get('manual_audits_required', []))
            score = summary.get('audit_score', 'N/A')
            
            context_parts.append(f"\n{url}")
            context_parts.append(f"  Score: {score}")
            context_parts.append(f"  Critical Issues: {critical}")
            context_parts.append(f"  Passed Checks: {passed}")
            context_parts.append(f"  Manual Review Needed: {manual}")
            
            # Show unique violations for this page
            if critical > 0:
                context_parts.append(f"  Critical violations on this page:")
                unique_violations = {}
                for v in report.get('automatic_results', []):
                    sc_id = v.get('sc_id', 'Unknown')
                    if sc_id not in unique_violations:
                        unique_violations[sc_id] = v.get('description', 'N/A')[:80]
                
                for sc_id, desc in unique_violations.items():
                    context_parts.append(f"    - {sc_id}: {desc}")
        
        # WCAG Category Explanations
        context_parts.append("\n" + "=" * 60)
        context_parts.append("WCAG CATEGORY INFORMATION")
        context_parts.append("=" * 60)
        context_parts.append("""
Common WCAG 2.2 Categories:
- 1.1.x: Text Alternatives (alt text for images)
- 1.2.x: Time-based Media (captions, audio descriptions)
- 1.3.x: Adaptable (semantic structure, info relationships)
- 1.4.x: Distinguishable (color contrast, text spacing, focus visible)
- 2.1.x: Keyboard Accessible (keyboard navigation)
- 2.2.x: Enough Time (timing adjustable, no timeouts)
- 2.4.x: Navigable (skip links, page titles, focus order, link purpose)
- 2.5.x: Input Modalities (pointer gestures, target size)
- 3.1.x: Readable (language of page)
- 3.2.x: Predictable (consistent navigation)
- 3.3.x: Input Assistance (form labels, error identification)
- 4.1.x: Compatible (parsing, name/role/value, status messages)

NOTE: Color blindness and contrast checks fall under 1.4.3 (Contrast Minimum)
and 1.4.1 (Use of Color). These require MANUAL verification as automated
tools cannot accurately assess visual perception.
        """)
        
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
        """Enhanced pattern-matching fallback with better coverage"""
        q = question.lower()
        
        if not scan_results:
            return "No scan results available. Please run a scan first."
        
        # Calculate comprehensive stats
        all_critical_by_sc = {}
        all_manual_by_sc = {}
        all_passed_by_sc = {}
        pages_with_issues = []
        
        for url, report in scan_results.items():
            if not report.get('error'):
                critical_count = len(report.get('automatic_results', []))
                score = report.get('summary', {}).get('audit_score', 'N/A')
                pages_with_issues.append((url, critical_count, score))
                
                # Collect by SC ID
                for item in report.get('automatic_results', []):
                    sc_id = item.get('sc_id', 'Unknown')
                    if sc_id not in all_critical_by_sc:
                        all_critical_by_sc[sc_id] = {
                            'count': 0,
                            'description': item.get('description', 'N/A')[:100],
                            'fix_tip': item.get('fix_tip', 'N/A')[:100]
                        }
                    all_critical_by_sc[sc_id]['count'] += 1
                
                for item in report.get('manual_audits_required', []):
                    sc_id = item.get('sc_id', 'Unknown')
                    if sc_id not in all_manual_by_sc:
                        all_manual_by_sc[sc_id] = item.get('description', 'N/A')[:100]
                
                for item in report.get('passed_checks', []):
                    sc_id = item.get('sc_id', 'Unknown')
                    all_passed_by_sc[sc_id] = all_passed_by_sc.get(sc_id, 0) + 1
        
        pages_with_issues.sort(key=lambda x: x[1], reverse=True)
        
        # Pattern: Color blindness / contrast
        if 'color' in q and ('blind' in q or 'contrast' in q or 'vision' in q):
            contrast_checks = [sc for sc in all_manual_by_sc.keys() if sc.startswith('1.4')]
            response = "**Color Blindness & Contrast Checks:**\n\n"
            
            if contrast_checks:
                response += f"Found {len(contrast_checks)} color/contrast-related checks requiring MANUAL verification:\n\n"
                for sc_id in contrast_checks:
                    response += f"• **{sc_id}**: {all_manual_by_sc[sc_id]}\n"
                response += "\n⚠️ **Important**: Color contrast (WCAG 1.4.3) and color usage (1.4.1) "
                response += "CANNOT be fully automated. These require:\n"
                response += "- Manual testing with contrast checkers\n"
                response += "- Testing by users with color vision deficiencies\n"
                response += "- Visual inspection of color-coded information\n"
            else:
                response += "No color/contrast checks were flagged for manual review in this scan. "
                response += "However, WCAG 1.4.3 (Contrast Minimum) and 1.4.1 (Use of Color) "
                response += "should ALWAYS be manually verified as automated tools have limitations.\n\n"
                response += "**Recommended tools:**\n"
                response += "- WebAIM Contrast Checker\n"
                response += "- Color Oracle (color blindness simulator)\n"
                response += "- Browser DevTools Accessibility Inspector"
            
            return response
        
        # Pattern: Categories / checks performed
        if 'categor' in q or 'type' in q or ('checks' in q and 'performed' in q):
            response = "**WCAG Categories Tested in This Scan:**\n\n"
            
            # Critical categories
            if all_critical_by_sc:
                response += "**Critical Violations Found:**\n"
                for sc_id, data in sorted(all_critical_by_sc.items(), key=lambda x: x[1]['count'], reverse=True):
                    category = get_wcag_category_name(sc_id)
                    response += f"• **{sc_id}** ({category}): {data['count']} issues\n"
            
            # Manual check categories
            if all_manual_by_sc:
                response += "\n**Manual Verification Required:**\n"
                manual_categories = {}
                for sc_id in all_manual_by_sc.keys():
                    category = get_wcag_category_name(sc_id)
                    manual_categories[category] = manual_categories.get(category, 0) + 1
                
                for category, count in sorted(manual_categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                    response += f"• {category}: {count} checks\n"
            
            # Passed categories
            if all_passed_by_sc:
                response += "\n**Passing Checks:**\n"
                passed_categories = {}
                for sc_id in all_passed_by_sc.keys():
                    category = get_wcag_category_name(sc_id)
                    passed_categories[category] = passed_categories.get(category, 0) + 1
                
                for category, count in sorted(passed_categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                    response += f"• {category}: {count} checks\n"
            
            response += f"\n📊 **Total**: {len(all_critical_by_sc)} violation types, "
            response += f"{len(all_passed_by_sc)} passed types, "
            response += f"{len(all_manual_by_sc)} requiring manual review"
            
            return response
        
        # Pattern: Most critical / worst pages
        if 'most' in q and ('issue' in q or 'critical' in q or 'problem' in q):
            if not pages_with_issues:
                return "No pages with critical issues found."
            
            response = "**Pages Ranked by Critical Issues:**\n\n"
            for i, (url, critical, score) in enumerate(pages_with_issues[:5], 1):
                response += f"{i}. **{url}**\n"
                response += f"   • Critical Issues: {critical}\n"
                response += f"   • Score: {score}\n\n"
            
            # Most common issue
            if all_critical_by_sc:
                top_issue = max(all_critical_by_sc.items(), key=lambda x: x[1]['count'])
                response += f"**Most Common Issue Across All Pages:**\n"
                response += f"• **{top_issue[0]}**: {top_issue[1]['count']} occurrences\n"
                response += f"• Description: {top_issue[1]['description']}\n"
                response += f"• How to fix: {top_issue[1]['fix_tip']}"
            
            return response
        
        # Pattern: Top violations
        if 'top' in q and ('violation' in q or 'issue' in q):
            if not all_critical_by_sc:
                return "No critical violations found."
            
            top_violations = sorted(
                all_critical_by_sc.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:5]
            
            response = "**Top Critical Violations:**\n\n"
            for i, (sc_id, data) in enumerate(top_violations, 1):
                category = get_wcag_category_name(sc_id)
                response += f"{i}. **WCAG {sc_id}** ({category})\n"
                response += f"   • Found: {data['count']} times\n"
                response += f"   • Issue: {data['description']}\n"
                response += f"   • Fix: {data['fix_tip']}\n\n"
            
            return response
        
        # Pattern: Summary
        if 'summary' in q or 'overview' in q:
            total_pages = len(scan_results)
            total_critical = sum(len(r.get('automatic_results', [])) for r in scan_results.values() if not r.get('error'))
            total_passed = sum(len(r.get('passed_checks', [])) for r in scan_results.values() if not r.get('error'))
            total_manual = sum(len(r.get('manual_audits_required', [])) for r in scan_results.values() if not r.get('error'))
            
            response = "**Comprehensive Scan Summary:**\n\n"
            response += f"📊 **Overview:**\n"
            response += f"• Pages Scanned: {total_pages}\n"
            response += f"• Total Critical Issues: {total_critical}\n"
            response += f"• Passed Checks: {total_passed}\n"
            response += f"• Manual Review Needed: {total_manual}\n\n"
            
            if all_critical_by_sc:
                response += f"**Violation Types:** {len(all_critical_by_sc)} unique WCAG criteria failed\n\n"
            
            if pages_with_issues:
                response += "**Top Problem Pages:**\n"
                for url, critical, score in pages_with_issues[:3]:
                    response += f"• {url}: {critical} issues (Score: {score})\n"
            
            return response
        
        # Pattern: Score
        if 'score' in q:
            if not pages_with_issues:
                return "No scored pages available."
            
            response = "**Accessibility Scores:**\n\n"
            for url, critical, score in pages_with_issues:
                response += f"• **{url}**: {score}\n"
            
            try:
                avg_score = sum(
                    int(str(r.get('summary', {}).get('audit_score', '0')).split('%')[0]) 
                    for r in scan_results.values() if not r.get('error')
                ) / len(pages_with_issues)
                
                response += f"\n📈 **Average Score**: {avg_score:.1f}%"
            except:
                pass
            
            return response
        
        # Default response
        return """I can help you with questions like:

**About Issues:**
- Which pages have the most critical issues?
- What are the top violations?
- What is the most common problem?

**About Categories:**
- What categories of WCAG checks were performed?
- Did we check for color blindness accessibility?
- What manual checks are needed?

**About Scores:**
- What are the accessibility scores?
- Give me a summary of the scan
- Which page performed best?

**Specific Checks:**
- Show me contrast issues
- What about keyboard navigation?
- Are there any form accessibility issues?

What would you like to know?"""
    
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