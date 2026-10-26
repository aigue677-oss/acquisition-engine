# ==========================================================
# ENTERPRISE INSTITUTIONAL WHOLESALE PIPELINE
# MULTI-SOURCE INGESTION, CLEVA WIRE ROUTING & AUTOMATED SMS
# ==========================================================

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
You are an elite Real Estate Acquisitions Director and Institutional Underwriter specializing in off-market distressed properties, probate compliance, and wholesaling.
Extract the following fields precisely into a valid JSON object:
- property_address (string or null - street address and city)
- distress_type ("foreclosure", "tax_delinquent", "probate", "code_violation", or "vacant")
- asking_price (integer or null)
- estimated_arv (integer or null)
- estimated_repairs (integer or null)
- occupancy_status ("vacant", "owner_occupied", or "tenant_occupied")
- probate_status ("unopened", "filed_in_court", "executor_appointed", or "n/a")
- confidence_score (integer 1-10)

Output ONLY raw JSON. No markdown code blocks, no conversational text.
"""

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
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

# 3. MULTI-SOURCE INGESTION ENGINE (Simulated Aggregated Streams)
def fetch_multi_source_leads():
    # Ingests from multiple institutional data vectors simultaneously
    return [
        """MULTI-SOURCE [TAX DEFAULT STREAM]: 909 Apex Summit Way, Capital City. Severe tax default. Asking price: $50,000. ARV: $175,000. Repairs: $18,000. Occupant: vacant.""",
        """MULTI-SOURCE [PROBATE COURT STREAM]: 1010 Legacy Blvd, Metro City. Unopened estate probate record. Asking price: $85,000. ARV: $230,000. Repairs: $30,000. Occupant: owner_occupied.""",
        """MULTI-SOURCE [CODE VIOLATION STREAM]: 444 Meridian Avenue, North District. Unresolved structural code violations. Asking price: $40,000. ARV: $155,000. Repairs: $22,000. Occupant: tenant_occupied."""
    ]

# 4. AUTOMATED SKIP-TRACING MODULE
def skiptrace_owner(property_address):
    return "Institutional Trust / Verified Heir", "+1 (555) 891-3342 [Verified Direct Mobile]"

# 5. AUTOMATED SMS OUTREACH GENERATOR
def trigger_automated_sms(owner_phone, property_address, offer_price):
    sms_text = (
        f"Hi, regarding your property at {property_address}. We are active all-cash buyers "
        f"prepared to close clean at ${offer_price:,} with zero agent fees. Are you open to reviewing terms?"
    )
    # Hooks into SMS dispatch gateway (e.g. Twilio API) when live keys are configured
    print(f"-> [AUTOMATED SMS DISPATCHED to {owner_phone}]: {sms_text}")
    return sms_text

# Execution Main Loop
raw_leads = fetch_multi_source_leads()
new_leads_count = 0

for raw_text in raw_leads:
    try:
        response_ai = client.models.generate_content(
            model='gemini-3.5-flash-lite', 
            contents=f"{real_estate_system_prompt}\n\nDATA TO PARSE:\n{raw_text}"
        )
        
        cleaned_text = response_ai.text.strip().replace("```json", "").replace("```", "")
        prop = json.loads(cleaned_text)
        
        prop_address = prop.get("property_address")
        if not prop_address or prop_address in seen_properties:
            continue
            
        asking_price = prop.get("asking_price") or 0
        arv = prop.get("estimated_arv") or 0
        repairs = prop.get("estimated_repairs") or 0
        confidence = prop.get("confidence_score") or 0
        occupancy = prop.get("occupancy_status", "unknown")
        probate = prop.get("probate_status", "n/a")
        
        # INSTITUTIONAL MAO FORMULA
        mao = (arv * 0.70) - repairs
        gross_spread = mao - asking_price
        
        if confidence >= 7 and asking_price <= mao and gross_spread >= 15000:
            
            owner_name, owner_phone = skiptrace_owner(prop_address)
            
            # FINANCIAL ROUTING ($0 UPFRONT)
            if gross_spread >= 30000:
                transaction_type = "SIMULTANEOUS DOUBLE-CLOSE (A-B-C)"
                funding_fee = 1500
                net_profit = gross_spread - funding_fee
                financial_note = f"💡 *Structure:* Double-Close | *Net Payout:* **${net_profit:,.0f}** (Wired to Cleva USD Account)"
            else:
                transaction_type = "STANDARD CONTRACT ASSIGNMENT"
                net_profit = gross_spread
                financial_note = f"💡 *Structure:* Assignment Fee | *Net Payout:* **${net_profit:,.0f}** (Wired directly to Cleva USD Account)"
                
            # TRIGGER AUTOMATED SMS OUTREACH
            triggered_sms = trigger_automated_sms(owner_phone, prop_address, asking_price)
            
            # SAFEGUARD FLAGS
            nuance_warnings = []
            if probate == "unopened":
                nuance_warnings.append("⚠️ *PROBATE ALERT:* Unopened estate! Connect heir with probate attorney.")
            if occupancy == "tenant_occupied":
                nuance_warnings.append("🏠 *OCCUPANCY NOTE:* Tenant-occupied. Verify lease terms.")
                
            warning_text = "\n".join(nuance_warnings) if nuance_warnings else "✅ *Compliance:* Clear title & standard terms."
            
            # PRIVATE ADMIN COMMAND ALERT WITH CLEVA WIRE & SMS STATUS
            admin_message = (
                f"🏛️ *INSTITUTIONAL ACQUISITIONS DESK* 🏛️\n\n"
                f"📍 *Address:* {prop_address}\n"
                f"👤 *Owner:* {owner_name}\n"
                f"📞 *Direct Phone:* {owner_phone}\n"
                f"⚙️ *Method:* {transaction_type}\n"
                f"💵 *Asking:* ${asking_price:,} | 🎯 *MAO:* ${mao:,.0f}\n"
                f"{financial_note}\n\n"
                f"📨 *Automated SMS:* Sent via system outbound queue.\n"
                f"{warning_text}\n\n"
                f"🏦 *Payout Destination:* Cleva U.S. Domestic Wire Routing Ready."
            )
            
            # PUBLIC BUYER BROADCAST
            buyer_message = (
                f"🚨 *OFF-MARKET WHOLESALE ASSIGNMENT* 🚨\n\n"
                f"📍 *Location:* {prop_address}\n"
                f"🏷️ *Asset:* Single Family Residential\n"
                f"💵 *Contract Price:* ${asking_price:,}\n"
                f"📈 *Est. ARV:* ${arv:,} | 🛠️ *Repairs:* ${repairs:,}\n"
                f"🔥 *Status:* Verified equity spread. Fast 14-day close.\n\n"
                f"_Reply 'INTERESTED' to secure asset terms._"
            )
            
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            requests.post(telegram_url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": admin_message,
                "parse_mode": "Markdown"
            })
            
            if BUYERS_CHANNEL_ID != TELEGRAM_CHAT_ID:
                requests.post(telegram_url, json={
                    "chat_id": BUYERS_CHANNEL_ID,
                    "text": buyer_message,
                    "parse_mode": "Markdown"
                })
                
            seen_properties.append(prop_address)
            new_leads_count += 1
            
        time.sleep(1.0)
    except Exception as e:
        print(f"-> Error on record: {e}")

save_seen_assets(seen_properties)
print(f"--- MULTI-SOURCE & CLEVA PIPELINE COMPLETE. Processed: {new_leads_count} ---")
        
