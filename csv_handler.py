"""
CSV file handling for contact management
"""

import csv
import logging
import os
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class CSVHandler:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.required_columns = [
            'DESCRIPTION', 'JOB_TITLE', 'EMAIL', 'LINKEDIN_URL',
            'COMPANY_WEBSITE', 'LOCATION', 'PHONE_NUMBER', 'FIRST_NAME'
        ]
        self.tracking_columns = [
            'initial_sent_date', 'followup1_sent_date', 'followup2_sent_date',
            'followup3_sent_date', 'reply_received', 'last_email_type'
        ]
        
    def load_contacts(self):
        """Load contacts from CSV file"""
        if not os.path.exists(self.csv_file):
            logger.error(f"CSV file not found: {self.csv_file}")
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
            
        contacts = []
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate columns
                if reader.fieldnames:
                    self._validate_columns(reader.fieldnames)
                    
                for row in reader:
                    # Clean and validate row data
                    contact = self._process_row(row)
                    if contact:
                        contacts.append(contact)
                        
            logger.info(f"Loaded {len(contacts)} contacts from {self.csv_file}")
            return contacts
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            raise
            
    def save_contacts(self, contacts):
        """Save contacts back to CSV file with tracking information"""
        if not contacts:
            logger.warning("No contacts to save")
            return
            
        # Create backup
        backup_file = f"{self.csv_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(self.csv_file):
            shutil.copy2(self.csv_file, backup_file)
            logger.info(f"Created backup: {backup_file}")
            
        try:
            # Determine all columns (original + tracking)
            all_columns = self.required_columns + self.tracking_columns
            
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=all_columns)
                writer.writeheader()
                
                for contact in contacts:
                    # Ensure all columns exist
                    row = {col: contact.get(col, '') for col in all_columns}
                    writer.writerow(row)
                    
            logger.info(f"Saved {len(contacts)} contacts to {self.csv_file}")
            
        except Exception as e:
            logger.error(f"Error saving CSV file: {str(e)}")
            # Restore from backup if save failed
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, self.csv_file)
                logger.info("Restored from backup due to save error")
            raise
            
    def _validate_columns(self, fieldnames):
        """Validate that required columns exist"""
        missing_columns = set(self.required_columns) - set(fieldnames)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
    def _process_row(self, row):
        """Process and validate a single row"""
        # Skip rows without email
        if not row.get('EMAIL'):
            return None
            
        # Clean email
        row['EMAIL'] = row['EMAIL'].strip().lower()
        
        # Extract company name from website if available
        if row.get('COMPANY_WEBSITE'):
            row['COMPANY'] = self._extract_company_name(row['COMPANY_WEBSITE'])
        else:
            row['COMPANY'] = 'your company'
            
        # Ensure tracking columns exist
        for col in self.tracking_columns:
            if col not in row:
                row[col] = ''
                
        return row
        
    def _extract_company_name(self, website):
        """Extract company name from website URL"""
        import re
        
        # Remove protocol and www
        website = website.lower()
        website = re.sub(r'^https?://', '', website)
        website = re.sub(r'^www\.', '', website)
        
        # Extract domain name
        domain = website.split('/')[0].split('.')[0]
        
        # Capitalize first letter
        return domain.capitalize() if domain else 'your company'
        
    def get_statistics(self):
        """Get statistics about contacts"""
        contacts = self.load_contacts()
        
        stats = {
            'total_contacts': len(contacts),
            'emails_sent': {
                'initial': 0,
                'followup1': 0,
                'followup2': 0,
                'followup3': 0
            },
            'replies_received': 0,
            'pending_contacts': 0
        }
        
        for contact in contacts:
            if contact.get('reply_received') == 'True':
                stats['replies_received'] += 1
            
            if contact.get('initial_sent_date'):
                stats['emails_sent']['initial'] += 1
            if contact.get('followup1_sent_date'):
                stats['emails_sent']['followup1'] += 1
            if contact.get('followup2_sent_date'):
                stats['emails_sent']['followup2'] += 1
            if contact.get('followup3_sent_date'):
                stats['emails_sent']['followup3'] += 1
                
            if not contact.get('initial_sent_date'):
                stats['pending_contacts'] += 1
                
        return stats