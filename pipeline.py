# ==========================================
# ENTERPRISE WHOLESALE REAL ESTATE PIPELINE 
# WITH AUTOMATED BUYER DISPATCH & MEMORY
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
# Optional: Add a dedicated Telegram Channel ID or Group ID for your Cash Buyers if separate (e.g., "@my_cash_buyers")
# If left matching TELEGRAM_CHAT_ID, it will post directly to your command feed.
BUYERS_CHANNEL_ID = os.environ.get("BUYERS_CHANNEL_ID", TELEGRAM_CHAT_ID)

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

# Distressed Real Estate Feed
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
        
        # INSTITUTIONAL MAO FORMULA: MAO = (ARV * 0.70) - Repairs
        mao = (arv * 0.70) - repairs
        potential_spread = mao - asking_price
        
        # Financial Decision Matrix
        if confidence >= 8 and asking_price <= mao and potential_spread >= 15000:
            
            # 1. Private Command Alert (Sent to You)
            admin_message = (
                f"🏠 *ACQUISITIONS: NEW TARGET SECURED* 🏠\n\n"
                f"📍 *Address:* {prop_address}\n"
                f"⚠️ *Distress:* {prop['distress_type'].upper()}\n"
                f"💵 *Asking Price:* ${asking_price:,}\n"
                f"📈 *ARV:* ${arv:,}\n"
                f"🛠️ *Repairs:* ${repairs:,}\n"
                f"🎯 *Calculated MAO:* ${mao:,.0f}\n"
                f"💰 *Wholesale Spread:* ${potential_spread:,.0f}\n"
                f"🚀 *Status:* Ready for seller outreach."
            )
            
            # 2. Public/Buyer Broadcast (Professional Deal Brief for Cash Buyers)
            buyer_message = (
                f"🚨 *OFF-MARKET WHOLESALE ASSIGNMENT* 🚨\n\n"
                f"📍 *Market/Area:* {prop_address}\n"
                f"🏷️ *Asset Class:* Single Family Residential\n"
                f"💵 *Contract Price:* ${asking_price:,}\n"
                f"📈 *Estimated ARV:* ${arv:,}\n"
                f"🛠️ *Est. Repairs:* ${repairs:,}\n"
                f"🔥 *Projected Potential Spread:* Excellent fix-and-flip or rental margins.\n"
                f"⚡ *Terms:* 14-day close, clear title, EMD secured in escrow.\n\n"
                f"_Reply 'INTERESTED' or contact acquisitions desk to review inspection reports and lock down contract terms._"
            )
            
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            # Dispatch Admin Alert
            requests.post(telegram_url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": admin_message,
                "parse_mode": "Markdown"
            })
            
            # Dispatch Buyer Network Broadcast (if a separate channel ID is specified)
            if BUYERS_CHANNEL_ID != TELEGRAM_CHAT_ID:
                requests.post(telegram_url, json={
                    "chat_id": BUYERS_CHANNEL_ID,
                    "text": buyer_message,
                    "parse_mode": "Markdown"
                })
                
            print(f"-> [DUAL DISPATCH SENT]: Admin alert & buyer broadcast queued for {prop_address}")
            
            seen_properties.append(prop_address)
            new_leads_count += 1
            
        else:
            print(f"-> [PASSED UNDERWRITING]: {prop_address} did not meet strict MAO spread criteria.")
            
        time.sleep(1.0)
    except Exception as e:
        print(f"-> Error on lead record #{index + 1}: {e}")

save_seen_assets(seen_properties)
print(f"--- REAL ESTATE WORKER CYCLE COMPLETE. New leads saved: {new_leads_count} ---")
    
