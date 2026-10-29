import os
import json
import gspread
from google.oauth2.service_account import Credentials
import requests

# --- Configuration & Credentials Setup ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_gspread_client():
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        return None
    creds_dict = json.loads(service_account_json)
    credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(credentials)

def send_telegram_alert(telegram_msg):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": telegram_msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

def parse_incoming_reply(sender_email, email_body):
    """
    Parses incoming seller email responses to detect acceptance and syncs with Google Sheets.
    """
    client = get_gspread_client()
    if not client:
        return {"status": "error", "message": "Google Sheets client failed"}

    try:
        sheet = client.open("Sovereign_Grid_Leads").sheet1
        records = sheet.get_all_records()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Search for the row matching the seller's email
    target_row = None
    row_idx = None
    for idx, row in enumerate(records, start=2):
        if row.get("Owner Email", "").strip().lower() == sender_email.strip().lower():
            target_row = row
            row_idx = idx
            break

    if not target_row:
        return {"status": "not_found", "message": f"No lead found for email {sender_email}"}

    body_lower = email_body.lower()
    acceptance_keywords = ["accept", "agreement", "deal", "let's do it", "approved", "sounds good", "proceed", "sign"]
    
    is_accepted = any(keyword in body_lower for keyword in acceptance_keywords)

    if is_accepted:
        # Update sheet status to Offer Accepted (Column 15)
        sheet.update_cell(row_idx, 15, "Offer Accepted")
        
        address = target_row.get("Property Address")
        city = target_row.get("City")
        currency = target_row.get("Currency", "USD")
        mao = target_row.get("MAO", "N/A")
        owner_name = target_row.get("Owner Name")

        telegram_msg = (
            f"🚨 *SOVEREIGN GRID: OFFER ACCEPTED!* 🚨\n\n"
            f"🎉 *Seller {owner_name} has accepted the offer!* 🎉\n"
            f"📍 *Property:* `{address}, {city}`\n"
            f"💰 *Agreed MAO:* `{mao} {currency}`\n"
            f"🚀 *Action Required:* Initiate Cleva Multi-Currency Escrow & Closing Protocol immediately!"
        )
        send_telegram_alert(telegram_msg)
        return {"status": "success", "message": "Offer acceptance processed and sheet updated."}
    else:
        # Update sheet status to Counter/In Negotiation (Column 15)
        sheet.update_cell(row_idx, 15, "Counter / Review Required")
        address = target_row.get("Property Address")
        
        telegram_msg = (
            f"💬 *SOVEREIGN GRID: SELLER REPLY RECEIVED* 💬\n\n"
            f"📍 *Property:* `{address}`\n"
            f"✉️ *Message Snippet:* _{email_body[:150]}...\n_\n"
            f"🔍 *Action:* Manual review required for counter-offer."
        )
        send_telegram_alert(telegram_msg)
        return {"status": "success", "message": "Seller reply logged as negotiation required."}
  
