"""
CSV Management Agent
This agent is responsible for reading from and writing to the CSV file that stores contact data
and email campaign progress, using the CSVHandler utility.
"""

import logging
import os
import sys
from typing import List, Dict, Optional

# Ensure the src directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from csv_handler import CSVHandler
from config import Config

logger = logging.getLogger(__name__)

class CSVManagementAgent:
    """
    Agent Instructions:
    -------------------
    This agent is tasked with managing contact data stored in a CSV file.
    You can load all contacts, retrieve a specific contact by email, update a contact's details,
    and save changes back to the CSV file.

    Available Tools:
    - `load_all_contacts_tool`: Loads and returns all contacts from the CSV.
    - `get_contact_by_email_tool`: Retrieves a specific contact using their email address.
    - `update_contact_details_tool`: Modifies the information for a specific contact and saves the CSV.
    - `add_new_contact_tool` (Optional): Adds a new contact to the CSV and saves.

    Workflow Examples:
    1. To get a contact:
       - Use `get_contact_by_email_tool` with the contact's email.
    2. To update a contact's status (e.g., mark 'reply_received'):
       - Use `get_contact_by_email_tool` to fetch the contact.
       - Modify the desired fields in the contact data.
       - Use `update_contact_details_tool` with the modified contact data.
    3. To load all contacts for processing:
       - Use `load_all_contacts_tool`.

    Constraints:
    - When updating a contact, ensure you provide the complete contact dictionary with changes.
    - The primary key for identifying contacts is their 'EMAIL' address.
    - Always handle data with care to avoid unintentional corruption of the CSV file.
      The underlying CSVHandler creates backups, but caution is advised.
    """

    def __init__(self):
        """
        Initializes the CSVManagementAgent.
        It sets up the CSVHandler using the CSV file path from the application configuration.
        """
        try:
            app_config = Config()
            # The CSVHandler expects the path to the CSV file.
            # config.csv_file already resolves to ../data/filename.csv
            self.csv_handler = CSVHandler(csv_file=app_config.csv_file) # Corrected argument name
            logger.info(f"CSVManagementAgent initialized successfully. Managing CSV: {app_config.csv_file}")
        except Exception as e:
            logger.error(f"Failed to initialize CSVManagementAgent: {e}")
            raise

    def load_all_contacts_task(self) -> List[Dict]:
        """
        Loads all contacts from the CSV file.

        Returns:
            A list of dictionaries, where each dictionary represents a contact.
            Returns an empty list if an error occurs or no contacts are found.
        """
        try:
            logger.info("Attempting to load all contacts from CSV.")
            contacts = self.csv_handler.load_contacts()
            logger.info(f"Successfully loaded {len(contacts)} contacts.")
            return contacts
        except Exception as e:
            logger.error(f"An error occurred while loading all contacts: {e}", exc_info=True)
            return []

    def get_contact_by_email_task(self, email: str) -> Optional[Dict]:
        """
        Retrieves a specific contact from the CSV file by their email address.

        Args:
            email: The email address of the contact to retrieve.

        Returns:
            A dictionary representing the contact if found, otherwise None.
        """
        if not email:
            logger.error("Missing required parameter: email for get_contact_by_email_task.")
            return None
        try:
            logger.info(f"Attempting to retrieve contact with email: {email}")
            contacts = self.csv_handler.load_contacts() # Consider optimizing if called frequently
            for contact in contacts:
                if contact.get('EMAIL', '').lower() == email.lower():
                    logger.info(f"Contact found for email: {email}")
                    return contact
            logger.info(f"No contact found with email: {email}")
            return None
        except Exception as e:
            logger.error(f"An error occurred while retrieving contact {email}: {e}", exc_info=True)
            return None

    def update_contact_task(self, updated_contact_data: Dict) -> bool:
        """
        Updates an existing contact's information in the CSV file.
        The contact is identified by the 'EMAIL' field in updated_contact_data.
        This method loads all contacts, finds the one to update, applies changes,
        and then saves all contacts back to the file.

        Args:
            updated_contact_data: A dictionary containing the full data for the contact,
                                 including the changes. Must include the 'EMAIL' field.

        Returns:
            True if the contact was successfully updated and saved, False otherwise.
        """
        email_to_update = updated_contact_data.get('EMAIL')
        if not email_to_update:
            logger.error("Missing 'EMAIL' field in updated_contact_data. Cannot update contact.")
            return False

        try:
            logger.info(f"Attempting to update contact with email: {email_to_update}")
            contacts = self.csv_handler.load_contacts()
            contact_found = False
            for i, contact in enumerate(contacts):
                if contact.get('EMAIL', '').lower() == email_to_update.lower():
                    contacts[i] = updated_contact_data # Replace with new data
                    contact_found = True
                    break

            if not contact_found:
                logger.warning(f"Contact with email {email_to_update} not found. Cannot update.")
                return False

            self.csv_handler.save_contacts(contacts)
            logger.info(f"Successfully updated contact {email_to_update} and saved CSV.")
            return True
        except Exception as e:
            logger.error(f"An error occurred while updating contact {email_to_update}: {e}", exc_info=True)
            return False

    def add_new_contact_task(self, new_contact_data: Dict) -> bool:
        """
        Adds a new contact to the CSV file.
        Checks if a contact with the same email already exists.

        Args:
            new_contact_data: A dictionary representing the new contact. Must include 'EMAIL'.

        Returns:
            True if the contact was successfully added and saved, False otherwise (e.g., if email exists).
        """
        email_to_add = new_contact_data.get('EMAIL')
        if not email_to_add:
            logger.error("Missing 'EMAIL' field in new_contact_data. Cannot add contact.")
            return False

        try:
            logger.info(f"Attempting to add new contact with email: {email_to_add}")
            contacts = self.csv_handler.load_contacts()

            for contact in contacts:
                if contact.get('EMAIL', '').lower() == email_to_add.lower():
                    logger.warning(f"Contact with email {email_to_add} already exists. Cannot add duplicate.")
                    return False

            contacts.append(new_contact_data)
            self.csv_handler.save_contacts(contacts)
            logger.info(f"Successfully added new contact {email_to_add} and saved CSV.")
            return True
        except Exception as e:
            logger.error(f"An error occurred while adding contact {email_to_add}: {e}", exc_info=True)
            return False

