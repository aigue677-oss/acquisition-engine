import requests
import json
import time

# Your live Render production webhook endpoint
WEBHOOK_URL = "https://acquisition-engine-61om.onrender.com/webhook"

def send_lead_to_engine(lead_data):
    """
    Sends a structured property lead payload to the live acquisition engine webhook.
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"[*] Dispatching lead for: {lead_data.get('property_address')}...")
        response = requests.post(WEBHOOK_URL, json=lead_data, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print("[+] Success! Lead processed, underwrote, matched, and dispatched.")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"[-] Error: Server responded with status {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"[!] Connection error failed to reach acquisition engine: {e}")

if __name__ == "__main__":
    # Example: A sample real-world distressed property lead ready for live ingestion
    sample_distressed_lead = {
        "property_address": "1042 Palm Terrace",
        "city": "Miami",
        "region_state": "FL",
        "country": "USA",
        "owner_name": "Robert Taylor",
        "owner_phone": "555-9822",
        "owner_email": "rtaylor@example.com",
        "asking_price": 165000.0,
        "repairs": 18000.0,
        "square_footage": 1650.0,
        "bedrooms": 3,
        "property_type": "Single Family",
        "zip_code": "33139"
    }

    # Dispatch the lead
    send_lead_to_energy = send_lead_to_engine(sample_distressed_lead)
    
