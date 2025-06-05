"""
Reply Checking Agent
This agent is responsible for checking for replies from a specific email address
using the ReplyChecker utility.
"""

import logging
import os
import sys

# Ensure the src directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from reply_checker import ReplyChecker
from config import Config

logger = logging.getLogger(__name__)

class ReplyCheckingAgent:
    """
    Agent Instructions:
    -------------------
    This agent is tasked with checking if a reply has been received from a specific email address.
    You will be provided with the sender's email address to check for replies from.

    Your primary tool is `check_for_reply_tool`.

    Workflow:
    1. Receive the sender_email address.
    2. Use the `check_for_reply_tool` to determine if a reply has been received from this sender.
    3. Report whether a reply was found (True/False).

    Constraints:
    - Ensure the sender_email parameter is present.
    - Handle potential errors during the reply checking process gracefully and report them.
    """

    def __init__(self):
        """
        Initializes the ReplyCheckingAgent.
        It sets up the ReplyChecker using credentials from the application configuration.
        The ReplyChecker is configured to check the inbox of the SENDER_EMAIL defined in the config.
        """
        try:
            app_config = Config()
            self.reply_checker = ReplyChecker(
                email_address=app_config.sender_email, # This is the inbox we are checking
                app_password=app_config.gmail_app_password
            )
            logger.info("ReplyCheckingAgent initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ReplyCheckingAgent: {e}")
            # Propagate the error or handle it as per agent framework requirements
            raise

    def check_reply_task(self, sender_email: str) -> bool:
        """
        Checks for a reply from the specified sender's email address.

        Args:
            sender_email: The email address of the sender to check for replies from.

        Returns:
            True if a reply from the sender_email is found, False otherwise.
        """
        if not sender_email:
            logger.error("Missing required parameter: sender_email.")
            return False

        try:
            logger.info(f"Attempting to check for replies from {sender_email} in inbox {self.reply_checker.email_address}")
            has_replied = self.reply_checker.has_replied(sender_email=sender_email)

            if has_replied:
                logger.info(f"Reply found from {sender_email}.")
            else:
                logger.info(f"No reply found from {sender_email}.")
            return has_replied
        except Exception as e:
            logger.error(f"An error occurred while checking for replies from {sender_email}: {e}", exc_info=True)
            return False

# Example of how this agent might be used (for testing or direct invocation)
if __name__ == '__main__':
    # Configure basic logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Attempting to initialize and use ReplyCheckingAgent for a test reply check...")

    # Load .env from the root directory for configuration
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if load_dotenv(dotenv_path, override=True):
        logger.info(f"Loaded .env file from {dotenv_path}")
    else:
        logger.warning(f".env file not found at {dotenv_path}. Reply checking might fail if config is not set.")

    try:
        agent = ReplyCheckingAgent()

        # Example usage:
        # Replace with an email address you want to check for replies from.
        # This email should ideally be one you've sent a test email to from the SENDER_EMAIL account,
        # and then replied to from that test_sender_email.
        test_sender_email_to_check = os.getenv("TEST_SENDER_REPLY_EMAIL") # Set this in your .env for testing

        if test_sender_email_to_check:
            logger.info(f"Checking for replies from: {test_sender_email_to_check}")
            reply_found = agent.check_reply_task(sender_email=test_sender_email_to_check)
            if reply_found:
                logger.info(f"Test reply check indicates a reply WAS FOUND from {test_sender_email_to_check}.")
            else:
                logger.info(f"Test reply check indicates NO REPLY was found from {test_sender_email_to_check}.")
        else:
            logger.warning("TEST_SENDER_REPLY_EMAIL not set in environment. Skipping test reply check.")

    except Exception as e:
        logger.error(f"Failed to run ReplyCheckingAgent example: {e}", exc_info=True)
