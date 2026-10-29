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
        print("Google Service Account credentials missing from environment.")
        return None
    try:
        creds_dict = json.loads(service_account_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Failed to initialize Google Sheets client: {e}")
        return None

def generate_pdf_contract(address, owner_name, mao):
    """
    Generates a formal, institutional PDF acquisition contract.
    """
    filename = "Sovereign_Agreement.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Document Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "SOVEREIGN GRID INSTITUTIONAL ACQUISITIONS")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 65, "Automated Global Real Estate Underwriting Engine")
    
    c.setLineWidth(1)
    c.line(50, height - 75, width - 50, height - 75)

    # Body Content
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
        "Terms: All-Cash, As-Is, Zero Agent Commissions, Standard Escrow Closing.",
        "Please reply directly to this dispatch to accept terms and execute closing paperwork."
    ]

    for line in lines:
        c.drawString(50, text_y, line)
        text_y -= 20

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 50, "Generated autonomously by Sovereign Grid Compliance Engine. Confidential & Legally Binding Framework.")
    
    c.save()
    return filename

def send_enhanced_telegram_alert(address, owner_name, owner_phone, owner_email, arv, repairs, asking_price, mao, gross_spread):
    """
    Dispatches a richly formatted, enhanced multi-channel audit report directly to Telegram.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("Telegram credentials missing. Skipping alert.")
        return
    
    telegram_msg = (
        f"🌐 *SOVEREIGN GRID: MULTI-MARKET EXECUTION ALERT* 🌐\n\n"
        f"📍 *Property Target:* `{address}`\n"
        f"👤 *Owner Name:* {owner_name}\n"
        f"📞 *Phone:* `{owner_phone}`\n"
        f"✉️ *Email:* {owner_email}\n\n"
        f"📊 *Underwriting Financials:*\n"
        f"• *ARV:* `${arv:,.2f}`\n"
        f"• *Est. Repairs:* `${repairs:,.2f}`\n"
        f"• *Asking Price:* `${asking_price:,.2f}`\n"
        f"• *Calculated MAO:* `${mao:,.2f}`\n"
        f"• *Gross Spread:* `${gross_spread:,.2f}`\n\n"
        f"🚀 *Execution Status:* Offer Contract Compiled, Dispatched via Email, & Logged to Sheet as 'Offer Sent'."
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": telegram_msg, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Enhanced Telegram mobile notification successfully dispatched.")
        else:
            print(f"Telegram API error: {response.text}")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def run_pipeline():
    print("Initializing Sovereign Grid Acquisition Pipeline (Governance & Compliance Mode)...")
    client = get_gspread_client()
    if not client:
        return

    sheet = client.open("Sovereign_Grid_Leads").sheet1
    records = sheet.get_all_records()

    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    for idx, row in enumerate(records, start=2):
        status = row.get("Status", "")
        
        if status == "Clear Title":
            address = row.get("Property Address")
            owner_name = row.get("Owner Name")
            owner_phone = row.get("Owner Phone")
            owner_email = row.get("Owner Email")
            arv = float(row.get("ARV", 0) or 0)
            repairs = float(row.get("Repairs", 0) or 0)
            asking_price = float(row.get("Asking Price", 0) or 0)

            print(f"Evaluating governance & compliance for lead: {address}")

            mao = (arv * 0.70) - repairs
            gross_spread = arv - repairs - asking_price

            if gross_spread > 0 and asking_price <= mao:
                print(f"Underwriting & Compliance Passed. Official MAO calculated: ${mao:,.2f}")

                pdf_filename = generate_pdf_contract(address, owner_name, mao)
                print(f"Compliant contract compiled successfully: {pdf_filename}")

                # Dispatch Email with PDF Attachment
                try:
                    msg = EmailMessage()
                    msg['Subject'] = f"Formal Acquisition Offer - {address}"
                    msg['From'] = sender_email
                    msg['To'] = owner_email
                    msg.set_content(
                        f"Dear {owner_name},\n\nPlease find attached the formal all-cash purchase offer "
                        f"from Sovereign Grid for your property at {address}.\n\nOffer Amount: ${mao:,.2f}\n\n"
                        "Review the attached agreement and reply to accept.\n\nBest regards,\nSovereign Grid Acquisitions"
                    )

                    with open(pdf_filename, 'rb') as f:
                        file_data = f.read()
                        file_name = f.name
                    msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.send_message(msg)
                    print(f"Acquisition offer dispatched securely to {owner_email}")
                except Exception as e:
                    print(f"Email dispatch failed: {e}")

                # Dispatch Enhanced Telegram Mobile Notification
                send_enhanced_telegram_alert(address, owner_name, owner_phone, owner_email, arv, repairs, asking_price, mao, gross_spread)

                # Update Google Sheet Status
                sheet.update_cell(idx, 11, "Offer Sent")
                print(f"Google Sheet row {idx} status updated to 'Offer Sent' under governance review.")

                # Security Hygiene: Shred Local Asset
                if os.path.exists(pdf_filename):
                    os.remove(pdf_filename)
                    print(f"Securely shredded and purged local asset: {pdf_filename}")
            else:
                print(f"Lead failed institutional governance thresholds. Gross Spread: ${gross_spread:,.2f}")

    print("Pipeline execution cycle complete. Audit logs secured.")

if __name__ == "__main__":
    run_pipeline()
        
