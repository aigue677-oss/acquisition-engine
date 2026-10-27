def log_to_google_sheets(lead_data):
    if not GCP_SA_KEY:
        print("Error: GCP_SA_KEY secret not found.")
        return

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        creds_dict = json.loads(GCP_SA_KEY)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        # Attempt to open and print confirmation
        sheet = client.open("Wholesale Acquisitions Master Pipeline").sheet1
        print("Successfully connected to Google Sheets spreadsheet object.")

        row = [
            lead_data.get("address"),
            lead_data.get("owner", "Institutional Trust"),
            lead_data.get("phone", "+1 (555) 000-0000"),
            lead_data.get("method", "SIMULTANEOUS DOUBLE-CLOSE (A-B-C)"),
            lead_data.get("asking_price", "$65,000"),
            lead_data.get("mao", "$127,000"),
            lead_data.get("net_payout", "$60,500"),
            lead_data.get("status", "Clear Title")
        ]
        
        sheet.append_row(row)
        print(f"Successfully appended row for {lead_data.get('address')}!")
    except Exception as e:
        print(f"CRITICAL GOOGLE SHEETS ERROR: {str(e)}")
        
