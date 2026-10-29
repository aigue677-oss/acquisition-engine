import os
import json
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.message import EmailMessage
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- Configuration & Credentials Setup ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_gspread_client():
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        print("Error: Google Service Account credentials missing from environment.")
        return None
    try:
        creds_dict = json.loads(service_account_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Failed to initialize Google Sheets client: {e}")
        return None

def generate_pdf_contract(address, owner_name, mao):
    filename = "Sovereign_Agreement.pdf"
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "SOVEREIGN GRID INSTITUTIONAL ACQUISITIONS")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 65, "Automated Global Real Estate Underwriting Engine")
        
        c.setLineWidth(1)
        c.line(50, height - 75, width - 50, height - 75)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 110, "MEMORANDUM OF INTENT / CASH PURCHASE AGREEMENT")

        c.setFont("Helvetica", 11)
        text_y = height - 140
        lines = [
            f"Dear {owner_name},",
            "",
            f"Sovereign Grid has completed its institutional underwriting and multi-market governance review",
            f"for the property located at: {address}.",
            "",
            f"Based on current market valuations, projected repairs, and clear title parameters,",
            f"our acquisition committee has approved a formal all-cash purchase offer of:",
            "",
            f"OFFER PURCHASE PRICE: ${mao:,.2f}",
            "",
            "Why Sovereign Grid?",
            "- 100% All-Cash Offer (Zero bank financing contingencies)",
            "- Zero Agent Commissions or Hidden Fees (You keep 100% of proceeds)",
            "- As-Is Purchase (No repairs or cleaning required)",
            "- Flexible Closing Timeline (7 to 21 days)",
            "",
            "Please reply directly to this dispatch to accept terms and execute closing paperwork."
        ]

        for line in lines:
            c.drawString(50, text_y, line)
            text_y -= 18

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, 40, "Generated autonomously by Sovereign Grid Compliance Engine. Confidential & Legally Binding.")
        
        c.save()
        return filename
    except Exception as e:
        print(f"PDF Generation failed for {address}: {e}")
        return None

def send_telegram_alert(telegram_msg):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("Telegram credentials missing. Skipping alert.")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": telegram_msg, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Telegram API warning: {response.text}")
    except Exception as e:
        print(f"Failed to dispatch Telegram alert securely: {e}")

def run_pipeline():
    print("Initializing Sovereign Grid Acquisition Pipeline (LIVE Production Mode)...")
    client = get_gspread_client()
    if not client:
        return

    try:
        sheet = client.open("Sovereign_Grid_Leads").sheet1
        records = sheet.get_all_records()
    except Exception as e:
        print(f"Critical error accessing Google Sheet database: {e}")
        return

    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    # --- Feature: Advanced Priority Queueing ---
    valid_leads = []
    for idx, row in enumerate(records, start=2):
        row["_row_index"] = idx
        valid_leads.append(row)

    def get_sort_key(r):
        try:
            arv = float(r.get("ARV", 0) or 0)
            repairs = float(r.get("Repairs", 0) or 0)
            asking = float(r.get("Asking Price", 0) or 0)
            return arv - repairs - asking
        except:
            return 0.0

    valid_leads.sort(key=get_sort_key, reverse=True)

    for row in valid_leads:
        idx = row["_row_index"]
        status = row.get("Status", "")
        
        try:
            # 1. Process New Clear Title Leads with Priority Queueing
            if status == "Clear Title":
                address = row.get("Property Address")
                owner_name = row.get("Owner Name")
                owner_phone = row.get("Owner Phone")
                owner_email = row.get("Owner Email")
                arv = float(row.get("ARV", 0) or 0)
                repairs = float(row.get("Repairs", 0) or 0)
                asking_price = float(row.get("Asking Price", 0) or 0)

                print(f"Evaluating live priority governance for lead: {address}")
                mao = (arv * 0.70) - repairs
                gross_spread = arv - repairs - asking_price

                if gross_spread > 0 and asking_price <= mao:
                    print(f"Underwriting Passed. Priority MAO calculated: ${mao:,.2f} (Spread: ${gross_spread:,.2f})")
                    pdf_filename = generate_pdf_contract(address, owner_name, mao)
                    
                    if pdf_filename:
                        try:
                            msg = EmailMessage()
                            msg['Subject'] = f"Official All-Cash Acquisition Offer - {address}"
                            msg['From'] = sender_email
                            msg['To'] = owner_email
                            msg.set_content(
                                f"Dear {owner_name},\n\nSovereign Grid Institutional Acquisitions has completed its "
                                f"underwriting for your property located at {address}.\n\n"
                                f"Our formal all-cash purchase offer is: ${mao:,.2f}\n\n"
                                "Please review the attached formal non-predatory purchase agreement and reply to accept.\n\n"
                                "Best regards,\nSovereign Grid Acquisitions Team"
                            )

                            with open(pdf_filename, 'rb') as f:
                                msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=f.name)

                            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                                server.starttls()
                                server.login(sender_email, sender_password)
                                server.send_message(msg)
                            print(f"Live acquisition offer dispatched securely to {owner_email}")
                        except Exception as email_err:
                            print(f"Email dispatch error for {address}: {email_err}")

                    telegram_msg = (
                        f"🌐 *SOVEREIGN GRID: LIVE OFFER DISPATCHED* 🌐\n\n"
                        f"📍 *Property:* `{address}`\n"
                        f"👤 *Owner:* {owner_name} ({owner_phone})\n"
                        f"💰 *Calculated MAO:* `${mao:,.2f}`\n"
                        f"📊 *Gross Spread:* `${gross_spread:,.2f}`\n"
                        f"🚀 *Status:* Live Institutional Offer Sent."
                    )
                    send_telegram_alert(telegram_msg)

                    sheet.update_cell(idx, 11, "Offer Sent")
                    print(f"Google Sheet row {idx} status successfully updated to 'Offer Sent'.")

                    if pdf_filename and os.path.exists(pdf_filename):
                        os.remove(pdf_filename)
                else:
                    print(f"Lead failed institutional governance thresholds. Gross Spread: ${gross_spread:,.2f}")

            # 2. Process Lifecycle Follow-Up State Management with Error Isolation
            elif status == "Offer Sent":
                address = row.get("Property Address")
                owner_name = row.get("Owner Name")
                print(f"Checking live lifecycle for pending offer: {address}")
                
                sheet.update_cell(idx, 11, "Follow-Up Required")
                
                followup_msg = (
                    f"🔄 *SOVEREIGN GRID: LIVE FOLLOW-UP REQUIRED* 🔄\n\n"
                    f"📍 *Property:* `{address}`\n"
                    f"👤 *Owner:* {owner_name}\n"
                    f"⏱️ *Action:* Initial live offer pending response. Secondary re-engagement required."
                )
                send_telegram_alert(followup_msg)
                print(f"Row {idx} transitioned to 'Follow-Up Required'.")

        except Exception as row_error:
            print(f"Error processing row {idx} ({row.get('Property Address', 'Unknown')}): {row_error}")
            continue

    print("LIVE Production pipeline execution cycle complete. All systems secure.")

if __name__ == "__main__":
    run_pipeline()
    
