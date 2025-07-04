#!/usr/bin/env python3
"""
Test Email Automation Script - Uses MINUTES instead of DAYS for testing
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_test import Config  # Using test config
from csv_handler import CSVHandler
from email_sender import EmailSender
from reply_checker import ReplyChecker
from template_handler import TemplateHandler

load_dotenv('.env.test')

# Configure rich logging
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.logging import RichHandler
    from rich import print as rprint
    
    console = Console()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            RichHandler(console=console, rich_tracebacks=True),
            logging.FileHandler('email_automation_test.log')
        ]
    )
except ImportError:
    # Fallback to standard logging if rich is not installed
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('email_automation_test.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    console = None
    rprint = print

logger = logging.getLogger(__name__)


class EmailAutomation:
    def __init__(self, config: Config):
        self.config = config
        
        # Fix CSV column name mapping for test.csv
        csv_path = config.csv_file if os.path.exists(config.csv_file) else 'data/test.csv'
        self.csv_handler = CSVHandler(csv_path)
        # Override the required columns for test.csv
        self.csv_handler.required_columns = [
            'DESCRIPTION', 'JOB_TITLE', 'EMAIL', 'LINKEDIN_URL',
            'COMPANY_WEBSITE', 'LOCATION', 'PHONE_NUMBER', 'FIRST_NAME'
        ]
        
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
        if console:
            console.print("[bold green]Starting TEST email automation (using MINUTES instead of days)...[/bold green]")
        else:
            logger.info("Starting TEST email automation (using MINUTES instead of days)...")
        
        if check_replies_only:
            self._check_replies()
            return
            
        contacts = self.csv_handler.load_contacts()
        
        # Fix column name mapping for test.csv
        for contact in contacts:
            if 'JOB TITLE' in contact and 'JOB_TITLE' not in contact:
                contact['JOB_TITLE'] = contact['JOB TITLE']
        
        sent_count = 0
        
        if console and not dry_run:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Processing contacts...", total=len(contacts))
                
                for contact in contacts:
                    if limit and sent_count >= limit:
                        console.print(f"[yellow]Reached send limit of {limit} emails[/yellow]")
                        break
                        
                    try:
                        if self._process_contact(contact, dry_run):
                            sent_count += 1
                    except Exception as e:
                        console.print(f"[red]Error processing {contact.get('EMAIL')}: {str(e)}[/red]")
                        
                    progress.advance(task)
        else:
            # Non-rich or dry-run mode
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
        
        if console:
            console.print(f"[bold green]Email automation completed. Sent {sent_count} emails.[/bold green]")
            
            # Show summary table
            table = Table(title="Email Campaign Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Contacts", str(len(contacts)))
            table.add_row("Emails Sent", str(sent_count))
            table.add_row("Mode", "TEST MODE (Minutes)")
            
            console.print(table)
        else:
            logger.info(f"Email automation completed. Sent {sent_count} emails.")
        
    def _process_contact(self, contact, dry_run=False):
        """Process a single contact"""
        email = contact.get('EMAIL')
        if not email:
            logger.warning(f"Skipping contact with no email: {contact}")
            return False
            
        # DISABLED FOR TESTING - Don't check replies
        # if contact.get('reply_received') == 'True':
        #     if console:
        #         console.print(f"[dim]Skipping {email} - reply already received[/dim]")
        #     else:
        #         logger.info(f"Skipping {email} - reply already received")
        #     return False
        #     
        # # Check for replies first
        # if self.reply_checker.has_replied(email):
        #     contact['reply_received'] = 'True'
        #     if console:
        #         console.print(f"[yellow]Reply detected from {email}[/yellow]")
        #     else:
        #         logger.info(f"Reply detected from {email}")
        #     return False
            
        # Determine which email to send
        email_type = self._determine_email_type(contact)
        if not email_type:
            return False
            
        # Personalize templates
        html_file, text_file = self._get_template_files(email_type)
        # Look for templates in templates/ directory
        html_path = os.path.join('templates', html_file)
        text_path = os.path.join('templates', text_file)
        
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
            if console:
                console.print(f"\n[yellow][DRY RUN][/yellow] Would send [bold]{email_type}[/bold] to [cyan]{email}[/cyan]")
                console.print(f"Subject: [green]{personalized_subject}[/green]")
                console.print("[dim]---[/dim]")
            else:
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
                if console:
                    console.print(f"[green]✓[/green] Sent [bold]{email_type}[/bold] to [cyan]{email}[/cyan]")
                else:
                    logger.info(f"Sent {email_type} to {email}")
                return True
                
        return False
        
    def _determine_email_type(self, contact):
        """Determine which email to send based on tracking data - USING MINUTES FOR TEST"""
        now = datetime.now()
        
        if not contact.get('initial_sent_date'):
            return 'initial'
            
        # Parse as datetime for minute-based calculations
        initial_date = datetime.strptime(contact['initial_sent_date'], '%Y-%m-%d %H:%M:%S')
        minutes_since_initial = (now - initial_date).total_seconds() / 60
        
        # All follow-ups calculated from initial email (using minutes instead of days for testing)
        if not contact.get('followup1_sent_date'):
            if minutes_since_initial >= self.config.followup1_days:  # Using "days" as minutes
                if console:
                    console.print(f"[dim]Follow-up 1 due: {minutes_since_initial:.1f} minutes since initial[/dim]")
                return 'followup1'
                
        elif not contact.get('followup2_sent_date'):
            if minutes_since_initial >= self.config.followup2_days:  # Using "days" as minutes
                if console:
                    console.print(f"[dim]Follow-up 2 due: {minutes_since_initial:.1f} minutes since initial[/dim]")
                return 'followup2'
                
        elif not contact.get('followup3_sent_date'):
            if minutes_since_initial >= self.config.followup3_days:  # Using "days" as minutes
                if console:
                    console.print(f"[dim]Follow-up 3 due: {minutes_since_initial:.1f} minutes since initial[/dim]")
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
        """Update tracking information after sending email - WITH TIMESTAMP FOR TEST"""
        # Use full timestamp for minute-based tracking
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tracking_map = {
            'initial': 'initial_sent_date',
            'followup1': 'followup1_sent_date',
            'followup2': 'followup2_sent_date',
            'followup3': 'followup3_sent_date'
        }
        contact[tracking_map[email_type]] = now
        contact['last_email_type'] = email_type
        
    def _check_replies(self):
        """Check replies for all contacts"""
        if console:
            console.print("[cyan]Checking for replies...[/cyan]")
        else:
            logger.info("Checking for replies...")
            
        contacts = self.csv_handler.load_contacts()
        reply_count = 0
        
        with Progress(console=console) if console else None as progress:
            if progress:
                task = progress.add_task("[cyan]Checking emails...", total=len(contacts))
                
            for contact in contacts:
                email = contact.get('EMAIL')
                if email and contact.get('reply_received') != 'True':
                    if self.reply_checker.has_replied(email):
                        contact['reply_received'] = 'True'
                        reply_count += 1
                        if console:
                            console.print(f"[green]✓[/green] Reply detected from [cyan]{email}[/cyan]")
                        else:
                            logger.info(f"Reply detected from {email}")
                            
                if progress:
                    progress.advance(task)
                    
        self.csv_handler.save_contacts(contacts)
        
        if console:
            console.print(f"[bold green]Reply check completed. Found {reply_count} new replies.[/bold green]")
        else:
            logger.info(f"Reply check completed. Found {reply_count} new replies.")


def main():
    parser = argparse.ArgumentParser(description='TEST Email Automation Script (Minutes-based)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview what would be sent without actually sending')
    parser.add_argument('--limit', type=int, help='Send only N emails')
    parser.add_argument('--check-replies', action='store_true',
                       help='Only check for replies')
    
    args = parser.parse_args()
    
    if console:
        console.print("[bold cyan]TEST MODE: Using MINUTES instead of DAYS for follow-ups[/bold cyan]")
        console.print("[yellow]Reply checking DISABLED for testing[/yellow]")
        console.print("Follow-up 1: After 1 minute")
        console.print("Follow-up 2: After 1 minute")
        console.print("Follow-up 3: After 1 minute\n")
    
    try:
        config = Config()
        automation = EmailAutomation(config)
        automation.run(
            dry_run=args.dry_run,
            limit=args.limit,
            check_replies_only=args.check_replies
        )
    except Exception as e:
        if console:
            console.print(f"[bold red]Fatal error: {str(e)}[/bold red]")
        else:
            logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()