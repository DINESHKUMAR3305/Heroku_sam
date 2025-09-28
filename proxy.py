from flask import Flask, request, jsonify
from flask_cors import CORS
from gradio_client import Client
import logging
import os
import time
import requests

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GradioClientManager:
    def __init__(self):
        self.client = None
        self.retry_count = 0
        self.max_retries = 3
        self.initialize_client()
    
    def initialize_client(self):
        try:
            self.client = Client(
                "DINESH03032005/topic-extension",
                verbose=False,
                timeout=30
            )
            logger.info("✅ Gradio client initialized successfully")
            self.retry_count = 0
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gradio client: {e}")
            self.retry_count += 1
            return False
    
    def predict(self, text):
        if self.client is None:
            if not self.initialize_client():
                raise Exception("Gradio client not available")
        
        try:
            result = self.client.predict(text, api_name="/predict")
            # Ensure result is string
            return str(result) if result is not None else "No result returned"
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            # Reset client and retry once
            self.client = None
            if self.retry_count < self.max_retries and self.initialize_client():
                result = self.client.predict(text, api_name="/predict")
                return str(result) if result is not None else "No result returned"
            else:
                raise e

# Initialize client manager
client_manager = GradioClientManager()

@app.route('/')
def home():
    return jsonify({
        "status": "Proxy server is running", 
        "message": "Use /predict endpoint",
        "model": "topic-extension",
        "deployment": "railway",
        "timestamp": time.time()
    })

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    try:
        # Handle both POST and GET for flexibility
        if request.method == 'GET':
            text = request.args.get('text', '')
        else:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        if len(text) > 10000:
            return jsonify({"error": "Text too long. Maximum 10000 characters allowed."}), 400
        
        logger.info(f"📥 Received request to process {len(text)} characters")
        
        # Call the Gradio Space with timing
        start_time = time.time()
        result = client_manager.predict(text)
        processing_time = round(time.time() - start_time, 2)
        
        logger.info(f"✅ Successfully processed in {processing_time}s")
        
        return jsonify({
            "success": True,
            "input_length": len(text),
            "processing_time": processing_time,
            "result": result,
            "message": "Successfully processed"
        })
        
    except Exception as e:
        logger.error(f"❌ Prediction error: {str(e)}")
        
        # Provide user-friendly error messages
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            user_error = "Request timeout. The model is taking too long to respond."
        elif "connection" in error_msg.lower():
            user_error = "Connection error. Cannot reach the AI model."
        elif "429" in error_msg:
            user_error = "Rate limit exceeded. Please try again in a moment."
        else:
            user_error = f"Processing error: {error_msg}"
        
        return jsonify({
            "success": False,
            "error": user_error,
            "debug_error": error_msg  # Include original error for debugging
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test with a simple prediction to verify everything works
        test_text = "Test health check"
        result = client_manager.predict(test_text)
        status = "healthy"
        details = "Client connected and responding"
    except Exception as e:
        status = "degraded"
        details = f"Client issue: {str(e)}"
    
    return jsonify({
        "status": status,
        "details": details,
        "client_initialized": client_manager.client is not None,
        "retry_count": client_manager.retry_count,
        "timestamp": time.time()
    })

@app.route('/test', methods=['GET', 'POST'])
def test_endpoint():
    """Test endpoint to verify the proxy is working"""
    try:
        test_text = "Artificial intelligence is transforming how we interact with technology and process information across various industries."
        
        start_time = time.time()
        result = client_manager.predict(test_text)
        processing_time = round(time.time() - start_time, 2)
        
        return jsonify({
            "success": True,
            "test_input": test_text,
            "result": result,
            "processing_time": processing_time,
            "status": "Proxy is working correctly"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "Proxy test failed"
        }), 500

@app.route('/info')
def info():
    """Get information about the proxy service"""
    return jsonify({
        "service": "Topic Extension Proxy",
        "model": "DINESH03032005/topic-extension",
        "version": "1.0",
        "deployment": "railway",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "test": "/test",
            "info": "/info"
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
