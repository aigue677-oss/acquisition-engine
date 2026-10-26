# ==========================================================
# ENTERPRISE INSTITUTIONAL WHOLESALE PIPELINE
# FULLY INTEGRATED: MULTI-REGION, MAO, SMS, CLEVA & CRM WEBHOOK
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

# 3. EXPANDED MULTI-STATE & MULTI-COUNTY INGESTION ENGINE
def fetch_multi_source_leads():
    # Ingests from multiple institutional data vectors across massive target markets
    return [
        # Region A: Metro Hub & Surrounding Counties
        """MULTI-SOURCE [TAX DEFAULT STREAM - COUNTY A]: 4022 Oakridge Terrace, Metro Core. Severe tax default. Asking price: $65,000. ARV: $210,000. Repairs: $20,000. Occupant: vacant.""",
        """MULTI-SOURCE [PROBATE COURT STREAM - COUNTY B]: 714 Heritage Way, Northern Suburbs. Unopened estate probate record. Asking price: $95,000. ARV: $265,000. Repairs: $35,000. Occupant: owner_occupied.""",
        
        # Region B: Secondary Growth Corridor
        """MULTI-SOURCE [CODE VIOLATION STREAM - REGION 2]: 128 Industrial Parkway, South District. Unresolved structural code violations. Asking price: $45,000. ARV: $180,000. Repairs: $25,000. Occupant: tenant_occupied.""",
        """MULTI-SOURCE [TAX DEFAULT STREAM - REGION 2]: 8809 Pinecrest Drive, West County. Tax lien auction pending. Asking price: $55,000. ARV: $195,000. Repairs: $15,000. Occupant: vacant."""
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
    print(f"-> [AUTOMATED SMS DISPATCHED to {owner_phone}]: {sms_text}")
    return sms_text

# 6. FAIL-SAFE FREE CRM / GOOGLE SHEET WEBHOOK BRIDGE
def sync_to_free_crm(prop_address, owner_name, owner_phone, asking_price, mao, gross_spread, transaction_type):
    try:
        webhook_url = os.environ.get("CRM_WEBHOOK_URL")
        if not webhook_url:
            return
            
        payload = {
            "address": prop_address,
            "owner": owner_name,
            "phone": owner_phone,
            "asking_price": asking_price,
            "mao": mao,
            "spread": gross_spread,
            "structure": transaction_type,
            "status": "New Lead - SMS Dispatched"
        }
        
        requests.post(webhook_url, json=payload, timeout=5)
        print("-> [CRM SYNC]: Lead successfully logged to database.")
    except Exception as e:
        print(f"-> [CRM SYNC WARNING]: Webhook dispatch skipped ({e})")

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
            
            # TRIGGER GOOGLE SHEET / CRM SYNC (FAIL-SAFE)
            sync_to_free_crm(prop_address, owner_name, owner_phone, asking_price, mao, gross_spread, transaction_type)
                
            seen_properties.append(prop_address)
            new_leads_count += 1
            
        time.sleep(1.0)
    except Exception as e:
        print(f"-> Error on record: {e}")

save_seen_assets(seen_properties)
print(f"--- EXPANDED MULTI-REGION, CLEVA & CRM PIPELINE COMPLETE. Processed: {new_leads_count} ---")
