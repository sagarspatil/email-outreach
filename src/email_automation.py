#!/usr/bin/env python3
"""
Email Automation Script
Main entry point for automated email outreach and follow-up campaigns
"""

import argparse
import logging
import sys
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
            
        # Personalize template
        template_file = self._get_template_file(email_type)
        # Look for template in templates/ directory
        template_path = os.path.join('..', 'templates', template_file)
        if not os.path.exists(template_path):
            logger.error(f"Template file not found: {template_path}")
            return False
            
        personalized_html = self.template_handler.personalize_template(
            template_path, contact
        )
        
        # Send or simulate
        if dry_run:
            logger.info(f"[DRY RUN] Would send {email_type} to {email}")
            print(f"\nTo: {email}")
            print(f"Type: {email_type}")
            print(f"Subject: {self._get_subject(email_type)}")
            print("---")
        else:
            success = self.email_sender.send_email(
                email,
                self._get_subject(email_type),
                personalized_html
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
        
        if not contact.get('followup1_sent_date'):
            days_passed = (today - initial_date).days
            if days_passed >= self.config.followup1_days:
                return 'followup1'
                
        elif not contact.get('followup2_sent_date'):
            followup1_date = datetime.strptime(contact['followup1_sent_date'], '%Y-%m-%d')
            days_passed = (today - followup1_date).days
            if days_passed >= self.config.followup2_days:
                return 'followup2'
                
        elif not contact.get('followup3_sent_date'):
            followup2_date = datetime.strptime(contact['followup2_sent_date'], '%Y-%m-%d')
            days_passed = (today - followup2_date).days
            if days_passed >= self.config.followup3_days:
                return 'followup3'
                
        return None
        
    def _get_template_file(self, email_type):
        """Get template file path based on email type"""
        template_map = {
            'initial': 'first-email.html',
            'followup1': 'follow-up-1.html',
            'followup2': 'follow-up-2.html',
            'followup3': 'follow-up-3.html'
        }
        return template_map.get(email_type, '')
        
    def _get_subject(self, email_type):
        """Get email subject based on type"""
        subjects = {
            'initial': 'Introduction - Partnership Opportunity',
            'followup1': 'Following up on my previous email',
            'followup2': 'Quick follow-up',
            'followup3': 'Final follow-up'
        }
        return subjects.get(email_type, 'Follow-up')
        
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