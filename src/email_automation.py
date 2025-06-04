#!/usr/bin/env python3
"""
Email Automation Script
Main entry point for automated email outreach and follow-up campaigns
"""

import argparse
import logging
import sys
import time
from datetime import datetime
import os
from dotenv import load_dotenv

from config import Config
from csv_handler import CSVHandler
from email_sender import EmailSender
from reply_checker import ReplyChecker
from template_handler import TemplateHandler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class EmailAutomation:
    def __init__(self, config: Config):
        self.config = config
        self.csv_handler = CSVHandler(config.csv_file)
        self.email_sender = EmailSender(
            config.sender_email,
            config.gmail_app_password
        )
        self.reply_checker = ReplyChecker(
            config.sender_email,
            config.gmail_app_password
        )
        self.template_handler = TemplateHandler()
        
    def run(self, dry_run=False, limit=None, check_replies_only=False):
        """Main execution flow"""
        logger.info("Starting email automation...")
        
        if check_replies_only:
            self._check_replies()
            return
            
        contacts = self.csv_handler.load_contacts()
        sent_count = 0
        
        for contact in contacts:
            if limit and sent_count >= limit:
                logger.info(f"Reached send limit of {limit} emails")
                break
                
            try:
                if self._process_contact(contact, dry_run):
                    sent_count += 1
                    # Add delay between emails (only in production, not dry run)
                    if not dry_run and sent_count < len(contacts):
                        logger.info(f"Waiting {self.config.email_delay_seconds} seconds before next email...")
                        time.sleep(self.config.email_delay_seconds)
            except Exception as e:
                logger.error(f"Error processing contact {contact.get('EMAIL')}: {str(e)}")
                
        self.csv_handler.save_contacts(contacts)
        logger.info(f"Email automation completed. Sent {sent_count} emails.")
        
    def _process_contact(self, contact, dry_run=False):
        """Process a single contact"""
        email = contact.get('EMAIL')
        if not email:
            logger.warning(f"Skipping contact with no email: {contact}")
            return False
            
        if contact.get('reply_received') == 'True':
            logger.info(f"Skipping {email} - reply already received")
            return False
            
        # Check for replies first
        if self.reply_checker.has_replied(email):
            contact['reply_received'] = 'True'
            logger.info(f"Reply detected from {email}")
            return False
            
        # Determine which email to send
        email_type = self._determine_email_type(contact)
        if not email_type:
            return False
            
        # Personalize templates
        html_file, text_file = self._get_template_files(email_type)
        # Look for templates in templates/ directory
        html_path = os.path.join('..', 'templates', html_file)
        text_path = os.path.join('..', 'templates', text_file)
        
        if not os.path.exists(html_path):
            logger.error(f"HTML template file not found: {html_path}")
            return False
        if not os.path.exists(text_path):
            logger.error(f"Text template file not found: {text_path}")
            return False
            
        personalized_html = self.template_handler.personalize_template(
            html_path, contact
        )
        personalized_text = self.template_handler.personalize_template(
            text_path, contact
        )
        
        # Personalize subject line
        subject_template = self._get_subject(email_type)
        personalized_subject = self._replace_double_brace_placeholders(subject_template, contact)
        
        # Send or simulate
        if dry_run:
            logger.info(f"[DRY RUN] Would send {email_type} to {email}")
            print(f"\nTo: {email}")
            print(f"Type: {email_type}")
            print(f"Subject: {personalized_subject}")
            print("---")
        else:
            success = self.email_sender.send_email(
                email,
                personalized_subject,
                personalized_html,
                personalized_text
            )
            if success:
                self._update_tracking(contact, email_type)
                logger.info(f"Sent {email_type} to {email}")
                return True
                
        return False
        
    def _determine_email_type(self, contact):
        """Determine which email to send based on tracking data"""
        today = datetime.now()
        
        if not contact.get('initial_sent_date'):
            return 'initial'
            
        initial_date = datetime.strptime(contact['initial_sent_date'], '%Y-%m-%d')
        days_since_initial = (today - initial_date).days
        
        # All follow-ups are calculated from the initial email date
        if not contact.get('followup1_sent_date'):
            if days_since_initial >= self.config.followup1_days:
                return 'followup1'
                
        elif not contact.get('followup2_sent_date'):
            if days_since_initial >= self.config.followup2_days:
                return 'followup2'
                
        elif not contact.get('followup3_sent_date'):
            if days_since_initial >= self.config.followup3_days:
                return 'followup3'
                
        return None
        
    def _get_template_files(self, email_type):
        """Get both HTML and text template file paths for email type"""
        template_map = {
            'initial': 'first-email',
            'followup1': 'follow-up-1',
            'followup2': 'follow-up-2',
            'followup3': 'follow-up-3'
        }
        template_name = template_map.get(email_type, '')
        if not template_name:
            return '', ''
        return f'{template_name}.html', f'{template_name}.txt'
        
    def _get_subject(self, email_type):
        """Get email subject based on type"""
        subjects = {
            'initial': 'Quick question from another woman in tech, {{FirstName}}',
            'followup1': 'Did my invite get lost, {{FirstName}}?',
            'followup2': 'Your experience could guide other women, {{FirstName}}',
            'followup3': 'Last call before I wrap, {{FirstName}}'
        }
        return subjects.get(email_type, 'Follow-up')
        
    def _replace_double_brace_placeholders(self, template, data):
        """Replace {{FirstName}} style placeholders for subjects"""
        import re
        double_brace_pattern = re.compile(r'\{\{([A-Za-z]+)\}\}')
        
        def replace_match(match):
            placeholder = match.group(1).strip()
            if placeholder.lower() == 'firstname':
                return data.get('FIRST_NAME', 'there')
            elif placeholder.lower() == 'jobtitle':
                return data.get('JOB_TITLE', 'Professional')
            else:
                return match.group(0)  # Keep original placeholder
                
        return double_brace_pattern.sub(replace_match, template)
        
    def _update_tracking(self, contact, email_type):
        """Update tracking information after sending email"""
        today = datetime.now().strftime('%Y-%m-%d')
        tracking_map = {
            'initial': 'initial_sent_date',
            'followup1': 'followup1_sent_date',
            'followup2': 'followup2_sent_date',
            'followup3': 'followup3_sent_date'
        }
        contact[tracking_map[email_type]] = today
        contact['last_email_type'] = email_type
        
    def _check_replies(self):
        """Check replies for all contacts"""
        logger.info("Checking for replies...")
        contacts = self.csv_handler.load_contacts()
        reply_count = 0
        
        for contact in contacts:
            email = contact.get('EMAIL')
            if email and contact.get('reply_received') != 'True':
                if self.reply_checker.has_replied(email):
                    contact['reply_received'] = 'True'
                    reply_count += 1
                    logger.info(f"Reply detected from {email}")
                    
        self.csv_handler.save_contacts(contacts)
        logger.info(f"Reply check completed. Found {reply_count} new replies.")


def main():
    parser = argparse.ArgumentParser(description='Email Automation Script')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview what would be sent without actually sending')
    parser.add_argument('--limit', type=int, help='Send only N emails')
    parser.add_argument('--check-replies', action='store_true',
                       help='Only check for replies')
    
    args = parser.parse_args()
    
    try:
        config = Config()
        automation = EmailAutomation(config)
        automation.run(
            dry_run=args.dry_run,
            limit=args.limit,
            check_replies_only=args.check_replies
        )
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()