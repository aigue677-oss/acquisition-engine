import os
import json
import gspread
from google.oauth2.service_account import Credentials

# --- Configuration & Credentials Setup ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_gspread_client():
    """
    Initializes and authorizes the Google Sheets client using environment credentials.
    """
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

def ingest_global_lead(property_data):
    """
    Ingests a raw property lead from specified global markets (e.g., Dallas, Atlanta, Dubai)
    directly into the Google Sheet database with automated underwriting calculations.
    """
    client = get_gspread_client()
    if not client:
        return False

    try:
        sheet_name = property_data.get("target_sheet", "Sovereign_Grid_Leads")
        sheet = client.open(sheet_name).sheet1
        
        # Financial and Underwriting calculations
        arv = float(property_data.get("arv", 0) or 0)
        repairs = float(property_data.get("repairs", 0) or 0)
        asking_price = float(property_data.get("asking_price", 0) or 0)
        
        mao = (arv * 0.70) - repairs
        gross_spread = arv - repairs - asking_price

        # Format address to include the global market tag
        market = property_data.get("market", "General")
        raw_address = property_data.get("address", "")
        formatted_address = f"{raw_address} [{market}]"

        row_values = [
            formatted_address,
            property_data.get("owner_name", ""),
            property_data.get("owner_phone", ""),
            property_data.get("owner_email", ""),
            arv,
            repairs,
            asking_price,
            mao,
            gross_spread,
            property_data.get("transaction_structure", "All-Cash Offer"),
            property_data.get("status", "Clear Title")
        ]
        
        sheet.append_row(row_values)
        print(f"Multi-Market Ingestion Success: Lead added for {market} -> {raw_address}")
        return True
    except Exception as e:
        print(f"Failed to ingest multi-market lead into Google Sheet: {e}")
        return False

if __name__ == "__main__":
    # Test batch simulating multi-market global deal flow (Dallas & Dubai)
    global_lead_batch = [
        {
            "market": "Dallas, TX",
            "address": "789 Horizon Blvd, Dallas, TX",
            "owner_name": "Texas Seller Example",
            "owner_phone": "+15550191122",
            "owner_email": "liamharford26@gmail.com",
            "arv": 450000.0,
            "repairs": 30000.0,
            "asking_price": 260000.0,
            "transaction_structure": "Standard Cash Assignment",
            "status": "Clear Title"
        },
        {
            "market": "Dubai, UAE",
            "address": "Marina Gate Tower 2, Dubai",
            "owner_name": "International Investor Example",
            "owner_phone": "+971501234567",
            "owner_email": "liamharford26@gmail.com",
            "arv": 1200000.0,
            "repairs": 50000.0,
            "asking_price": 850000.0,
            "transaction_structure": "Direct Cash Purchase",
            "status": "Clear Title"
        }
    ]
    
    print("Initializing Multi-Market Global Ingestion Hub...")
    for lead in global_lead_batch:
        ingest_global_lead(lead)
        
