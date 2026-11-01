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
    Production inbound webhook endpoint handling lead ingestion, heuristic underwriting,
    institutional buyer matching, CRM logging, and Telegram broadcast notifications.
    """
    try:
        payload = request.get_json(force=True, silent=True)
        if not payload:
            logger.warning("Received invalid or empty JSON payload on /webhook")
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Extract core lead details matching your new 15-column schema
        property_address = payload.get("property_address", "Unknown Address")
        city = payload.get("city", "")
        region_state = payload.get("region_state", "")
        country = payload.get("country", "USA")
        owner_name = payload.get("owner_name", "Unknown Seller")
        owner_phone = payload.get("owner_phone", "")
        owner_email = payload.get("owner_email", "")
        
        asking_price = float(payload.get("asking_price", 0.0))
        repairs = float(payload.get("repairs", 0.0))
        square_footage = float(payload.get("square_footage", 0.0))
        bedrooms = int(payload.get("bedrooms", 0))
        property_type = payload.get("property_type", "Single Family")
        zip_code = str(payload.get("zip_code", ""))

        logger.info(f"Processing incoming lead for property: {property_address}, {city}")

        # Core Heuristic Calculation
        arv = square_footage * 180.0
        mao = (arv * 0.70) - repairs
        gross_spread = arv - asking_price - repairs
        transaction_structure = "Wholesale / Cash"
        currency = "USD"
        status = "New Lead"

        # 1. Connect to Google Sheets & Perform Buyer Matching
        matched_buyers = []
        sheet_logged = False

        if GOOGLE_SHEET_KEY and GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                gc = get_gspread_client()
                if gc:
                    spreadsheet = gc.open_by_key(GOOGLE_SHEET_KEY)
                    
                    # --- Buyer Matching Logic ---
                    try:
                        buyers_worksheet = spreadsheet.worksheet("Institutional_Buyers")
                        all_buyers = buyers_worksheet.get_all_records()
                        
                        for buyer in all_buyers:
                            b_id = buyer.get("Buyer_ID", "Unknown Buyer")
                            b_city = str(buyer.get("Target_City", "")).strip().lower()
                            b_zip = str(buyer.get("Target_Zip_Codes", "")).strip()
                            b_max_price = float(buyer.get("Max_Purchase_Price", 0.0) or 0.0)
                            b_min_beds = int(buyer.get("Min_Bedrooms", 0) or 0)
                            b_prop_type = str(buyer.get("Target_Property_Type", "")).strip().lower()
                            b_email = buyer.get("Contact_Email", "")

                            # Check criteria matches
                            city_match = not b_city or (b_city in city.lower())
                            zip_match = not b_zip or (zip_code in b_zip)
                            price_match = b_max_price == 0.0 or asking_price <= b_max_price
                            bed_match = bedrooms >= b_min_beds
                            type_match = not b_prop_type or (b_prop_type in property_type.lower())

                            if (city_match or zip_match) and price_match and bed_match and type_match:
                                matched_buyers.append({
                                    "buyer_id": b_id,
                                    "email": b_email
                                })
                    except Exception as match_err:
                        logger.error(f"Error during buyer matching scan: {match_err}")

                    # --- Log to Incoming_Leads Tab ---
                    leads_worksheet = spreadsheet.worksheet("Incoming_Leads")
                    # Schema: Property address, City, Region/State, Country, Owner Name, Owner Phone, 
                    # Owner Email, ARV, Repairs, Asking Price, MAO, Gross Spread, Transaction Structure, Currency, Status
                    row_data = [
                        property_address,
                        city,
                        region_state,
                        country,
                        owner_name,
                        owner_phone,
                        owner_email,
                        arv,
                        repairs,
                        asking_price,
                        mao,
                        gross_spread,
                        transaction_structure,
                        currency,
                        status
                    ]
                    leads_worksheet.append_row(row_data)
                    logger.info("Successfully appended lead row to Incoming_Leads CRM.")
                    sheet_logged = True
            except Exception as sheet_err:
                logger.error(f"Failed to process Google Sheets operations: {sheet_err}")
        else:
            logger.warning("Google Sheets configuration keys missing; logging skipped.")

        # 2. Build Rich Notification Text with Matched Buyers
        buyer_alert_text = "None"
        if matched_buyers:
            buyer_lines = [f"• {b['buyer_id']} ({b['email']})" for b in matched_buyers]
            buyer_alert_text = "\n" + "\n".join(buyer_lines)

        alert_message = (
            f"🚨 **New Qualified Lead Processed**\n\n"
            f"📍 **Address:** {property_address}, {city}, {region_state}\n"
            f"👤 **Owner:** {owner_name} ({owner_phone})\n"
            f"💰 **Asking Price:** ${asking_price:,.2f}\n"
            f"🛠️ **Repairs:** ${repairs:,.2f}\n"
            f"📊 **Calculated MAO:** ${mao:,.2f}\n"
            f"📈 **Gross Spread:** ${gross_spread:,.2f}\n\n"
            f"🏢 **Matched Institutional Buyers:** {buyer_alert_text}\n"
            f"📋 **CRM Logged:** {'✅ Yes' if sheet_logged else '❌ Failed'}"
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
            "message": "Lead processed, checked against institutional buyers, logged to CRM, and broadcasted.",
            "data": {
                "property_address": property_address,
                "mao": mao,
                "gross_spread": gross_spread,
                "matched_buyers_count": len(matched_buyers),
                "crm_logged": sheet_logged
            }
        }), 200

    except Exception as e:
        logger.error(f"Critical error processing webhook: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
