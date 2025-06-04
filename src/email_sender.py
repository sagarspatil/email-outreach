"""
Email sending functionality using Gmail SMTP
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import ssl

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, sender_email, app_password):
        self.sender_email = sender_email
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
    def send_email(self, recipient_email, subject, html_content, text_content=None, retry_count=3):
        """Send email with both HTML and text versions"""
        for attempt in range(retry_count):
            try:
                # Create message
                message = MIMEMultipart('alternative')
                message['Subject'] = subject
                message['From'] = self.sender_email
                message['To'] = recipient_email
                
                # Attach text content first (fallback)
                if text_content:
                    text_part = MIMEText(text_content, 'plain')
                    message.attach(text_part)
                
                # Attach HTML content
                html_part = MIMEText(html_content, 'html')
                message.attach(html_part)
                
                # Create secure SSL context
                context = ssl.create_default_context()
                
                # Send email
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.sender_email, self.app_password)
                    server.send_message(message)
                    
                logger.info(f"Email sent successfully to {recipient_email}")
                return True
                
            except smtplib.SMTPAuthenticationError:
                logger.error("Gmail authentication failed. Check app password.")
                raise
                
            except smtplib.SMTPRecipientsRefused:
                logger.error(f"Invalid recipient email: {recipient_email}")
                return False
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to send email to {recipient_email} after {retry_count} attempts")
                    return False
                    
        return False
        
    def validate_email(self, email):
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None