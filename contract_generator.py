import os
from docx import Document

def generate_purchase_agreement(lead_data, output_filename="Generated_PSA.docx"):
    """
    Dynamically populates a Real Estate Purchase and Sale Agreement (PSA) 
    using verified underwritten lead parameters.
    """
    try:
        # Initialize a document (or load an existing template document path if available)
        doc = Document()
        
        # Document Header
        doc.add_heading("PURCHASE AND SALE AGREEMENT", level=1)
        doc.add_paragraph("This Agreement is entered into by and between the Buyer and Seller detailed below.\n")
        
        # Key Deal Terms Table
        table = doc.add_table(rows=1, cols=2)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Deal Parameter"
        hdr_cells[1].text = "Contract Specification"
        
        deal_records = [
            ("Property Address", lead_data.get("address", "N/A")),
            ("Seller Name", lead_data.get("seller_name", "N/A")),
            ("Agreed Purchase Price", f"${float(lead_data.get('asking_price', 0)):,.2f}"),
            ("Estimated Repairs", f"${float(lead_data.get('repairs', 0)):,.2f}"),
            ("Calculated MAO", f"${float(lead_data.get('calculated_mao', 0)):,.2f}"),
            ("Closing Terms", "Standard Cash Offer / As-Is Condition")
        ]
        
        for param, value in deal_records:
            row_cells = table.add_row().cells
            row_cells[0].text = param
            row_cells[1].text = value
            
        doc.add_paragraph("\n")
        doc.add_paragraph("Terms & Conditions: Buyer agrees to purchase the property in its current 'as-is' physical condition. Closing shall occur within 14 to 21 days of contract execution through a designated title company.")
        
        # Signature Block Section
        doc.add_paragraph("\n\n_________________________________________\nSeller Signature & Date")
        doc.add_paragraph("\n_________________________________________\nBuyer Signature & Date")
        
        # Save file locally
        os.makedirs("generated_contracts", exist_ok=True)
        file_path = os.path.join("generated_contracts", output_filename)
        doc.save(file_path)
        
        print(f"[+] Purchase Agreement successfully compiled: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"[ERROR] Failed to generate contract document: {str(e)}")
        return None

if __name__ == "__main__":
    # Test execution payload simulation
    sample_lead = {
        "address": "789 Palm Tree Lane, Orlando FL",
        "seller_name": "Marcus Vance",
        "asking_price": 165000.0,
        "repairs": 15000.0,
        "calculated_mao": 114500.0
    }
    generate_purchase_agreement(sample_lead)
      
