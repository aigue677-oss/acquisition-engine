# ==========================================
# ENTERPRISE CLOUD PIPELINE WITH MEMORY LAYER
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

elite_system_prompt = """
You are an elite Digital Asset & Domain Arbitrage Director specializing in undervalued web properties and digital products. 
Extract the following fields precisely into a valid JSON object:
- asset_name (string or null - e.g., domain name or product title)
- estimated_discount_percentage (float or null - calculate discount based on asking price vs market valuation)
- asset_type ("domain", "saas", "content_site", "digital_product", or "unknown")
- confidence_score (integer 1-10)

Output ONLY raw JSON. No markdown code blocks, no conversational text.
"""

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 2. STATE MANAGEMENT: Load previously seen assets from local ledger
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

seen_assets = load_seen_assets()
print(f"--- MEMORY LOADED: {len(seen_assets)} unique assets tracked in ledger ---")

# Simulated Live Feed (Including digital products and domains)
digital_asset_feed = [
    """PREMIUM DOMAIN FLIP: CloudAI.io. Asking price $4,500. Comparable institutional sales and market valuation estimated at $22,000. Clean history.""",
    """EVERGREEN DIGITAL PRODUCT BUNDLE: AI Automation Mastery Kit. Asking price $99. Value $499. High demand commercial license included.""",
    """MICRO-SAAS ACQUISITION: InvoiceAutomate.com. Generating $1,200 MRR. Asking price $18,000 (15x multiple). True market valuation $36,000.""",
]

print(f"--- CLOUD WORKER INITIATED: SCANNING {len(digital_asset_feed)} FEEDS ---")

new_discoveries_count = 0

for index, raw_text in enumerate(digital_asset_feed):
    try:
        response_ai = client.models.generate_content(
            model='gemini-3.5-flash-lite', 
            contents=f"{elite_system_prompt}\n\nDATA TO PARSE:\n{raw_text}"
        )
        
        cleaned_text = response_ai.text.strip().replace("```json", "").replace("```", "")
        asset = json.loads(cleaned_text)
        
        asset_name = asset.get("asset_name")
        if not asset_name:
            continue
            
        # DEDUPLICATION CHECK: Have we already processed this exact asset?
        if asset_name in seen_assets:
            print(f"-> [DUPLICATE SKIPPED]: '{asset_name}' already exists in memory ledger.")
            continue
            
        discount = asset.get("estimated_discount_percentage") or 0.0
        confidence = asset.get("confidence_score") or 0
        
        # Investment Decision Matrix (Catching high-discount domains, saas, or digital products)
        if discount >= 40.0 and confidence >= 8:
            message_text = (
                f"💎 *NEW ARBITRAGE TARGET ACQUIRED* 💎\n\n"
                f"🌐 *Asset:* {asset_name}\n"
                f"🏷️ *Type:* {asset['asset_type'].upper()}\n"
                f"💰 *Discount Spread:* {discount}%\n"
                f"⭐ *Confidence Score:* {confidence}/10\n"
                f"🚀 *Status:* DEDUPLICATED & DISPATCHED"
            )
            
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message_text,
                "parse_mode": "Markdown"
            }
            
            requests.post(telegram_url, json=payload)
            print(f"-> [DISPATCH SENT & MEMORY UPDATED]: New target '{asset_name}' secured.")
            
            # Add to memory ledger and flag for commit
            seen_assets.append(asset_name)
            new_discoveries_count += 1
            
        time.sleep(1.0)
    except Exception as e:
        print(f"-> Error on record #{index + 1}: {e}")

# Save updated ledger back to disk
save_seen_assets(seen_assets)
print(f"--- CLOUD WORKER CYCLE COMPLETE. New items saved: {new_discoveries_count} ---")

