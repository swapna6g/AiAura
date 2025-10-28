# src/python_backend/app.py

import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# Local modules
from .crawler import run_crawler
from .config import AGGREGATED_RESULTS, GLOBAL_CONFIG
from .chatbot_service import get_chatbot

app = Flask(__name__)
CORS(app)

@app.route('/audit', methods=['POST'])
def audit_endpoint():
    """Handles the incoming URL list and runs the audit synchronously."""
    
    AGGREGATED_RESULTS.clear()

    try:
        data = request.get_json()
        raw_urls = data.get('url', '')
        custom_config = data.get('config', None)  # 🆕 GET CUSTOM CONFIG
        
        urls = [url.strip() for url in raw_urls.split('\n') if url.strip()]
        
        if not urls:
            return jsonify({'error': 'No URLs provided for audit.'}), 400

        # 🆕 VALIDATE URL LIMIT
        if len(urls) > 20:
            return jsonify({'error': 'Maximum 20 URLs allowed'}), 400

        print(f"Received Request Body: {data}")
        print(f"Starting audit for {len(urls)} URL(s).")
        
        # 🆕 PASS CUSTOM CONFIG TO CRAWLER
        results_from_crawler = run_crawler(urls, custom_config)
        
        # Check if we got an error response
        if results_from_crawler.get('error'):
            return jsonify({'error': results_from_crawler['error']}), 500

        # 🆕 SAVE TO output.json
        import os
        output_path = r'C:\Users\DELL\Documents\Hackathon\accessibility-auditor_python_withoutAI\src\output.json'
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results_from_crawler, f, indent=2, ensure_ascii=False)
            print(f"[OUTPUT] Saved results to {output_path}")
        except Exception as e:
            print(f"[OUTPUT-ERROR] Failed to save output.json: {e}")

        return jsonify(results_from_crawler)

    except Exception as e:
        print(f"An unexpected error occurred in the /audit endpoint: {e}")
        return jsonify({'error': f'Backend execution error: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """Handle chatbot questions about scan results"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        chatbot = get_chatbot()
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

@app.route('/config', methods=['GET'])
def get_config():
    """Returns essential configuration settings to the frontend."""
    return jsonify({
        'AUDIT_SETTINGS': GLOBAL_CONFIG.get('AUDIT_SETTINGS', {}),
    })

if __name__ == '__main__':
    app.run(port=3001, debug=True)