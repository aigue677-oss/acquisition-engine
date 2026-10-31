import os
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

# Initialize Flask application
app = Flask(__name__)

# Configure logging for Render runtime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables check
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GOOGLE_SHEET_KEY = os.environ.get("GOOGLE_SHEET_KEY")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

def get_gspread_client():
    """Initializes and returns an authorized gspread client using environment credentials."""
    try:
        if not GOOGLE_SERVICE_ACCOUNT_JSON:
            logger.error("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is missing.")
            return None
        
        # Parse the JSON string from the environment variable
        creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize gspread client: {str(e)}")
        return None

@app.route("/", methods=["GET"])
def index():
    """Health check endpoint to keep the Render service alive and responsive."""
    return jsonify({
        "service": "Acquisition Engine Web Service",
        "status": "online",
        "version": "3.11.9"
    }), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Production inbound webhook endpoint that handles lead ingestion, heuristic underwriting,
    Telegram notification dispatch, and automated Google Sheets CRM logging.
    """
    try:
        # force=True ensures JSON is parsed even if the Content-Type header is missing or altered
        payload = request.get_json(force=True, silent=True)
        if not payload:
            logger.warning("Received invalid or empty JSON payload on /webhook")
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Extract core lead details
        address = payload.get("address", "Unknown Address")
        seller_name = payload.get("seller_name", "Unknown Seller")
        asking_price = float(payload.get("asking_price", 0.0))
        repairs = float(payload.get("repairs", 0.0))
        square_footage = float(payload.get("square_footage", 0.0))

        logger.info(f"Processing incoming lead for property: {address}")

        # Core Heuristic Calculation
        estimated_arv = square_footage * 180.0
        allowable_offer = (estimated_arv * 0.70) - repairs
        gross_spread = estimated_arv - asking_price - repairs
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Log to Google Sheets CRM (`Incoming_Leads` tab)
        sheet_logged = False
        if GOOGLE_SHEET_KEY and GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                gc = get_gspread_client()
                if gc:
                    spreadsheet = gc.open_by_key(GOOGLE_SHEET_KEY)
                    worksheet = spreadsheet.worksheet("Incoming_Leads")
                    
                    # Row schema: Timestamp, Address, Seller_Name, Asking_Price, Repairs, MAO, Gross_Spread
                    row_data = [
                        timestamp,
                        address,
                        seller_name,
                        asking_price,
                        repairs,
                        allowable_offer,
                        gross_spread
                    ]
                    worksheet.append_row(row_data)
                    logger.info("Successfully appended lead row to Google Sheets CRM.")
                    sheet_logged = True
            except Exception as sheet_err:
                logger.error(f"Failed to log lead into Google Sheets: {sheet_err}")
        else:
            logger.warning("Google Sheets configuration keys missing; logging skipped.")

        # 2. Build Rich Notification Text
        alert_message = (
            f"🚨 **New Qualified Lead Processed**\n\n"
            f"📍 **Address:** {address}\n"
            f"👤 **Seller:** {seller_name}\n"
            f"💰 **Asking Price:** ${asking_price:,.2f}\n"
            f"🛠️ **Estimated Repairs:** ${repairs:,.2f}\n"
            f"📊 **Calculated MAO:** ${allowable_offer:,.2f}\n"
            f"📈 **Projected Gross Spread:** ${gross_spread:,.2f}\n"
            f"📋 **CRM Logged:** {'✅ Yes' if sheet_logged else '❌ Failed/Skipped'}"
        )

        # 3. Dispatch Telegram Notification
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": alert_message,
                "parse_mode": "Markdown"
            }).encode("utf-8")

            req = urllib.request.Request(telegram_url, data=data, method="POST")
            try:
                with urllib.request.urlopen(req) as response:
                    logger.info("Telegram notification dispatched successfully.")
            except Exception as tel_err:
                logger.error(f"Failed to send Telegram alert: {tel_err}")
        else:
            logger.warning("Telegram credentials missing; notification skipped.")

        return jsonify({
            "status": "success",
            "message": "Lead successfully processed, logged to CRM, and broadcasted.",
            "data": {
                "address": address,
                "mao": allowable_offer,
                "gross_spread": gross_spread,
                "crm_logged": sheet_logged
            }
        }), 200

    except Exception as e:
        logger.error(f"Critical error processing webhook: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
