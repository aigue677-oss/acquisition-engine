# ==========================================
# ENTERPRISE CLOUD PIPELINE: pipeline.py
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
You are an elite Digital Asset & Domain Arbitrage Director specializing in undervalued web properties and domain portfolios. 
Extract the following fields precisely into a valid JSON object:
- asset_name (string or null - e.g., domain name or project title)
- estimated_discount_percentage (float or null - calculate discount based on asking price vs market valuation)
- asset_type ("domain", "saas", "content_site", "newsletter", or "unknown")
- confidence_score (integer 1-10)

Output ONLY raw JSON. No markdown code blocks, no conversational text.
"""

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

digital_asset_feed = [
    """PREMIUM DOMAIN FLIP: CloudAI.io. Asking price $4,500. Comparable institutional sales and market valuation estimated at $22,000. Clean history.""",
    """Incomplete listing: Missing asset name, asking $500 for an unknown digital project.""",
    """MICRO-SAAS ACQUISITION: InvoiceAutomate.com. Generating $1,200 MRR. Asking price $18,000 (15x multiple). True market valuation $36,000.""",
]

print(f"--- CLOUD WORKER INITIATED: SCANNING {len(digital_asset_feed)} FEEDS ---")

for index, raw_text in enumerate(digital_asset_feed):
    try:
        response_ai = client.models.generate_content(
            model='gemini-3.5-flash-lite', 
            contents=f"{elite_system_prompt}\n\nDATA TO PARSE:\n{raw_text}"
        )
        
        cleaned_text = response_ai.text.strip().replace("```json", "").replace("```", "")
        asset = json.loads(cleaned_text)
        
        if not asset.get("asset_name"):
            continue
            
        discount = asset.get("estimated_discount_percentage") or 0.0
        confidence = asset.get("confidence_score") or 0
        
        if discount >= 40.0 and confidence >= 8:
            message_text = (
                f"💎 *CLOUD AUTONOMOUS ALERT* 💎\n\n"
                f"🌐 *Asset:* {asset['asset_name']}\n"
                f"🏷️ *Type:* {asset['asset_type'].upper()}\n"
                f"💰 *Discount Spread:* {asset['estimated_discount_percentage']}%\n"
                f"⭐ *Confidence Score:* {asset['confidence_score']}/10\n"
                f"🚀 *Status:* ARBITRAGE TARGET ACQUIRED"
            )
            
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message_text,
                "parse_mode": "Markdown"
            }
            
            requests.post(telegram_url, json=payload)
            print(f"-> [CLOUD DISPATCH SENT]: Successfully alerted for {asset['asset_name']}")
            
        time.sleep(1.0)
    except Exception as e:
        print(f"-> Error on record #{index + 1}: {e}")

print("--- CLOUD WORKER CYCLE COMPLETE ---")
      
