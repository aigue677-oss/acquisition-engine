import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from engine_sovereign import SovereignEngine
from pdf_compiler import PDFCompiler
from email_dispatcher import EmailDispatcher
from memory_wiper import MemoryWiper

def send_telegram_alert(message: str):
    """Sends immediate institutional command alerts straight to your Telegram channel."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Telegram alert transmission failed: {e}")

def fetch_live_leads_from_sheets():
    """
    Connects securely to Google Sheets and fetches rows ready for outreach.
    """
    try:
        creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not creds_json:
            print("Google Service Account credentials missing from environment.")
            return []

        creds_dict = json.loads(creds_json)
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        sheet = client.open("Sovereign_Grid_Leads").sheet1
        records = sheet.get_all_records()

        dynamic_leads = []
        for idx, row in enumerate(records, start=2): # start=2 accounts for header row
            # We look for rows where Status is set to 'Clear Title' (or change to your preferred trigger status)
            status_val = str(row.get("Status", "")).strip().lower()
            if status_val == "clear title":
                lead_data = {
                    "row_index": idx,
                    "seller_name": row.get("Owner Name", "Property Owner"),
                    "email": row.get("Owner Email", "seller@example.com"), # Fallback if email column isn't filled yet
                    "address": row.get("Property Address", ""),
                    "arv": float(row.get("ARV", 250000.0)), # Defaults if column is blank
                    "repair_costs": float(row.get("Repairs", 15000.0)),
                    "date": str(row.get("Date", ""))
                }
                dynamic_leads.append(lead_data)

        return dynamic_leads
    except Exception as e:
        print(f"Error fetching live leads from Google Sheets: {e}")
        return []

def update_lead_status_in_sheet(row_index: int, new_status: str):
    """Updates the Status column in your Google Sheet once a deal is processed."""
    try:
        creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        creds_dict = json.loads(creds_json)
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("Sovereign_Grid_Leads").sheet1
        header = sheet.row_values(1)
        status_col_idx = header.index("Status") + 1
        sheet.update_cell(row_index, status_col_idx, new_status)
    except Exception as e:
        print(f"Failed to update sheet status: {e}")

def run_pipeline():
    print("Initializing Sovereign Grid Acquisition Pipeline (Custom Schema Mode)...")

    sovereign_engine = SovereignEngine(max_offer_discount=0.70)
    pdf_compiler = PDFCompiler()
    email_dispatcher = EmailDispatcher()
    memory_wiper = MemoryWiper()

    leads = fetch_live_leads_from_sheets()
    if not leads:
        print("No eligible leads found with 'Clear Title' status.")
        return

    for lead in leads:
        print(f"Processing live target lead: {lead['address']}")

        mao_offer = sovereign_engine.calculate_mao(lead['arv'], lead['repair_costs'])
        offer_package = sovereign_engine.draft_acquisition_email(
            seller_name=lead['seller_name'],
            property_address=lead['address'],
            arv=lead['arv'],
            repair_costs=lead['repair_costs']
        )

        lead_contract_data = {
            "address": lead['address'],
            "price": mao_offer,
            "arv": lead['arv'],
            "equity": f"{((lead['arv'] - mao_offer)/lead['arv'])*100:.1f}%",
            "date": lead['date']
        }

        pdf_filename = pdf_compiler.generate_contract(lead_contract_data)

        email_dispatched = email_dispatcher.send_offer(
            recipient_email=lead['email'],
            subject=offer_package['subject'],
            body_text=offer_package['body']
        )

        alert_message = (
            f"🚨 *SOVEREIGN GRID: LIVE DEAL PROCESSED*\n\n"
            f"📍 *Property:* {lead['address']}\n"
            f"👤 *Owner:* {lead['seller_name']}\n"
            f"💰 *Calculated MAO:* ${mao_offer:,.2f}\n"
            f"📧 *Outreach Status:* {'Dispatched Successfully' if email_dispatched else 'Failed / Skipped'}\n"
            f"📄 *Contract:* Compiled in-memory ({pdf_filename})"
        )
        send_telegram_alert(alert_message)

        # Update status to prevent duplication
        update_lead_status_in_sheet(lead['row_index'], "Offer Sent")
        memory_wiper.purge_transient_files()

    print("Pipeline execution cycle complete. All local traces securely shredded.")

if __name__ == "__main__":
    run_pipeline()
    
