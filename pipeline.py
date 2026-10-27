import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GCP_SA_KEY = os.environ.get("GCP_SA_KEY")

def send_telegram_alert(lead_data):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return

    message = (
        f"🚨 **INSTITUTIONAL ACQUISITION LEAD** 🚨\n\n"
        f"📍 **Address:** {lead_data.get('address')}\n"
        f"🏢 **Owner:** {lead_data.get('owner', 'Institutional Trust')}\n"
        f"📞 **Phone:** {lead_data.get('phone', '+1 (555) 000-0000')}\n"
        f"💼 **Method:** {lead_data.get('method', 'SIMULTANEOUS DOUBLE-CLOSE (A-B-C)')}\n"
        f"💵 **Asking Price:** {lead_data.get('asking_price', '$65,000')}\n"
        f"📊 **MAO:** {lead_data.get('mao', '$127,000')}\n"
        f"💰 **Net Payout:** {lead_data.get('net_payout', '$60,500')}\n"
        f"🏷️ **Status:** {lead_data.get('status', 'Clear Title')}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"Telegram alert sent for {lead_data.get('address')}")
    else:
        print(f"Failed to send Telegram alert: {response.text}")

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

        # Open your master pipeline sheet
        sheet = client.open("Wholesale Acquisitions Master Pipeline").sheet1
        print("Successfully connected to Google Sheets spreadsheet object.")

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
        print(f"Successfully appended row for {lead_data.get('address')}!")
    except Exception as e:
        print(f"CRITICAL GOOGLE SHEETS ERROR: {str(e)}")

if __name__ == "__main__":
    # Sample pipeline leads payload
    leads = [
        {
            "address": "4022 Oakridge Terrace",
            "owner": "Apex Holdings LLC",
            "phone": "+1 (312) 555-0199",
            "method": "SIMULTANEOUS DOUBLE-CLOSE (A-B-C)",
            "asking_price": "$65,000",
            "mao": "$127,000",
            "net_payout": "$60,500",
            "status": "Clear Title"
        },
        {
            "address": "714 Heritage Way",
            "owner": "Meridian Trust",
            "phone": "+1 (404) 555-0143",
            "method": "WHOLESALE ASSIGNMENT",
            "asking_price": "$89,000",
            "mao": "$145,000",
            "net_payout": "$56,000",
            "status": "Pending Verification"
        }
    ]

    for lead in leads:
        send_telegram_alert(lead)
        log_to_google_sheets(lead)
        
