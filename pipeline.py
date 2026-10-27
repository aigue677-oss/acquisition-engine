import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

# Configuration & Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GCP_SA_KEY = os.environ.get("GCP_SA_KEY")
LEAD_API_URL = os.environ.get("LEAD_API_URL", "https://api.yourleadprovider.com/v1/leads") # Placeholder for your live provider endpoint
LEAD_API_KEY = os.environ.get("LEAD_API_KEY")

def fetch_live_leads():
    """
    Queries your institutional real estate data provider API securely 
    using environment tokens.
    """
    if not LEAD_API_KEY:
        print("Warning: LEAD_API_KEY not found. Operating in safe idle mode.")
        return []
    
    headers = {
        "Authorization": f"Bearer {LEAD_API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(LEAD_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Assumes the API returns a list under a 'leads' or 'data' key
        return data.get("leads", data.get("data", []))
    except Exception as e:
        print(f"CRITICAL API FETCH ERROR: {e}")
        return []

def get_existing_addresses(sheet):
    """
    Fetches already logged property addresses from Google Sheets 
    to enforce absolute deduplication.
    """
    try:
        # Assumes Address is in column 2 (Index 2)
        column_values = sheet.col_values(2)
        return set(column_values)
    except Exception as e:
        print(f"Warning: Could not fetch existing sheet state for deduplication: {e}")
        return set()

def send_telegram_alert(lead_data):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
        
    message = (
        f"🚨 **INSTITUTIONAL ACQUISITION ALERT** 🚨\n\n"
        f"📍 **Address:** {lead_data.get('address', 'N/A')}\n"
        f"💰 **Asking Price:** ${lead_data.get('price', 0):,}\n"
        f"📊 **ARV:** ${lead_data.get('arv', 0):,}\n"
        f"📈 **Est. Equity:** {lead_data.get('equity', 'N/A')}\n"
        f"🔍 **Source:** {lead_data.get('source', 'Live Provider Feed')}"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

def log_to_google_sheets(sheet, lead_data):
    row = [
        lead_data.get("date", "2026-10-27"),
        lead_data.get("address", "N/A"),
        lead_data.get("price", 0),
        lead_data.get("arv", 0),
        lead_data.get("equity", "N/A"),
        "New Live Lead"
    ]
    sheet.append_row(row)
    print(f"Successfully logged live lead: {lead_data.get('address')}")

if __name__ == "__main__":
    # Initialize Google Sheets connection
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(GCP_SA_KEY)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("Wholesale Acquisitions Master Pipeline").sheet1
    
    # Pull current state for deduplication
    existing_addresses = get_existing_addresses(sheet)
    
    # Fetch live incoming properties
    live_leads = fetch_live_leads()
    
    if not live_leads:
        print("Pipeline poll complete: No new unprocessed leads detected.")
    else:
        new_count = 0
        for lead in live_leads:
            address = lead.get('address')
            if address in existing_addresses:
                print(f"Skipping duplicate record: {address}")
                continue
                
            # Execute institutional notification and logging sequence
            send_telegram_alert(lead)
            log_to_google_sheets(sheet, lead)
            existing_addresses.add(address) # Prevent intra-run duplicates
            new_count += 1
            
        print(f"Pipeline execution complete. Processed {new_count} new verified leads.")
            
