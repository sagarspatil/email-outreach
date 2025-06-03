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
        self.csv_file = os.getenv('CSV_FILE', 'final.csv')
        
        # Time intervals (in days)
        self.followup1_days = int(os.getenv('FOLLOWUP1_DAYS', '3'))
        self.followup2_days = int(os.getenv('FOLLOWUP2_DAYS', '5'))
        self.followup3_days = int(os.getenv('FOLLOWUP3_DAYS', '7'))
        
        # Send limits
        self.daily_send_limit = int(os.getenv('DAILY_SEND_LIMIT', '50'))
        
        # Send time window (optional)
        self.send_start_hour = os.getenv('SEND_START_HOUR')
        self.send_end_hour = os.getenv('SEND_END_HOUR')
        
        # Convert to int if provided
        if self.send_start_hour is not None:
            self.send_start_hour = int(self.send_start_hour)
        if self.send_end_hour is not None:
            self.send_end_hour = int(self.send_end_hour)
        
        # Validate
        self._validate()
        
    def _validate(self):
        """Validate configuration"""
        if not self.gmail_app_password:
            raise ValueError("GMAIL_APP_PASSWORD environment variable is required")
            
        # Only validate send hours if both are provided
        if self.send_start_hour is not None and self.send_end_hour is not None:
            if self.send_start_hour >= self.send_end_hour:
                raise ValueError("Send start hour must be before end hour")
            
        if self.followup1_days < 1 or self.followup2_days < 1 or self.followup3_days < 1:
            raise ValueError("Follow-up intervals must be at least 1 day")
            
    def is_within_send_window(self):
        """Check if current time is within send window"""
        # If send hours not configured, always allow sending
        if self.send_start_hour is None or self.send_end_hour is None:
            return True
            
        from datetime import datetime
        current_hour = datetime.now().hour
        return self.send_start_hour <= current_hour < self.send_end_hour