# Example of how this agent might be used
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Attempting to initialize and use CSVManagementAgent...")

    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if load_dotenv(dotenv_path, override=True):
        logger.info(f"Loaded .env file from {dotenv_path}")
    else:
        logger.warning(f".env file not found at {dotenv_path}. CSV path might be default or incorrect.")

    try:
        agent = CSVManagementAgent()

        # 1. Load all contacts
        logger.info("\n--- Loading all contacts ---")
        all_contacts = agent.load_all_contacts_task()
        if all_contacts:
            logger.info(f"Loaded {len(all_contacts)} contacts. First contact: {all_contacts[0] if all_contacts else 'N/A'}")

        # 2. Get a specific contact (assuming one exists from your test.csv or final.csv)
        # Replace 'john.doe@example.com' with an email you know is in your CSV
        test_email_to_get = "john.doe@example.com"
        # You might want to load this from .env or use a known email from your test data
        # For the default test.csv, one email is "jane.smith@example.com"
        # If using final.csv, ensure the email exists.

        # Let's try to use an email from the loaded contacts if possible
        if all_contacts:
            test_email_to_get = all_contacts[0].get("EMAIL", test_email_to_get)

        logger.info(f"\n--- Getting contact: {test_email_to_get} ---")
        contact = agent.get_contact_by_email_task(test_email_to_get)
        if contact:
            logger.info(f"Found contact: {contact}")

            # 3. Update a contact
            logger.info(f"\n--- Updating contact: {test_email_to_get} ---")
            original_description = contact.get('DESCRIPTION')
            contact['DESCRIPTION'] = "Updated by CSVManagementAgent"
            contact['reply_received'] = 'True' # Example update
            if agent.update_contact_task(contact):
                logger.info(f"Contact {test_email_to_get} updated. Verifying...")
                updated_contact = agent.get_contact_by_email_task(test_email_to_get)
                logger.info(f"Verified updated contact: {updated_contact}")
                # Revert for subsequent tests if needed
                # contact['DESCRIPTION'] = original_description
                # contact['reply_received'] = ''
                # agent.update_contact_task(contact)
            else:
                logger.error(f"Failed to update contact {test_email_to_get}")
        else:
            logger.warning(f"Could not find contact {test_email_to_get} to test update.")

        # 4. Add a new contact
        logger.info("\n--- Adding a new contact ---")
        new_contact_info = {
            'EMAIL': 'new.agent.test@example.com', 'FIRST_NAME': 'Agent', 'JOB_TITLE': 'Tester',
            'DESCRIPTION': 'Test contact added by CSVManagementAgent'
            # Add other required fields as per your CSVHandler.required_columns
        }
        # Ensure all required columns are present for the new contact
        for col in agent.csv_handler.required_columns:
            if col not in new_contact_info:
                new_contact_info[col] = f"Test {col}"


        if agent.add_new_contact_task(new_contact_info):
            logger.info(f"New contact {new_contact_info['EMAIL']} added. Verifying...")
            added_contact = agent.get_contact_by_email_task(new_contact_info['EMAIL'])
            logger.info(f"Verified added contact: {added_contact}")
        else:
            logger.error(f"Failed to add new contact {new_contact_info['EMAIL']}. It might already exist.")

    except Exception as e:
        logger.error(f"Failed to run CSVManagementAgent example: {e}", exc_info=True)

# End of file
