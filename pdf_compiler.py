from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class PDFCompiler:
    def generate_contract(self, owner_name, property_address, mao, filename="Sovereign_Agreement.pdf"):
        """
        Generates a formal institutional real estate purchase agreement PDF.
        """
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawString(54, height - 54, "SOVEREIGN GRID — PURCHASE & SALE AGREEMENT")
        
        # Metadata / Property Info
        c.setFont("Helvetica", 12)
        c.drawString(54, height - 100, f"Property Address: {property_address}")
        c.drawString(54, height - 125, f"Seller / Owner: {owner_name}")
        c.drawString(54, height - 150, f"Official Cash Offer (MAO): ${mao:,.2f}")
        
        # Contract Terms
        c.setFont("Helvetica-Bold", 14)
        c.drawString(54, height - 200, "Terms and Conditions:")
        
        c.setFont("Helvetica", 11)
        terms = [
            "1. Buyer agrees to purchase the property for the verified Maximum Allowable Offer (MAO) stated above.",
            "2. This transaction is an all-cash offer with zero financial contingencies.",
            "3. Closing shall occur within 14 business days upon clear title verification.",
            "4. Earnest money deposit (EMD) of $1,000 shall be deposited within 48 hours of execution."
        ]
        
        y_offset = 230
        for term in terms:
            c.drawString(54, height - y_offset, term)
            y_offset += 25
            
        # Signatures section
        c.drawString(54, height - 380, "Buyer Signature: ___________________________      Date: _________")
        c.drawString(54, height - 430, "Seller Signature: ___________________________      Date: _________")
        
        c.showPage()
        c.save()
        return filename
        
