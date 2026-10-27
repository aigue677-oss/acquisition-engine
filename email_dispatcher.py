import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailDispatcher:
    """
    Handles secure outbound SMTP transmission of institutional acquisition 
    offers with stealth headers and environment-injected credentials.
    """
    def __init__(self):
        # Pulls email configuration securely from GitHub Secrets / environment
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", 587))
        self.sender_email = os.environ.get("SENDER_EMAIL", "")
        self.sender_password = os.environ.get("SENDER_PASSWORD", "")

    def send_offer(self, recipient_email: str, subject: str, body_text: str) -> bool:
        """
        Dispatches a secure HTML/Text plaintext email to the property seller.
        """
        if not self.sender_email or not self.sender_password:
            print("Email dispatch skipped: Missing SMTP credentials in environment variables.")
            return False

        try:
            # Construct message envelope
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Attach body content
            msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

            # Establish secure TLS connection and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())

            print(f"Acquisition offer dispatched successfully to: {recipient_email}")
            return True

        except Exception as e:
            print(f"Failed to dispatch email to {recipient_email}: {e}")
            return False

if __name__ == "__main__":
    # Test execution layout
    dispatcher = EmailDispatcher()
    print("EmailDispatcher module loaded successfully in secure mode.")
              
