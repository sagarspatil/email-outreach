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

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich import print as rprint

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
console = Console()


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
        console.print(Panel.fit("[bold blue]Email Automation Starting[/bold blue]", border_style="blue"))
        
        if check_replies_only:
            self._check_replies()
            return
            
        contacts = self.csv_handler.load_contacts()
        sent_count = 0
        
        # Create progress bar
        total_contacts = min(len(contacts), limit) if limit else len(contacts)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[green]Processing contacts...", total=total_contacts)
            
            for contact in contacts:
                if limit and sent_count >= limit:
                    console.print(f"[yellow]Reached send limit of {limit} emails[/yellow]")
                    break
                    
                try:
                    if self._process_contact(contact, dry_run):
                        sent_count += 1
                    progress.update(task, advance=1)
                except Exception as e:
                    console.print(f"[red]Error processing contact {contact.get('EMAIL')}: {str(e)}[/red]")
                    
        self.csv_handler.save_contacts(contacts)
        
        # Summary table
        table = Table(title="Email Automation Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Total Contacts", str(len(contacts)))
        table.add_row("Emails Sent", str(sent_count))
        table.add_row("Status", "[green]Completed[/green]")
        
        console.print("\n")
        console.print(table)
        
    def _process_contact(self, contact, dry_run=False):
        """Process a single contact"""
        email = contact.get('EMAIL')
        if not email:
            logger.warning(f"Skipping contact with no email: {contact}")
            return False
            
        if contact.get('reply_received') == 'True':
            console.print(f"[dim]Skipping {email} - reply already received[/dim]")
            return False
            
        # Check for replies first
        if self.reply_checker.has_replied(email):
            contact['reply_received'] = 'True'
            console.print(f"[green]Reply detected from {email}[/green]")
            return False
            
        # Determine which email to send
        email_type = self._determine_email_type(contact)
        if not email_type:
            return False
            
        # Personalize template
        template_file = self._get_template_file(email_type)
        if not os.path.exists(template_file):
            logger.error(f"Template file not found: {template_file}")
            return False
            
        personalized_html = self.template_handler.personalize_template(
            template_file, contact
        )
        
        # Send or simulate
        if dry_run:
            console.print(f"[yellow][DRY RUN][/yellow] Would send {email_type} to [bold]{email}[/bold]")
            dry_run_panel = Panel(
                f"To: {email}\nType: {email_type}\nSubject: {self._get_subject(email_type)}",
                title="[yellow]Dry Run Email[/yellow]",
                border_style="yellow"
            )
            console.print(dry_run_panel)
        else:
            success = self.email_sender.send_email(
                email,
                self._get_subject(email_type),
                personalized_html
            )
            if success:
                self._update_tracking(contact, email_type)
                console.print(f"[green]✓[/green] Sent {email_type} to [bold]{email}[/bold]")
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
        console.print(Panel.fit("[bold cyan]Checking for Replies[/bold cyan]", border_style="cyan"))
        contacts = self.csv_handler.load_contacts()
        reply_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Checking emails...", total=None)
            
            for contact in contacts:
                email = contact.get('EMAIL')
                if email and contact.get('reply_received') != 'True':
                    if self.reply_checker.has_replied(email):
                        contact['reply_received'] = 'True'
                        reply_count += 1
                        console.print(f"[green]✓ Reply detected from {email}[/green]")
                        
        self.csv_handler.save_contacts(contacts)
        
        # Summary
        summary_panel = Panel(
            f"Total new replies found: [bold green]{reply_count}[/bold green]",
            title="Reply Check Summary",
            border_style="green"
        )
        console.print("\n")
        console.print(summary_panel)


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
        console.print(f"[bold red]Fatal error: {str(e)}[/bold red]")
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()