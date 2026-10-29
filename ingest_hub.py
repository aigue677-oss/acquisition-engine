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

def ingest_lead(property_data):
    """
    Ingests a raw property lead from global markets directly into the Google Sheet database.
    Aligned precisely with your 11-column schema headers:
    [Property Address, Owner Name, Owner Phone, Owner Email, ARV, Repairs, Asking Price, MAO, Gross spread, Transaction Structure, Status]
    """
    client = get_gspread_client()
    if not client:
        return False

    try:
        sheet = client.open("Sovereign_Grid_Leads").sheet1
        
        # Calculate MAO and Gross spread automatically on ingestion if desired
        arv = property_data.get("arv", 0)
        repairs = property_data.get("repairs", 0)
        asking_price = property_data.get("asking_price", 0)
        
        mao = (arv * 0.70) - repairs
        gross_spread = arv - repairs - asking_price

        row_values = [
            property_data.get("address", ""),
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
        print(f"Global Ingestion Success: Lead added for {property_data.get('address')}")
        return True
    except Exception as e:
        print(f"Failed to ingest lead into Google Sheet: {e}")
        return False

if __name__ == "__main__":
    # Test payload simulating a live market lead matching your full sheet schema
    sample_global_lead = {
        "address": "456 Expansion Ave, Dallas, TX",
        "owner_name": "Global Seller Test",
        "owner_phone": "+15550198765",
        "owner_email": "liamharford26@gmail.com",
        "arv": 320000.0,
        "repairs": 25000.0,
        "asking_price": 180000.0,
        "transaction_structure": "Standard Cash Assignment",
        "status": "Clear Title"
    }
    
    print("Testing Global Ingestion Hub with Full Schema...")
    ingest_lead(sample_global_lead)
