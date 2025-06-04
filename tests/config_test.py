"""
Test configuration for email automation with minutes instead of days
"""

import os
from datetime import time
from dotenv import load_dotenv

# Load test environment
load_dotenv('.env.test')


class Config:
    def __init__(self):
        # Email settings
        self.sender_email = os.getenv('SENDER_EMAIL', 'advayaholistic@gmail.com')
        self.gmail_app_password = os.getenv('GMAIL_APP_PASSWORD', '')
        
        # CSV file
        self.csv_file = os.getenv('CSV_FILE', 'data/test.csv')
        
        # Time intervals - USING MINUTES FOR TESTING
        # These will be treated as minutes instead of days
        self.followup1_days = 0  # 0 minutes (immediate)
        self.followup2_days = 0  # 0 minutes (immediate) 
        self.followup3_days = 0  # 0 minutes (immediate)
        
        # Send limits
        self.daily_send_limit = int(os.getenv('DAILY_SEND_LIMIT', '50'))
        
        # Send time window - disabled for testing
        self.send_start_hour = 0
        self.send_end_hour = 24
        
        # Validate
        self._validate()
        
    def _validate(self):
        """Validate configuration"""
        if not self.gmail_app_password:
            raise ValueError("GMAIL_APP_PASSWORD environment variable is required")
            
    def is_within_send_window(self):
        """Always return True for testing"""
        return True