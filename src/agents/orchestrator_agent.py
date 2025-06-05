"""
Orchestrator Agent
This agent manages the overall email automation workflow, coordinating other specialized agents
to replicate the logic of the original EmailAutomation script.
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Ensure the src directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# Also ensure the agents directory is in the path for direct imports if necessary
sys.path.append(os.path.dirname(__file__))


from config import Config
from template_handler import TemplateHandler
from csv_management_agent import CSVManagementAgent
from email_sending_agent import EmailSendingAgent
from reply_checking_agent import ReplyCheckingAgent

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Agent Instructions:
    -------------------
    This agent orchestrates the entire email outreach campaign.
    It manages contacts, checks for replies, determines appropriate follow-ups,
    personalizes messages, sends emails, and records all activities.

    Primary Task: `run_email_campaign`

    Workflow:
    1. Load all contacts from the CSV file.
    2. For each contact:
        a. Check if a reply has already been received. If yes, update status and move to the next contact.
        b. Determine the type of email to send (initial, follow-up 1, 2, or 3) based on campaign logic
           (e.g., days since last email, no reply received).
        c. If an email is due:
            i. Get the appropriate email template (HTML and text).
            ii. Personalize the template and subject line with the contact's information.
            iii. Send the email.
            iv. Update the contact's record in the CSV with the sent date and email type.
        d. If no email is due (e.g., waiting for follow-up interval), move to the next contact.
    3. Report campaign completion and summary statistics.

    Sub-Agents Used (conceptually):
    - CSVManagementAgent: For all CSV data operations (loading, getting, updating contacts).
    - ReplyCheckingAgent: To check if a contact has replied.
    - EmailSendingAgent: To send the actual emails.
    - TemplateHandler: (Directly used) For personalizing email content.

    Constraints:
    - Adhere to follow-up timing rules defined in the configuration.
    - Accurately track sent emails and received replies.
    - Handle errors from sub-agents gracefully and log them.
    """

    def __init__(self):
        """
        Initializes the OrchestratorAgent and its subordinate agents and handlers.
        """
        try:
            self.config = Config()
            self.template_handler = TemplateHandler()

            # Initialize specialized agents
            self.csv_agent = CSVManagementAgent()
            self.email_agent = EmailSendingAgent()
            self.reply_agent = ReplyCheckingAgent()

            logger.info("OrchestratorAgent initialized successfully with all sub-agents and handlers.")
        except Exception as e:
            logger.error(f"Failed to initialize OrchestratorAgent: {e}", exc_info=True)
            raise

    def _determine_email_type(self, contact: dict) -> Optional[str]:
        """
        Determines the type of email to send based on tracking data and campaign logic.
        Mirrors the logic from EmailAutomation.determine_email_type.
        Args:
            contact: A dictionary representing the contact's data.
        Returns:
            A string indicating the email type ('initial', 'followup1', etc.) or None.
        """
        today = datetime.now()

        if not contact.get('initial_sent_date'):
            return 'initial'

        # Dates in CSV might be YYYY-MM-DD or YYYY-MM-DD HH:MM:SS (from test script)
        # We should be robust to this.
        initial_date_str = contact['initial_sent_date']
        try:
            if ' ' in initial_date_str:
                initial_date = datetime.strptime(initial_date_str, '%Y-%m-%d %H:%M:%S')
            else:
                initial_date = datetime.strptime(initial_date_str, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Could not parse initial_sent_date '{initial_date_str}' for contact {contact.get('EMAIL')}. Skipping.")
            return None

        days_since_initial = (today - initial_date).days

        if not contact.get('followup1_sent_date'):
            if days_since_initial >= self.config.followup1_days:
                return 'followup1'
        elif not contact.get('followup2_sent_date'):
            # Follow-up 2 days are from *initial* email in original logic
            if days_since_initial >= self.config.followup2_days:
                return 'followup2'
        elif not contact.get('followup3_sent_date'):
            # Follow-up 3 days are from *initial* email in original logic
            if days_since_initial >= self.config.followup3_days:
                return 'followup3'
        return None

    def _get_template_files(self, email_type: str) -> tuple[Optional[str], Optional[str]]:
        """Gets HTML and text template file names based on email type."""
        template_map = {
            'initial': 'first-email',
            'followup1': 'follow-up-1',
            'followup2': 'follow-up-2',
            'followup3': 'follow-up-3'
        }
        template_name = template_map.get(email_type)
        if not template_name:
            return None, None
        # These are relative to the 'templates' directory.
        # The TemplateHandler will prepend 'templates/' or '../templates' as needed by its own logic.
        # Here, we refer to the base name.
        return f'{template_name}.html', f'{template_name}.txt'

    def _get_subject(self, email_type: str, contact_data: dict) -> str:
        """Gets and personalizes the email subject based on type and contact data."""
        subjects = {
            'initial': 'Quick question from another woman in tech, {{FirstName}}',
            'followup1': 'Did my invite get lost, {{FirstName}}?',
            'followup2': 'Your experience could guide other women, {{FirstName}}',
            'followup3': 'Last call before I wrap, {{FirstName}}'
        }
        subject_template = subjects.get(email_type, 'Follow-up')

        # Perform simple {{Placeholder}} replacement for subject
        # This logic was in EmailAutomation, now here or in TemplateHandler.
        # For now, keeping it simple here.
        # A more robust solution might involve TemplateHandler for subjects too.
        # Using TemplateHandler's method for consistency:
        return self.template_handler._replace_double_brace_placeholders(subject_template, contact_data)

    def run_email_campaign_task(self, dry_run: bool = False, limit: Optional[int] = None):
        """
        Manages the main email automation campaign.
        Args:
            dry_run: If True, simulates sending emails without actually sending.
            limit: Maximum number of emails to send in this run.
        """
        logger.info(f"OrchestratorAgent starting campaign run. Dry run: {dry_run}, Limit: {limit}")

        contacts = self.csv_agent.load_all_contacts_task()
        if not contacts:
            logger.warning("No contacts loaded. Ending campaign.")
            return

        sent_count = 0
        processed_contacts = 0

        for contact in contacts:
            email_address = contact.get('EMAIL')
            if not email_address:
                logger.warning(f"Skipping contact with no email address: {contact.get('FIRST_NAME', 'N/A')}")
                continue

            processed_contacts += 1
            logger.info(f"Processing contact: {email_address}")

            if contact.get('reply_received') == 'True':
                logger.info(f"Skipping {email_address} - reply already marked as received.")
                continue

            # 1. Check for replies using ReplyCheckingAgent
            if self.reply_agent.check_reply_task(sender_email=email_address):
                logger.info(f"Reply detected from {email_address} via ReplyCheckingAgent.")
                contact['reply_received'] = 'True'
                self.csv_agent.update_contact_task(contact) # Update CSV
                continue

            # 2. Determine which email to send
            email_type = self._determine_email_type(contact)
            if not email_type:
                logger.info(f"No email due for {email_address} at this time.")
                continue

            if limit is not None and sent_count >= limit:
                logger.info(f"Send limit of {limit} reached. Stopping campaign for now.")
                break

            logger.info(f"Determined {email_type} email is due for {email_address}.")

            # 3. Get and personalize templates
            # The template paths are relative to the `templates` dir, which TemplateHandler knows.
            # The original EmailAutomation was constructing paths like `os.path.join('..', 'templates', html_file)`
            # when it was in `src/`. TemplateHandler now manages this.
            # The `personalize_template` method in TemplateHandler expects path relative to CWD or an absolute path.
            # Let's ensure the paths are correct for TemplateHandler.
            # The TemplateHandler itself is in `src/` and usually templates are in `templates/` at root.
            # So `templates/first-email.html` should work if CWD is project root.

            html_template_name, text_template_name = self._get_template_files(email_type)
            if not html_template_name:
                logger.error(f"No template found for email type {email_type}. Skipping {email_address}.")
                continue

            # Construct paths that TemplateHandler can use (relative to project root)
            # This assumes the agent is run from the project root directory.
            # If not, TemplateHandler might need to be smarter or paths adjusted.
            # For now, let's assume 'templates/file.html' is the way.
            html_template_path = os.path.join('templates', html_template_name)
            text_template_path = os.path.join('templates', text_template_name)

            if not os.path.exists(html_template_path): # Quick check before passing to handler
                 logger.error(f"HTML template file not found: {html_template_path} for contact {email_address}")
                 continue

            personalized_html = self.template_handler.personalize_template(html_template_path, contact)
            personalized_text = self.template_handler.personalize_template(text_template_path, contact) if os.path.exists(text_template_path) else ""

            personalized_subject = self._get_subject(email_type, contact)

            # 4. Send email using EmailSendingAgent
            if dry_run:
                logger.info(f"[DRY RUN] Would send {email_type} to {email_address}. Subject: '{personalized_subject}'")
                # In dry run, we should still update tracking as if it were sent
                # This matches the original script's dry run behavior implicitly
                sent_successfully = True
            else:
                logger.info(f"Attempting to send {email_type} to {email_address} via EmailSendingAgent.")
                sent_successfully = self.email_agent.send_email_task(
                    recipient_email=email_address,
                    subject=personalized_subject,
                    html_content=personalized_html,
                    text_content=personalized_text
                )

            # 5. Update tracking in CSV if email was sent (or dry_run)
            if sent_successfully:
                sent_count += 1
                tracking_field_map = {
                    'initial': 'initial_sent_date',
                    'followup1': 'followup1_sent_date',
                    'followup2': 'followup2_sent_date',
                    'followup3': 'followup3_sent_date'
                }
                date_field_to_update = tracking_field_map.get(email_type)
                if date_field_to_update:
                    # Use YYYY-MM-DD for dates, but if testing with minutes, need YYYY-MM-DD HH:MM:SS
                    # For now, stick to YYYY-MM-DD as per original main script.
                    # The test script used HH:MM:SS for its own tracking.
                    contact[date_field_to_update] = datetime.now().strftime('%Y-%m-%d')
                contact['last_email_type'] = email_type

                logger.info(f"Updating CSV for {email_address}: last_email_type='{email_type}', {date_field_to_update}='{contact[date_field_to_update]}'")
                self.csv_agent.update_contact_task(contact)

                if not dry_run and sent_count < (limit if limit is not None else float('inf')) and processed_contacts < len(contacts):
                    logger.info(f"Waiting {self.config.email_delay_seconds} seconds before next email...")
                    time.sleep(self.config.email_delay_seconds)
            else:
                logger.error(f"Failed to send {email_type} to {email_address}.")

        logger.info(f"OrchestratorAgent campaign run finished. Processed {processed_contacts} contacts. Sent {sent_count} emails.")

    def perform_global_reply_check_task(self):
        """
        Checks for replies for all contacts in the CSV and updates their status.
        This is equivalent to the old script's --check-replies functionality.
        """
        logger.info("OrchestratorAgent starting global reply check task...")
        contacts = self.csv_agent.load_all_contacts_task()
        if not contacts:
            logger.warning("No contacts loaded. Ending global reply check.")
            return

        updated_reply_count = 0
        for contact in contacts:
            email_address = contact.get('EMAIL')
            if not email_address:
                logger.warning(f"Skipping contact with no email address: {contact.get('FIRST_NAME', 'N/A')}")
                continue

            # Only check if not already marked as replied
            if contact.get('reply_received') == 'True':
                continue

            logger.debug(f"Checking reply for {email_address} via ReplyCheckingAgent.")
            if self.reply_agent.check_reply_task(sender_email=email_address):
                logger.info(f"Reply detected from {email_address} during global check.")
                contact['reply_received'] = 'True'
                if self.csv_agent.update_contact_task(contact):
                    logger.info(f"Marked reply_received for {email_address} in CSV.")
                    updated_reply_count += 1
                else:
                    logger.error(f"Failed to update CSV for {email_address} after detecting reply.")

        logger.info(f"OrchestratorAgent global reply check finished. Found and updated {updated_reply_count} new replies.")


# Example of how this agent might be used
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Attempting to initialize and use OrchestratorAgent...")

    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if load_dotenv(dotenv_path, override=True):
        logger.info(f"Loaded .env file from {dotenv_path}")
    else:
        logger.warning(f".env file not found at {dotenv_path}. Config might be default or incorrect.")

    try:
        orchestrator = OrchestratorAgent()

        # Run a campaign (e.g., dry run with a limit)
        logger.info("\n--- Running campaign (dry_run=True, limit=5) ---")
        orchestrator.run_email_campaign_task(dry_run=True, limit=5)

        # Example of global reply check:
        # logger.info("\n--- Performing global reply check ---")
        # orchestrator.perform_global_reply_check_task()

        # To run a live campaign (use with caution):
        # logger.info("\n--- Running LIVE campaign (limit=2) ---")
        # orchestrator.run_email_campaign_task(dry_run=False, limit=2)

    except Exception as e:
        logger.error(f"Failed to run OrchestratorAgent example: {e}", exc_info=True)

# End of file
