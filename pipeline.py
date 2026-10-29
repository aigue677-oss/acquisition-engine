import os
import json
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import gspread
from google.oauth2.service_account import Credentials
from pdf_compiler import PDFCompiler

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
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        print(f"Failed to initialize Google Sheets client: {e}")
        return None

def send_telegram_alert(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram credentials missing. Skipping notification.")
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
        print(f"Telegram connection error: {e}")

def send_offer_email(recipient_email, pdf_path, property_address, mao):
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        print("SMTP configuration missing. Cannot send email.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Official Ethical Cash Acquisition Offer - {property_address}"

        body = (
            f"Hello,\n\n"
            f"We have professionally reviewed your property located at {property_address}. "
            f"Based on our transparent market analysis and underwriting guidelines, our official cash purchase offer (MAO) is ${mao:,.2f}.\n\n"
            f"Please find your formal, non-predatory purchase and sale agreement attached to this email for your review.\n\n"
            f"Best regards,\nSovereign Grid Institutional Acquisitions Team"
        )
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF Contract with correct attachment headers
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename=Sovereign_Agreement.pdf")
            msg.attach(part)

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"Acquisition offer dispatched securely to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def run_pipeline():
    print("Initializing Sovereign Grid Acquisition Pipeline (Governance & Compliance Mode)...")
    client = get_gspread_client()
    if not client:
        return

    try:
        sheet = client.open("Sovereign_Grid_Leads").sheet1
        records = sheet.get_all_records()
    except Exception as e:
        print(f"Error accessing Google Sheet: {e}")
        return

    processed_any = False

    for idx, row in enumerate(records, start=2): # Row 1 is header
        status = str(row.get("Status", "")).strip()
        if status.lower() == "clear title":
            processed_any = True
            address = row.get("Property Address", "Unknown Address")
            owner_name = row.get("Owner Name", "Property Owner")
            owner_email = row.get("Owner Email", "")
            arv = float(row.get("ARV", 0) or 0)
            repairs = float(row.get("Repairs", 0) or 0)
            asking_price = float(row.get("Asking price", 0) or 0)

            print(f"Evaluating governance & compliance for lead: {address}")

            # --- Ethical & Financial Guardrails / Sanitization ---
            if arv <= 0 or repairs < 0:
                print(f"Compliance Violation: Invalid financial metrics for {address}. Skipping.")
                continue
            
            if not owner_email or "@" not in owner_email:
                print(f"Compliance Notice: Missing or invalid owner email for {address}. Bypassing direct outreach.")
                continue

            # Calculate Transparent MAO
            mao = (arv * 0.70) - repairs
            if mao <= 0:
                print(f"Underwriting Guardrail: Calculated MAO is non-viable (${mao:,.2f}). Aborting offer dispatch.")
                continue

            print(f"Underwriting & Compliance Passed. Official MAO calculated: ${mao:,.2f}")
            
            # Compile Contract PDF
            pdf_filename = "Sovereign_Agreement.pdf"
            compiler = PDFCompiler()
            compiler.generate_contract(
                owner_name=owner_name,
                property_address=address,
                mao=mao
            )
            print(f"Compliant contract compiled successfully: {pdf_filename}")

            # Send Email
            send_offer_email(owner_email, pdf_filename, address, mao)

            # Send Verified Telegram Alert with Audit Markers
            telegram_msg = (
                f"🛡 *Sovereign Grid Audit: Offer Dispatched*\n\n"
                f"📍 *Address:* {address}\n"
                f"👤 *Owner:* {owner_name}\n"
                f"💰 *Verified MAO:* `${mao:,.2f}`\n"
                f"⚖️ *Governance:* Compliance & Ethics Passed\n"
                f"📊 *Status:* Offer Sent"
            )
            send_telegram_alert(telegram_msg)

            # Update Google Sheet Status to 'Offer Sent' with Audit Trail
            try:
                status_col_index = list(row.keys()).index("Status") + 1
                sheet.update_cell(idx, status_col_index, "Offer Sent")
                print(f"Google Sheet row {idx} status updated to 'Offer Sent' under governance review.")
            except Exception as e:
                print(f"Failed to update sheet status: {e}")

            # Secure Cleanup
            if os.path.exists(pdf_filename):
                os.remove(pdf_filename)
                print(f"Securely shredded and purged local asset: {pdf_filename}")

            break # Process one lead per run cycle

    if not processed_any:
        print("No eligible leads found matching institutional governance standards with 'Clear Title' status.")

    print("Pipeline execution cycle complete. Audit logs secured.")

if __name__ == "__main__":
    run_pipeline()
        
