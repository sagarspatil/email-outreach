#!/usr/bin/env python3
"""
Email Automation Script
Main entry point for automated email outreach and follow-up campaigns,
now utilizing the OrchestratorAgent.
"""

import argparse
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables from parent directory FIRST
# This ensures that when src/config.py is loaded by agents, it sees these variables.
# The agents themselves also load .env, but this makes it explicit for the script entry point.
# The path is relative to this file (src/email_automation.py), so ../.env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path, override=True)


# It's good practice to ensure the src directory (parent of agents) is in PYTHONPATH
# This helps in resolving imports like `from agents.orchestrator_agent import OrchestratorAgent`
# especially when the script is run from the `src` directory or other locations.
# sys.path.insert(0, os.path.dirname(__file__)) # Add src directory to Python path - this is where email_automation.py is
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) # Add project root to Python path


try:
    from agents.orchestrator_agent import OrchestratorAgent
    # from config import Config # Not directly needed by main anymore, agents handle their config.
except ImportError as e:
    # This block helps diagnose import errors early.
    logging.basicConfig(level=logging.ERROR) # Ensure logging is configured for this error message
    logger_diag = logging.getLogger(__name__) # Use a local logger for diagnostics
    logger_diag.error(f"Failed to import OrchestratorAgent. Ensure PYTHONPATH is correct or run from project root. Error: {e}")
    logger_diag.error(f"Current sys.path: {sys.path}")
    logger_diag.error(f"Current working directory: {os.getcwd()}")
    agents_dir = os.path.join(os.path.dirname(__file__), "agents")
    if os.path.exists(agents_dir):
        logger_diag.error(f"Contents of {agents_dir}: {os.listdir(agents_dir)}")
    else:
        logger_diag.error(f"Directory not found: {agents_dir}")
    sys.exit(1)


# Configure logging for the main script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'), # Log file in CWD
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Email Automation Script using OrchestratorAgent')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview what would be sent without actually sending')
    parser.add_argument('--limit', type=int, help='Send only N emails')
    parser.add_argument('--check-replies', action='store_true',
                       help='Only check for replies and update CSV')
    
    args = parser.parse_args()
    
    try:
        logger.info("Initializing OrchestratorAgent...")
        orchestrator = OrchestratorAgent() # Agent loads its own config internally

        if args.check_replies:
            logger.info("Running in --check-replies mode.")
            orchestrator.perform_global_reply_check_task()
        else:
            logger.info(f"Starting email campaign with dry_run={args.dry_run}, limit={args.limit}.")
            orchestrator.run_email_campaign_task(
                dry_run=args.dry_run,
                limit=args.limit
            )
        logger.info("Email automation script finished.")

    except Exception as e:
        logger.error(f"A fatal error occurred in main: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    # Ensure .env is loaded before any agent tries to access Config.
    # This is done at the top of the file.
    # A check here can be useful for immediate feedback if running the script directly.
    if not os.getenv('GMAIL_APP_PASSWORD'):
         # Use the main logger here if it's already configured, or a print statement if very early.
         print("WARNING: GMAIL_APP_PASSWORD not found in environment. Ensure .env is loaded and configured.", file=sys.stderr)

    main()
