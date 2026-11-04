import os
import json
import logging
import tempfile
import requests
from datetime import datetime
from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
from docx import Document

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
        return gspread.authorize(credentials)
    except Exception as e:
        logger.error(f"Failed to initialize gspread client: {str(e)}")
        return None

def fetch_dynamic_multiplier(spreadsheet, zip_code, city):
    """
    Zero-Cost Dynamic Valuation: Looks up local Price-Per-SqFt 
    from the 'Market_Multipliers' Google Sheet tab. Falls back to $180.0 if not found.
    """
    default_multiplier = 180.0
    try:
        worksheet = spreadsheet.worksheet("Market_Multipliers")
        records = worksheet.get_all_records()
        for row in records:
            r_zip = str(row.get("Target_Zip_Code", "")).strip()
            r_city = str(row.get("City", "")).strip().lower()
            r_ppsf = float(row.get("Price_Per_SqFt", 0.0) or 0.0)
            
            if (zip_code and r_zip == zip_code) or (city and r_city in city.lower()):
                if r_ppsf > 0:
                    logger.info(f"Matched dynamic market multiplier: ${r_ppsf}/sqft for {city} / {zip_code}")
                    return r_ppsf
    except Exception as e:
        logger.warning(f"Could not fetch market multipliers tab (using default): {e}")
    
    return default_multiplier

def generate_purchase_agreement(lead_data):
    """
    Generates a custom Purchase & Sale Agreement (PSA) docx file dynamically.
    """
    doc = Document()
    doc.add_heading("PURCHASE AND SALE AGREEMENT", level=1)
    
    doc.add_paragraph(f"Date: {datetime.utcnow().strftime('%B %d, %Y')}")
    doc.add_paragraph(f"This agreement is entered into by and between the Seller: {lead_data['owner_name']} "
                      f"and the Buyer (or Assigns) for the real property located at:")
    
    p = doc.add_paragraph()
    p.add_run(f"{lead_data['property_address']}, {lead_data['city']}, {lead_data['region_state']} {lead_data['zip_code']}").bold = True
    
    doc.add_heading("1. Purchase Price & Terms", level=2)
    doc.add_paragraph(f"The total purchase price (Maximum Allowable Offer - MAO) agreed upon is: ${lead_data['mao']:,.2f}")
    doc.add_paragraph(f"Estimated Repairs factored: ${lead_data['repairs']:,.2f}")
    doc.add_paragraph(f"Original Seller Asking Price: ${lead_data['asking_price']:,.2f}")
    
    doc.add_heading("2. Closing & Title", level=2)
    doc.add_paragraph("Closing shall take place within 30 days of execution through a designated title company or escrow agent.")
    
    doc.add_heading("3. Signatures", level=2)
    doc.add_paragraph("Seller Signature: ___________________________ Date: _________")
    doc.add_paragraph("Buyer Signature: ____________________________ Date: _________")
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    temp_file.close()
    return temp_file.name

