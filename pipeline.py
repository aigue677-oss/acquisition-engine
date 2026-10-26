# ==========================================
# ENTERPRISE REAL ESTATE WHOLESALE PIPELINE
# ==========================================

import os
import json
import time
import requests
from google import genai

# 1. Initialize client using Secure Cloud Environment Variables
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not found!")

client = genai.Client(api_key=api_key)

real_estate_system_prompt = """
You are an elite Real Estate Acquisitions Director and Institutional Underwriter specializing in off-market distressed properties and wholesaling.
Extract the following fields precisely into a valid JSON object:
- property_address (string or null - e.g., street address and city)
- distress_type ("foreclosure", "tax_delinquent", "probate", "code_violation", or "vacant")
- asking_price (integer or null - what the seller is asking for)
- estimated_arv (integer or null - After Repair Value based on comparable market sales)
- estimated_repairs (integer or null - estimated rehab/repair costs)
- confidence_score (integer 1-10)

Output ONLY raw JSON. No markdown code blocks, no conversational text.
"""

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 2. STATE MANAGEMENT: Load deduplication memory ledger
STATE_FILE = "seen_assets.json"

def load_seen_assets():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_seen_assets(seen_list):
    with open(STATE_FILE, "w") as f:
        json.dump(seen_list, f, indent=2)

seen_properties = load_seen_assets()
print(f"--- MEMORY LOADED: {len(seen_properties)} unique properties tracked in ledger ---")

# Simulated Distressed Real Estate Feed (In production, connect county scrapers or off-market RSS)
real_estate_feed = [
    """DISTRESSED OFF-MARKET LEAD: 742 Evergreen Terrace, Springfield. Pre-foreclosure notice filed. Owner facing auction. Asking price: $120,000. ARV comp sales in neighborhood: $280,000. Estimated cosmetic and roof repairs: $35,000. Motivated seller wants fast cash.""",
    """RETAIL PRICED HOME: 123 Main Street. Move-in ready. Asking $250,000. ARV $260,000. No distress indicators.""",
    """TAX DELINQUENT PROBATE: 884 Oak Lane, Shelbyville. Inherited property, out-of-state heirs. Tax lien of $14,000. Asking price / debt payoff: $65,000. ARV: $190,000. Full gut rehab required: $45,000.""",
]

print(f"--- CLOUD REAL ESTATE WORKER: SCANNING {len(real_estate_feed)} LEADS ---")

new_leads_count = 0

for index, raw_text in enumerate(real_estate_feed):
    try:
        response_ai = client.models.generate_content(
            model='gemini-3.5-flash-lite', 
            contents=f"{real_estate_system_prompt}\n\nDATA TO PARSE:\n{raw_text}"
        )
        
        cleaned_text = response_ai.text.strip().replace("```json", "").replace("```", "")
        prop = json.loads(cleaned_text)
        
        prop_address = prop.get("property_address")
        if not prop_address:
            continue
            
        # DEDUPLICATION CHECK
        if prop_address in seen_properties:
            print(f"-> [DUPLICATE SKIPPED]: '{prop_address}' already exists in memory ledger.")
            continue
            
        asking_price = prop.get("asking_price") or 0
        arv = prop.get("estimated_arv") or 0
        repairs = prop.get("estimated_repairs") or 0
        confidence = prop.get("confidence_score") or 0
        
        # INSTITUTIONAL MAO (Maximum Allowable Offer) FORMULA
        # MAO = (ARV * 0.70) - Repairs
        mao = (arv * 0.70) - repairs
        potential_spread = mao - asking_price  # If asking price is below MAO, this is your wholesale assignment buffer/profit
        
        # Financial Decision Matrix: Require high confidence, positive wholesale spread, and distress motivation
        if confidence >= 8 and asking_price <= mao and potential_spread >= 15000:
            message_text = (
                f"🏠 *WHOLESALE REAL ESTATE ALERT* 🏠\n\n"
                f"📍 *Address:* {prop_address}\n"
                f"⚠️ *Distress Type:* {prop['distress_type'].upper()}\n"
                f"💵 *Asking Price:* ${asking_price:,}\n"
                f"📈 *ARV (Market Value):* ${arv:,}\n"
                f"🛠️ *Est. Repairs:* ${repairs:,}\n"
                f"🎯 *Calculated MAO:* ${mao:,.0f}\n"
                f"💰 *Est. Wholesale Spread:* ${potential_spread:,.0f}\n"
                f"🚀 *Status:* CONTRACT UNDERWRITTEN & DISPATCHED"
            )
            
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message_text,
                "parse_mode": "Markdown"
            }
            
            requests.post(telegram_url, json=payload)
            print(f"-> [DISPATCH SENT]: Wholesale lead secured for {prop_address}")
            
            seen_properties.append(prop_address)
            new_leads_count += 1
            
        else:
            print(f"-> [PASSED UNDERWRITING]: {prop_address} did not meet strict MAO spread criteria.")
            
        time.sleep(1.0)
    except Exception as e:
        print(f"-> Error on lead record #{index + 1}: {e}")

save_seen_assets(seen_properties)
print(f"--- REAL ESTATE WORKER CYCLE COMPLETE. New leads saved: {new_leads_count} ---")

