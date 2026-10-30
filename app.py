from flask import Flask, request, jsonify
from pipeline import process_inbound_lead

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Get the JSON payload sent to the webhook
        payload = request.get_json()
        
        if not payload:
            return jsonify({"error": "No JSON payload provided"}), 400
            
        # Run your heuristic pipeline and sync to Google Sheets
        result = process_inbound_lead(payload)
        
        return jsonify({
            "status": "success",
            "message": "Lead processed and underwritten via internal heuristics.",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
