import json
import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from valuation_engine import calculate_heuristic_arv, calculate_dynamic_mao

# Google Sheets Setup Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_gspread_client():
    """Initializes and returns the authenticated gspread client using either an environment JSON string or local file."""
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    if creds_json:
        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    else:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
        if os.path.exists(creds_path):
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        else:
            raise FileNotFoundError("Google service account credentials not found in environment variables or file.")
    
    client = gspread.authorize(creds)
    return client

def send_telegram_alert(message: str):
    """Sends an automated notification alert via your Telegram bot."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram credentials not found. Skipping notification.")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram notification sent successfully.")
        else:
            print(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {str(e)}")

def process_inbound_lead(webhook_payload: dict):
    """
    Core pipeline function that processes inbound lead webhooks,
    runs internal heuristic underwriting, syncs to Google Sheets, and fires Telegram alerts.
    """
    property_address = webhook_payload.get("address", "Unknown Address")
    seller_name = webhook_payload.get("seller_name", "Unknown Seller")
    seller_asking_price = float(webhook_payload.get("asking_price", 0.0))
    estimated_repairs = float(webhook_payload.get("repairs", 15000.0))
    square_footage = float(webhook_payload.get("square_footage", 1500.0))

    print(f"Running internal heuristic underwriting for: {property_address}")
    
    try:
        # 1. Compute underwriting metrics
        arv = calculate_heuristic_arv(square_footage)
        mao = calculate_dynamic_mao(arv, estimated_repairs)
        gross_spread = arv - estimated_repairs - seller_asking_price
        
        # 2. State Machine Decision Rule
        status = "Offer Accepted" if seller_asking_price <= mao else "Review Required"

        # 3. Package row data
        row_data = [
            property_address,
            seller_name,
            seller_asking_price,
            arv,
            estimated_repairs,
            mao,
            gross_spread,
            status
        ]
        
        # 4. Push data to Google Sheets
        client = get_gspread_client()
        sheet_key = os.getenv("GOOGLE_SHEET_KEY")
        
        if sheet_key:
            sheet = client.open_by_key(sheet_key).sheet1
            sheet.append_row(row_data)
            print(f"Google Sheet successfully updated for: {property_address}")
        else:
            print("Warning: GOOGLE_SHEET_KEY environment variable not set. Skipping sheet sync.")

        # 5. Format and send Telegram Alert
        alert_message = (
            f"🚨 *New Real Estate Lead Processed*\n\n"
            f"📍 *Address:* {property_address}\n"
            f"👤 *Seller:* {seller_name}\n"
            f"💰 *Asking Price:* ${seller_asking_price:,.2f}\n"
            f"🏡 *Heuristic ARV:* ${arv:,.2f}\n"
            f"🛠 *Est. Repairs:* ${estimated_repairs:,.2f}\n"
            f"📊 *Calculated MAO:* ${mao:,.2f}\n"
            f"📈 *Gross Spread:* ${gross_spread:,.2f}\n"
            f"⚡ *Status:* *{status}*"
        )
        send_telegram_alert(alert_message)

        print(f"Underwriting Complete & Notified. Status: {status}")
        return row_data

    except Exception as e:
        print(f"Error in heuristic pipeline execution: {str(e)}")
        raise e
            
