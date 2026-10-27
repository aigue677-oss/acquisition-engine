import os
import requests
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

def run_pipeline():
    print("Initializing Sovereign Grid Acquisition Pipeline (Phase 6 Integrated)...")

    # 1. Initialize Modules
    sovereign_engine = SovereignEngine(max_offer_discount=0.70)
    pdf_compiler = PDFCompiler()
    email_dispatcher = EmailDispatcher()
    memory_wiper = MemoryWiper()

    # 2. Simulated Live Lead Ingress (Replace with your Google Sheets / API ingestion logic)
    # In production, this data feeds dynamically from your ingestion source.
    sample_lead = {
        "seller_name": "Property Owner",
        "email": "seller@example.com",
        "address": "123 Sovereign Way, Test City, TX",
        "arv": 250000.0,
        "repair_costs": 15000.0,
        "date": "2026-10-27"
    }

    print(f"Processing target lead: {sample_lead['address']}")

    # 3. Compute MAO & Draft Acquisition Email
    mao_offer = sovereign_engine.calculate_mao(sample_lead['arv'], sample_lead['repair_costs'])
    offer_package = sovereign_engine.draft_acquisition_email(
        seller_name=sample_lead['seller_name'],
        property_address=sample_lead['address'],
        arv=sample_lead['arv'],
        repair_costs=sample_lead['repair_costs']
    )

    lead_contract_data = {
        "address": sample_lead['address'],
        "price": mao_offer,
        "arv": sample_lead['arv'],
        "equity": f"{((sample_lead['arv'] - mao_offer)/sample_lead['arv'])*100:.1f}%",
        "date": sample_lead['date']
    }

    # 4. Compile In-Memory Contract PDF
    pdf_filename = pdf_compiler.generate_contract(lead_contract_data)

    # 5. Dispatch Outbound Email to Seller (Stealth SMTP)
    email_dispatched = email_dispatcher.send_offer(
        recipient_email=sample_lead['email'],
        subject=offer_package['subject'],
        body_text=offer_package['body']
    )

    # 6. Notify Operator via Telegram
    alert_message = (
        f"🚨 *SOVEREIGN GRID: OFFER DISPATCHED*\n\n"
        f"📍 *Property:* {sample_lead['address']}\n"
        f"💰 *Calculated MAO:* ${mao_offer:,.2f}\n"
        f"📊 *Estimated ARV:* ${sample_lead['arv']:,.2f}\n"
        f"📧 *Outreach Status:* {'Sent Successfully' if email_dispatched else 'Skipped (Check Credentials)'}\n"
        f"📄 *Contract:* Compiled in-memory ({pdf_filename})"
    )
    send_telegram_alert(alert_message)

    # 7. Secure Ephemeral Memory Purge
    memory_wiper.purge_transient_files()
    print("Pipeline execution complete. All local traces securely shredded.")

if __name__ == "__main__":
    run_pipeline()
    
