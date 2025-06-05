"""
Email Sending Agent
This agent is responsible for sending emails using the EmailSender utility.
"""

import logging
import os
import sys

# Ensure the src directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from email_sender import EmailSender
from config import Config

logger = logging.getLogger(__name__)

class EmailSendingAgent:
    """
    Agent Instructions:
    -------------------
    This agent is tasked with sending an email.
    You will be provided with the recipient's email address, the subject of the email,
    and the HTML body content. You may optionally be provided with a plain text version of the body.

    Your primary tool is `send_email_tool`.

    Workflow:
    1. Receive the recipient_email, subject, html_body, and optionally text_body.
    2. Use the `send_email_tool` to dispatch the email.
    3. Report the success or failure of the email sending operation.

    Constraints:
    - Ensure all required parameters (recipient_email, subject, html_body) are present.
    - Handle potential errors during email sending gracefully and report them.
    """

    def __init__(self):
        """
        Initializes the EmailSendingAgent.
        It sets up the EmailSender using credentials from the application configuration.
        """
        try:
            app_config = Config()
            self.email_sender = EmailSender(
                sender_email=app_config.sender_email,
                app_password=app_config.gmail_app_password
            )
            logger.info("EmailSendingAgent initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize EmailSendingAgent: {e}")
            # Propagate the error or handle it as per agent framework requirements
            raise

    def send_email_task(self, recipient_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """
        Sends an email to the specified recipient.

        Args:
            recipient_email: The email address of the recipient.
            subject: The subject of theemail.
            html_content: The HTML content of the email body.
            text_content: Optional plain text content for the email body. If not provided,
                          it's good practice for the EmailSender to generate it or handle its absence.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        if not all([recipient_email, subject, html_content]):
            logger.error("Missing required parameters for sending email: recipient, subject, or HTML content.")
            return False

        try:
            logger.info(f"Attempting to send email to {recipient_email} with subject '{subject}'")
            # The EmailSender's send_email method expects html_content and optionally text_content.
            success = self.email_sender.send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            if success:
                logger.info(f"Email successfully sent to {recipient_email}.")
            else:
                logger.warning(f"Failed to send email to {recipient_email} as reported by EmailSender.")
            return success
        except Exception as e:
            logger.error(f"An error occurred while sending email to {recipient_email}: {e}", exc_info=True)
            return False

# Example of how this agent might be used (for testing or direct invocation)
if __name__ == '__main__':
    # Configure basic logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # This is a placeholder for how an agent runner or a testing script might invoke the agent.
    # In a real scenario, the agent's lifecycle and task execution would be managed by an agent framework (e.g., agno).

    logger.info("Attempting to initialize and use EmailSendingAgent for a test email...")

    # Load .env from the root directory for configuration
    from dotenv import load_dotenv
    # Construct the path to the .env file (assuming it's in the parent directory of src)
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if load_dotenv(dotenv_path, override=True):
        logger.info(f"Loaded .env file from {dotenv_path}")
    else:
        logger.warning(f".env file not found at {dotenv_path}. Email sending might fail if config is not set via environment.")

    try:
        agent = EmailSendingAgent()

        # Example usage:
        # Replace with actual recipient, subject, and body for testing.
        # Be careful with real email sending during tests.
        test_recipient = os.getenv("TEST_RECIPIENT_EMAIL") # You might want to set this in your .env for testing

        if test_recipient:
            logger.info(f"Test recipient found: {test_recipient}")
            email_sent = agent.send_email_task(
                recipient_email=test_recipient,
                subject="Agent Test Email",
                html_content="<h1>Hello from EmailSendingAgent!</h1><p>This is a test email.</p>",
                text_content="Hello from EmailSendingAgent! This is a test email."
            )
            if email_sent:
                logger.info("Test email dispatched successfully via agent.")
            else:
                logger.error("Test email dispatch failed via agent.")
        else:
            logger.warning("TEST_RECIPIENT_EMAIL not set in environment. Skipping test email sending.")

    except Exception as e:
        logger.error(f"Failed to run EmailSendingAgent example: {e}", exc_info=True)
