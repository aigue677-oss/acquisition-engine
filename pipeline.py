import json
import os
import time
import random
import requests
import gspread
from google.oauth2.service_account import Credentials
from valuation_engine import calculate_heuristic_arv, calculate_dynamic_mao

# Optional Playwright imports for stealth scraping
try:
    from playwright.sync_api import sync_playwright
    from playwright_stealth import stealth_sync
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Google Sheets Setup Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_gspread_client():
    """Initializes and returns the authenticated gspread client using environment JSON or local file."""
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    if creds_json:
        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    else:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
        if os.path.exists(creds_path):
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        else:
            raise FileNotFoundError("Google service account credentials not found in environment variables or file.")
    
    client = gspread.authorize(creds)
    return client

def send_telegram_alert(message: str):
    """Sends an automated notification alert via your Telegram bot."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram credentials not found. Skipping notification.")
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
        print(f"Error sending Telegram alert: {str(e)}")

def simulate_human_jitter(min_sec=3.5, max_sec=9.2):
    """Introduces randomized delays to prevent rate-limiting firewalls (HTTP 429)."""
    sleep_duration = random.uniform(min_sec, max_sec)
    print(f"[Jitter] Pausing for {sleep_duration:.2f} seconds to mimic human browsing behavior...")
    time.sleep(sleep_duration)

def fetch_target_property_data(target_url: str):
    """
    Scrapes target property records using Playwright with stealth fingerprint masking 
    and XHR network interception to bypass CAPTCHAs and data-center IP blocks.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright is not installed or available in this environment.")
        return []

    intercepted_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # Apply Playwright-Stealth fingerprint masking
        stealth_sync(page)

        def handle_response(response):
            if "api" in response.url or "json" in response.headers.get("content-type", ""):
                try:
                    data = response.json()
                    intercepted_data.append(data)
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            print(f"Navigating securely to target source: {target_url}")
            page.goto(target_url, timeout=60000)
            simulate_human_jitter(4.0, 8.5)
            page.wait_for_load_state("networkidle")
            browser.close()
            return intercepted_data

        except Exception as e:
            print(f"Error during stealth scraping execution: {str(e)}")
            browser.close()
            return []

def match_institutional_buyer(purchase_price: float, bedrooms: int = 3):
    """
    Scans the Institutional_Buyers tab in Google Sheets to find 
    the optimal cash buyer matching the property criteria.
    """
    try:
        client = get_gspread_client()
        sheet_key = os.getenv("GOOGLE_SHEET_KEY")
        
        if not sheet_key:
            return "Hedge_Fund_Alpha (Default Match)"

        spreadsheet = client.open_by_key(sheet_key)
        
        try:
            buyer_sheet = spreadsheet.worksheet("Institutional_Buyers")
            buyers = buyer_sheet.get_all_records()
        except Exception:
            print("Institutional_Buyers tab not found. Using default buyer routing.")
            return "Hedge_Fund_Alpha (Default Match)"

        best_match = "Open Market / Standard Exit"
        
        for buyer in buyers:
            max_price = float(buyer.get("Max_Purchase_Price", 999999))
            min_beds = int(buyer.get("Min_Bedrooms", 2))
            
            if purchase_price <= max_price and bedrooms >= min_beds:
                best_match = buyer.get("Buyer_ID", "Hedge_Fund_Alpha")
                break 

        return best_match

    except Exception as e:
        print(f"Error matching institutional buyer: {str(e)}")
        return "Hedge_Fund_Alpha (Default Match)"

def process_cognitive_payload(raw_data: dict):
    """
    Structures scraped information into a flat JSON format 
    ready for Google Sheets synchronization and Telegram dispatch.
    """
    structured_payload = {
        "address": raw_data.get("address", "123 Main Street, Miami FL"),
        "seller_name": raw_data.get("owner_name", "John Doe (Executor)"),
        "asking_price": raw_data.get("asking_price", 120000.0),
        "repairs": raw_data.get("repairs", 15000.0),
        "square_footage": raw_data.get("square_footage", 1500.0),
        "motivation_score": raw_data.get("motivation_score", 9),
        "core_pain_point": raw_data.get("core_pain_point", "Probate property, out-of-state heir"),
        "exit_strategy_buyer_id": "Hedge_Fund_Alpha"
    }
    return structured_payload

def process_inbound_lead(webhook_payload: dict):
    """
    Core pipeline function that processes inbound lead payloads,
    runs internal heuristic underwriting, matches buyers, syncs to Google Sheets, and fires Telegram alerts.
    """
    property_address = webhook_payload.get("address", "Unknown Address")
    seller_name = webhook_payload.get("seller_name", "Unknown Seller")
    seller_asking_price = float(webhook_payload.get("asking_price", 0.0))
    estimated_repairs = float(webhook_payload.get("repairs", 15000.0))
    square_footage = float(webhook_payload.get("square_footage", 1500.0))

    print(f"Running internal heuristic underwriting for: {property_address}")
    
    try:
        # 1. Compute underwriting metrics
        arv = calculate_heuristic_arv(square_footage)
        mao = calculate_dynamic_mao(arv, estimated_repairs)
        gross_spread = arv - estimated_repairs - seller_asking_price
        
        # 2. State Machine Decision Rule
        status = "Offer Accepted" if seller_asking_price <= mao else "Review Required"

        # 3. Match Institutional Buyer
        matched_buyer = match_institutional_buyer(seller_asking_price)

        # 4. Package row data for Google Sheets (9 columns)
        row_data = [
            property_address,
            seller_name,
            seller_asking_price,
            arv,
            estimated_repairs,
            mao,
            gross_spread,
            status,
            matched_buyer
        ]
        
        # 5. Push data to Google Sheets
        client = get_gspread_client()
        sheet_key = os.getenv("GOOGLE_SHEET_KEY")
        
        if sheet_key:
            sheet = client.open_by_key(sheet_key).sheet1
            sheet.append_row(row_data)
            print(f"Google Sheet successfully updated for: {property_address}")
        else:
            print("Warning: GOOGLE_SHEET_KEY environment variable not set. Skipping sheet sync.")

        # 6. Format and send Telegram Alert
        alert_message = (
            f"🚨 *New Real Estate Lead & Buyer Match*\n\n"
            f"📍 *Address:* {property_address}\n"
            f"👤 *Seller:* {seller_name}\n"
            f"💰 *Asking Price:* ${seller_asking_price:,.2f}\n"
            f"🏡 *Heuristic ARV:* ${arv:,.2f}\n"
            f"🛠 *Est. Repairs:* ${estimated_repairs:,.2f}\n"
            f"📊 *Calculated MAO:* ${mao:,.2f}\n"
            f"📈 *Gross Spread:* ${gross_spread:,.2f}\n"
            f"⚡ *Status:* *{status}*\n"
            f"🏛 *Matched Buyer:* `{matched_buyer}`"
        )
        send_telegram_alert(alert_message)

        print(f"Underwriting & Buyer Matching Complete. Status: {status} | Buyer: {matched_buyer}")
        return row_data

    except Exception as e:
        print(f"Error in heuristic pipeline execution: {str(e)}")
        raise e
    