@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "Enterprise Acquisition Engine", "status": "online"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payload = request.get_json(force=True, silent=True)
        if not payload:
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Parse Tally webhook payload structure robustly
        form_data = {}
        payload_data = payload.get("data", payload)
        fields = payload_data.get("fields", [])
        
        if isinstance(fields, list):
            for field in fields:
                label = str(field.get("label", field.get("key", ""))).strip().lower()
                value = field.get("value")
                if label and value is not None:
                    form_data[label] = value
        
        if isinstance(payload, dict):
            for k, v in payload.items():
                form_data[k.strip().lower()] = v

        # Helper to safely fetch mapped values across various possible Tally label formats
        def get_field(*possible_keys):
            for key in possible_keys:
                clean_key = key.lower()
                for f_key, f_val in form_data.items():
                    if clean_key in f_key or f_key in clean_key:
                        if f_val not in [None, ""]:
                            return f_val
            return None

        # Extract & map fields corresponding to your Tally form UI
        property_address = str(get_field("property address", "address") or "Unknown Address")
        city = str(get_field("city") or "")
        region_state = str(get_field("state / region", "state", "region") or "")
        country = str(get_field("country") or "USA")
        zip_code = str(get_field("zip code", "zip") or "")
        
        owner_name = str(get_field("owner full name", "full name", "name") or "Unknown Seller")
        owner_phone = str(get_field("phone number", "phone") or "")
        owner_email = str(get_field("email address", "email") or "")
        
        # Numerical fields with robust parsing
        def parse_float(val, default=0.0):
            if val is None:
                return default
            try:
                clean_val = str(val).replace("$", "").replace(",", "").strip()
                return float(clean_val)
            except ValueError:
                return default

        def parse_int(val, default=3):
            if val is None:
                return default
            try:
                clean_val = str(val).replace(",", "").strip()
                return int(float(clean_val))
            except ValueError:
                return default

        asking_price = parse_float(get_field("asking price", "price"), 0.0)
        repairs = parse_float(get_field("estimated repairs", "repairs"), 0.0)
        square_footage = parse_float(get_field("square footage", "sqft"), 1500.0)
        bedrooms = parse_int(get_field("bedrooms", "beds"), 3)
        property_type = str(get_field("property type") or "Single Family")

        matched_buyers = []
        sheet_logged = False
        ppsf = 180.0  # default fallback

        if GOOGLE_SHEET_KEY and GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                gc = get_gspread_client()
                if gc:
                    spreadsheet = gc.open_by_key(GOOGLE_SHEET_KEY)
                    
                    # 1. Fetch Dynamic Multiplier (Zero-Cost Market Matrix)
                    ppsf = fetch_dynamic_multiplier(spreadsheet, zip_code, city)
                    
                    # 2. Buyer Matching Scan
                    try:
                        buyers_ws = spreadsheet.worksheet("Institutional_Buyers")
                        for buyer in buyers_ws.get_all_records():
                            b_id = buyer.get("Buyer_ID", "Unknown")
                            b_city = str(buyer.get("Target_City", "")).strip().lower()
                            b_zip = str(buyer.get("Target_Zip_Codes", "")).strip()
                            b_max = float(buyer.get("Max_Purchase_Price", 0.0) or 0.0)
                            b_beds = int(buyer.get("Min_Bedrooms", 0) or 0)
                            
                            if (not b_city or b_city in city.lower() or not b_zip or zip_code in b_zip) and \
                               (b_max == 0.0 or asking_price <= b_max) and (bedrooms >= b_beds):
                                matched_buyers.append({"buyer_id": b_id, "email": buyer.get("Contact_Email", "")})
                    except Exception as match_err:
                        logger.error(f"Buyer matching error: {match_err}")

                    # Core Heuristic Calculation using dynamic sheet multiplier
                    arv = square_footage * ppsf
                    mao = (arv * 0.70) - repairs
                    gross_spread = arv - asking_price - repairs
                    transaction_structure = "Wholesale / Cash"
                    currency = "USD"
                    status = "New Lead"

                    # 3. Log to Incoming_Leads
                    leads_ws = spreadsheet.worksheet("Incoming_Leads")
                    leads_ws.append_row([
                        property_address, city, region_state, country, owner_name, owner_phone,
                        owner_email, arv, repairs, asking_price, mao, gross_spread,
                        transaction_structure, currency, status
                    ])
                    sheet_logged = True
            except Exception as sheet_err:
                logger.error(f"Sheets error: {sheet_err}")
        
        # Fallback calculation if sheets are disconnected
        arv = square_footage * ppsf
        mao = (arv * 0.70) - repairs
        gross_spread = arv - asking_price - repairs

        # 4. Generate Contract if Spread meets threshold ($20,000+)
        contract_path = None
        if gross_spread >= 20000.0:
            contract_data = {
                "owner_name": owner_name,
                "property_address": property_address,
                "city": city,
                "region_state": region_state,
                "zip_code": zip_code,
                "mao": mao,
                "repairs": repairs,
                "asking_price": asking_price
            }
            contract_path = generate_purchase_agreement(contract_data)

        # 5. Telegram Notifications & Document Dispatch
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            buyer_text = "\n".join([f"• {b['buyer_id']} ({b['email']})" for b in matched_buyers]) or "None"
            alert_msg = (
                f"🚨 **Enterprise Lead Processed**\n\n"
                f"📍 **Address:** {property_address}, {city}, {region_state} {zip_code}\n"
                f"👤 **Owner:** {owner_name} ({owner_phone} | {owner_email})\n"
                f"📊 **Used PPSF:** ${ppsf:.2f}/sqft | **ARV:** ${arv:,.2f}\n"
                f"💰 **Asking:** ${asking_price:,.2f} | **MAO:** ${mao:,.2f}\n"
                f"📈 **Spread:** ${gross_spread:,.2f}\n\n"
                f"🏢 **Matched Buyers:**\n{buyer_text}\n\n"
                f"📋 **CRM Logged:** {'✅' if sheet_logged else '❌'} | "
                f"📝 **PSA Generated:** {'✅' if contract_path else '⏳ Below Threshold'}"
            )
            
            # Send Text Alert
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": alert_msg, "parse_mode": "Markdown"}
            )
            
            # Send Contract Document via Telegram if generated
            if contract_path:
                with open(contract_path, "rb") as doc_file:
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                        data={"chat_id": TELEGRAM_CHAT_ID, "caption": "📄 **Auto-Generated Purchase & Sale Agreement**"},
                        files={"document": ("Purchase_Agreement.docx", doc_file)}
                    )
                os.remove(contract_path)

        return jsonify({
            "status": "success",
            "message": "Zero-cost enterprise pipeline executed successfully.",
            "data": {"arv": arv, "mao": mao, "gross_spread": gross_spread, "contract_generated": bool(contract_path)}
        }), 200

    except Exception as e:
        logger.error(f"Webhook critical error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
