import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

# Configuration from GitHub Secrets / Environment
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GCP_SA_KEY = os.environ.get("GCP_SA_KEY")

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def log_to_google_sheets(lead_data):
    if not GCP_SA_KEY:
        print("Error: GCP_SA_KEY secret not found.")
        return

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Load credentials securely from the environment secret
    creds_dict = json.loads(GCP_SA_KEY)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)

    # Open the Master Pipeline Sheet
    sheet = client.open("Wholesale Acquisitions Master Pipeline").sheet1

    # Map your institutional lead data to columns
    row = [
        lead_data.get("address"),
        lead_data.get("owner"),
        lead_data.get("phone"),
        lead_data.get("method"),
        lead_data.get("asking_price"),
        lead_data.get("mao"),
        lead_data.get("net_payout"),
        lead_data.get("status", "New Lead")
    ]
    
    sheet.append_row(row)
    print(f"Successfully logged {lead_data.get('address')} directly to Google Sheets!")

def run_pipeline():
    # Example simulated institutional lead payload matching your criteria
    leads = [
        {
            "address": "4022 Oakridge Terrace, Metro Core",
            "owner": "Institutional Trust / Verified Heir",
            "phone": "+1 (555) 891-3342",
            "method": "SIMULTANEOUS DOUBLE-CLOSE (A-B-C)",
            "asking_price": "$65,000",
            "mao": "$127,000",
            "net_payout": "$60,500",
            "status": "Clear Title"
        }
    ]

    for lead in leads:
        # 1. Fire Telegram Alert
        msg = (
            "🏛️ INSTITUTIONAL ACQUISITIONS DESK 🏛️\n\n"
            f"📍 Address: {lead['address']}\n"
            f"👤 Owner: {lead['owner']}\n"
            f"📞 Direct Phone: {lead['phone']}\n"
            f"⚙️ Method: {lead['method']}\n"
            f"💵 Asking: {lead['asking_price']} | 🎯 MAO: {lead['mao']}\n"
            f"💡 Structure: Double-Close | Net Payout: {lead['net_payout']} (Wired to Cleva USD Account)\n\n"
            "🏦 Payout Destination: Cleva U.S. Domestic Wire Routing Ready."
        )
        send_telegram_alert(msg)
        
        # 2. Log Directly to Google Sheets
        log_to_google_sheets(lead)

if __name__ == "__main__":
    run_pipeline()
    
