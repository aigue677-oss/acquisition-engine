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
    
    try:
        creds_dict = json.loads(GCP_SA_KEY)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        # Open the Master Pipeline Sheet
        sheet = client.open("Wholesale Acquisitions Master Pipeline").sheet1

        # Map lead data to columns
        row = [
            lead_data.get("address"),
            lead_data.get("owner", "Institutional Trust"),
            lead_data.get("phone", "+1 (555) 000-0000"),
            lead_data.get("method", "SIMULTANEOUS DOUBLE-CLOSE (A-B-C)"),
            lead_data.get("asking_price", "$65,000"),
            lead_data.get("mao", "$127,000"),
            lead_data.get("net_payout", "$60,500"),
            lead_data.get("status", "Clear Title")
        ]
        
        sheet.append_row(row)
        print(f"Successfully logged {lead_data.get('address')} directly to Google Sheets!")
    except Exception as e:
        print(f"Google Sheets Logging Error: {e}")

def run_pipeline():
    # Processed leads matching your engine's multi-region output
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
        },
        {
            "address": "714 Heritage Way, Northern Suburbs",
            "owner": "Private Estate",
            "phone": "+1 (555) 432-1190",
            "method": "SIMULTANEOUS DOUBLE-CLOSE (A-B-C)",
            "asking_price": "$95,000",
            "mao": "$145,000",
            "net_payout": "$48,000",
            "status": "Clear Title"
        }
    ]

    for lead in leads:
        print(f"-> [AUTOMATED DISPATCH] Processing {lead['address']}...")
        
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

    print("--- EXPANDED MULTI-REGION, CLEVA & PIPELINE LOGGING COMPLETE ---")

if __name__ == "__main__":
    run_pipeline()
    
