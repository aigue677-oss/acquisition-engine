import os
import gspread
from google.oauth2.service_account import Credentials
from valuation_engine import calculate_heuristic_arv, calculate_dynamic_mao

# Google Sheets Setup Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_gspread_client():
    """Initializes and returns the authenticated gspread client using environment credentials."""
    # If credentials are stored via a service account JSON file or env variable
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    else:
        # Fallback handling if configured via environment JSON string
        raise FileNotFoundError("Google service account credentials file not found.")
    
    client = gspread.authorize(creds)
    return client

def process_inbound_lead(webhook_payload: dict):
    """
    Core pipeline function that processes inbound lead webhooks,
    runs internal heuristic underwriting, and syncs directly to Google Sheets.
    """
    # 1. Extract lead parameters from incoming webhook payload
    property_address = webhook_payload.get("address", "Unknown Address")
    seller_name = webhook_payload.get("seller_name", "Unknown Seller")
    seller_asking_price = float(webhook_payload.get("asking_price", 0.0))
    estimated_repairs = float(webhook_payload.get("repairs", 15000.0)) # Default baseline repair cost
    square_footage = float(webhook_payload.get("square_footage", 1500.0)) # Default baseline sqft

    print(f"Running internal heuristic underwriting for: {property_address}")
    
    try:
        # 2. Compute internal heuristic ARV and institutional MAO
        arv = calculate_heuristic_arv(square_footage)
        mao = calculate_dynamic_mao(arv, estimated_repairs)
        gross_spread = arv - estimated_repairs - seller_asking_price
        
        # 3. Automated State Machine Decision Rule
        status = "Offer Accepted" if seller_asking_price <= mao else "Review Required"

        # 4. Package row data for Google Sheets sync matching your structural layout
        row_data = [
            property_address,
            seller_name,
            seller_asking_price,
            arv,
            estimated_repairs,
            mao,
            gross_spread,
            status
        ]
        
        # 5. Push data to Google Sheets state machine
        client = get_gspread_client()
        sheet_key = os.getenv("GOOGLE_SHEET_KEY")
        
        if sheet_key:
            sheet = client.open_by_key(sheet_key).sheet1
            sheet.append_row(row_data)
            print(f"Google Sheet successfully updated for: {property_address}")
        else:
            print("Warning: GOOGLE_SHEET_KEY environment variable not set. Skipping sheet sync.")

        print(f"Underwriting Complete. Heuristic ARV: ${arv:,.2f} | MAO: ${mao:,.2f} | Status: {status}")
        return row_data

    except Exception as e:
        print(f"Error in heuristic pipeline execution: {str(e)}")
        raise e
    
