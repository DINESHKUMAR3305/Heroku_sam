from flask import Flask, request, jsonify
from flask_cors import CORS
from gradio_client import Client
import logging
import os

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Gradio client
try:
    client = Client("DINESH03032005/topic-extension")
    logger.info("Gradio client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gradio client: {e}")
    client = None

@app.route('/')
def home():
    return jsonify({
        "status": "Proxy server is running", 
        "message": "Use /predict endpoint",
        "model": "topic-extension"
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if client is None:
            return jsonify({
                "success": False,
                "error": "Gradio client not initialized"
            }), 500
            
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' in request body"}), 400
        
        text = data['text'].strip()
        
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        # Call the Gradio Space
        result = client.predict(text, api_name="/predict")
        
        # Convert to string if needed
        if hasattr(result, 'format') and callable(result.format):
            result = str(result)
        
        logger.info(f"Successfully processed text: {len(text)} characters")
        
        return jsonify({
            "success": True,
            "input_length": len(text),
            "result": result,
            "message": "Successfully processed"
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/health')
def health():
    status = "healthy" if client is not None else "degraded"
    return jsonify({"status": status, "client_initialized": client is not None})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)