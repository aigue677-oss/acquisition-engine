from flask import Flask, request, jsonify
from pipeline import process_inbound_lead

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "success", "message": "Sovereign Acquisition Engine is online."}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Receives inbound JSON payloads, processes underwriting, and triggers automation."""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
            
        result = process_inbound_lead(data)
        return jsonify({
            "status": "success", 
            "message": "Lead processed successfully and logged to sheet/Telegram.",
            "data": result
        }), 200
        
    except Exception as e:
        print(f"Webhook execution error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    
