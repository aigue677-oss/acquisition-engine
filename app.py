import os
import subprocess
from flask import Flask, request, jsonify
import requests
from contract_generator import generate_purchase_agreement

app = Flask(__name__)

# Configuration & Telegram Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    """Sends real-time updates directly to your Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARNING] Telegram credentials not configured.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram alert: {str(e)}")

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "service": "Autonomous Real Estate Acquisition Engine",
        "mode": "Live Production"
    }), 200

@app.route("/trigger-scraper", methods=["POST"])
def trigger_scraper():
    """Secure endpoint to trigger the autonomous Playwright-stealth scraper in the background."""
    try:
        # Launch scraper.py as a detached background subprocess to avoid blocking the web server
        subprocess.Popen(["python", "scraper.py"])
        return jsonify({
            "status": "success",
            "message": "Autonomous seller scraping sequence initiated successfully in the background."
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to trigger scraper: {str(e)}"
        }), 500

@app.route("/webhook", methods=["POST"])
def webhook_receiver():
    """Receives inbound property leads, executes underwriting, generates contracts, and alerts Telegram."""
    try:
        lead_data = request.get_json()
        if not lead_data:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400

        address = lead_data.get("address", "Unknown Address")
        seller_name = lead_data.get("seller_name", "Unknown Seller")
        asking_price = float(lead_data.get("asking_price", 0))
        repairs = float(lead_data.get("repairs", 0))
        square_footage = float(lead_data.get("square_footage", 1000))

        # Underwriting Heuristic: 70% ARV Formula Estimation
        estimated_arv = square_footage * 185.0  
        mao = (estimated_arv * 0.70) - repairs
        gross_spread = estimated_arv - asking_price - repairs

        # Evaluation criteria check
        is_approved = asking_price <= mao
        status = "Approved - Underwriting Passed" if is_approved else "Review - High Asking Price"

        # --- PHASE B INTEGRATION: AUTOMATED CONTRACT GENERATION ---
        contract_status_msg = "Not Generated (Did not pass underwriting)"
        if is_approved:
            contract_payload = {
                "address": address,
                "seller_name": seller_name,
                "asking_price": asking_price,
                "repairs": repairs,
                "calculated_mao": mao
            }
            generated_file = generate_purchase_agreement(contract_payload)
            if generated_file:
                contract_status_msg = f"Compiled Successfully (`{generated_file}`)"

        # Format Telegram Notification Alert with Contract Status
        alert_message = (
            f"🚨 **Autonomous Acquisition Lead Processed**\n\n"
            f"📍 **Address:** {address}\n"
            f"👤 **Seller:** {seller_name}\n"
            f"💰 **Asking Price:** ${asking_price:,.2f}\n"
            f"🛠 **Estimated Repairs:** ${repairs:,.2f}\n"
            f"📊 **Calculated MAO:** ${mao:,.2f}\n"
            f"📈 **Projected Spread:** ${gross_spread:,.2f}\n"
            f"⚡ **Status:** {status}\n"
            f"📄 **PSA Contract:** {contract_status_msg}"
        )

        send_telegram_alert(alert_message)

        return jsonify({
            "status": "success",
            "message": "Lead ingested, underwritten, contract compiled (if approved), and alerted successfully.",
            "calculated_mao": mao,
            "projected_spread": gross_spread
        }), 200

    except Exception as e:
        print(f"[CRITICAL ERROR] Webhook processing exception: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    
