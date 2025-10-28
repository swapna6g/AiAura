# src/python_backend/app.py (FINAL SYNCHRONOUS VERSION)

import json
from flask import Flask, request, jsonify
from flask_cors import CORS
# Note: The unnecessary asyncio and platform imports (used for the failed loop fix) are removed.

# Local modules
from .crawler import run_crawler
from .config import AGGREGATED_RESULTS 
from .config import GLOBAL_CONFIG
from .chatbot_service import get_chatbot

app = Flask(__name__)
CORS(app) 

# Note: The view function is synchronous and calls the completely synchronous crawler.
@app.route('/audit', methods=['POST'])
def audit_endpoint():
    """Handles the incoming URL list and runs the audit synchronously."""
    
    AGGREGATED_RESULTS.clear()

    try:
        data = request.get_json()
        raw_urls = data.get('url', '')
        
        urls = [url.strip() for url in raw_urls.split('\n') if url.strip()]
        
        if not urls:
            return jsonify({'error': 'No URLs provided for audit.'}), 400

        print(f"Received Request Body: {data}")
        print(f"Starting audit for {len(urls)} URL(s).")

        results_from_crawler = run_crawler(urls)
        
        # Check if we got an error response
        if results_from_crawler.get('error'):
            return jsonify({'error': results_from_crawler['error']}), 500

        return jsonify(results_from_crawler)

    except Exception as e:
        print(f"An unexpected error occurred in the /audit endpoint: {e}")
        return jsonify({'error': f'Backend execution error: {str(e)}'}), 500
    
    # 🆕 ADD THIS NEW ROUTE (after your /audit route)
@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """Handle chatbot questions about scan results"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Get chatbot instance
        chatbot = get_chatbot()
        
        # Answer using current scan results
        answer = chatbot.answer_question(question, AGGREGATED_RESULTS)
        
        return jsonify({
            'question': question,
            'answer': answer,
            'provider': chatbot.provider
        })
    
    except Exception as e:
        print(f"[CHAT-ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
# --- Server Execution ---

# 💡 ADD THIS ROUTE HANDLER:
@app.route('/config', methods=['GET'])
def get_config():
    """Returns essential configuration settings to the frontend."""
    # Ensure you only expose settings needed by the frontend
    return jsonify({
        'AUDIT_SETTINGS': GLOBAL_CONFIG.get('AUDIT_SETTINGS', {}),
    })

if __name__ == '__main__':
    # Running on port 3001
    app.run(port=3001, debug=True)