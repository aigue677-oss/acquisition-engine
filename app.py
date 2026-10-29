import os
import json
from flask import Flask, request
from webhook_parser import parse_incoming_reply

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return "Sovereign Grid Webhook Receiver is Online", 200

@app.route("/inbound-email", methods=["POST"])
def inbound_email_webhook():
    # Supports multipart/form-data common in email parsing webhooks (e.g., SendGrid Inbound Parse)
    sender_full = request.form.get("from", "") or request.json.get("from", "") if request.is_json else ""
    email_body = request.form.get("text", "") or request.form.get("html", "")
    
    if not email_body and request.is_json:
        email_body = request.json.get("text", "") or request.json.get("html", "")

    # Extract clean email address if format is provided as "Name <email@domain.com>"
    if "<" in sender_full and ">" in sender_full:
        sender_email = sender_full.split("<")[1].split(">")[0].strip()
    else:
        sender_email = sender_full.strip()

    if not sender_email:
        return json.dumps({"status": "error", "message": "Missing sender email"}), 400, {'Content-Type': 'application/json'}

    print(f"Received inbound reply from: {sender_email}")
    
    # Execute sovereign grid parsing logic & sheet synchronization
    result = parse_incoming_reply(sender_email, email_body)
    
    return json.dumps(result), 200, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  
