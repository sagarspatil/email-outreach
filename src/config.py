"""
Configuration settings for email automation
"""

import os
from datetime import time


class Config:
    def __init__(self):
        # Email settings
        self.sender_email = os.getenv('SENDER_EMAIL', 'advayaholistic@gmail.com')
        self.gmail_app_password = os.getenv('GMAIL_APP_PASSWORD', '')
        
        # CSV file
        csv_filename = os.getenv('CSV_FILE', 'final.csv')
        self.csv_file = os.path.join('..', 'data', csv_filename)
        
        # Time intervals (in days from initial email)
        self.followup1_days = int(os.getenv('FOLLOWUP1_DAYS', '3'))  # 3 days from initial
        self.followup2_days = int(os.getenv('FOLLOWUP2_DAYS', '5'))  # 5 days from initial
        self.followup3_days = int(os.getenv('FOLLOWUP3_DAYS', '7'))  # 7 days from initial
        
        # Send limits
        self.daily_send_limit = int(os.getenv('DAILY_SEND_LIMIT', '500'))
        
        # Email sending delays (in seconds)
        self.email_delay_seconds = int(os.getenv('EMAIL_DELAY_SECONDS', '60'))  # 1 minute between emails
        
        # Send time window
        self.send_start_hour = int(os.getenv('SEND_START_HOUR', '9'))
        self.send_end_hour = int(os.getenv('SEND_END_HOUR', '17'))
        
        # Validate
        self._validate()
        
    def _validate(self):
        """Validate configuration"""
        if not self.gmail_app_password:
            raise ValueError("GMAIL_APP_PASSWORD environment variable is required")
            
        if self.send_start_hour >= self.send_end_hour:
            raise ValueError("Send start hour must be before end hour")
            
        if self.followup1_days < 1 or self.followup2_days < 1 or self.followup3_days < 1:
            raise ValueError("Follow-up intervals must be at least 1 day")
            
    def is_within_send_window(self):
        """Check if current time is within send window"""
        from datetime import datetime
        current_hour = datetime.now().hour
        return self.send_start_hour <= current_hour < self.send_end_hour