import os
import logging
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "Acquisition Engine Web Service",
        "status": "online",
        "version": "3.11.9"
    }), 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # If opened via browser (GET), return a friendly status so we know the route exists!
    if request.method == "GET":
        return jsonify({
            "status": "active",
            "message": "Webhook endpoint is live and ready for POST requests."
        }), 200

    try:
        payload = request.get_json(silent=True) or {}
        address = payload.get("address", "123 Acquisition Way, Miami FL")
        seller_name = payload.get("seller_name", "Test Seller")
        asking_price = float(payload.get("asking_price", 120000.0))
        repairs = float(payload.get("repairs", 10000.0))
        square_footage = float(payload.get("square_footage", 1600.0))

        estimated_arv = square_footage * 180.0
        allowable_offer = (estimated_arv * 0.70) - repairs
        gross_spread = estimated_arv - asking_price - repairs

        alert_message = (
            f"🚨 **New Qualified Lead Processed**\n\n"
            f"📍 **Address:** {address}\n"
            f"👤 **Seller:** {seller_name}\n"
            f"💰 **Asking Price:** ${asking_price:,.2f}\n"
            f"🛠️ **Estimated Repairs:** ${repairs:,.2f}\n"
            f"📊 **Calculated MAO:** ${allowable_offer:,.2f}\n"
            f"📈 **Projected Gross Spread:** ${gross_spread:,.2f}"
        )

        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": alert_message,
                "parse_mode": "Markdown"
            }).encode("utf-8")

            req = urllib.request.Request(telegram_url, data=data, method="POST")
            with urllib.request.urlopen(req) as response:
                logger.info("Telegram notification dispatched successfully.")

        return jsonify({
            "status": "success",
            "message": "Lead processed and Telegram alert sent!"
        }), 200

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
