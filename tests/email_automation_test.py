import unittest
from unittest.mock import MagicMock, patch, call
import os
import sys
from datetime import datetime, timedelta

# Adjust path to import OrchestratorAgent and other necessary components from src
# This adds the 'src' directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# We need to be able to import from agents package correctly
# If 'src' is in sys.path, then 'from agents.orchestrator_agent...' should work.
# Ensure OrchestratorAgent and other dependencies can be found.
try:
    from agents.orchestrator_agent import OrchestratorAgent
    from template_handler import TemplateHandler # Real TemplateHandler is in src/
except ImportError as e:
    print(f"Error importing modules for test: {e}")
    print(f"Sys.path: {sys.path}")
    print(f"CWD: {os.getcwd()}")
    # Attempt to list files in src/agents to help debug
    src_agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'agents'))
    if os.path.exists(src_agents_dir):
        print(f"Contents of {src_agents_dir}: {os.listdir(src_agents_dir)}")
    else:
        print(f"Directory not found: {src_agents_dir}")
    raise


# Use a simplified test config or mock config values directly in tests
class TestConfigForOrchestrator: # Renamed to avoid potential clash if AppConfig was also named TestConfig
    def __init__(self):
        self.sender_email = "test_sender@example.com"
        self.gmail_app_password = "test_password"
        # This path is relative to project root if Orchestrator/CSVHandler uses it that way
        self.csv_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_data', 'test_contacts.csv'))
        self.followup1_days = 1
        self.followup2_days = 2
        self.followup3_days = 3
        self.email_delay_seconds = 0

class TestOrchestratorAgent(unittest.TestCase):

    def setUp(self):
        self.mock_csv_agent = MagicMock(name='mock_csv_agent')
        self.mock_email_agent = MagicMock(name='mock_email_agent')
        self.mock_reply_agent = MagicMock(name='mock_reply_agent')

        # Patch the agent constructors within OrchestratorAgent's scope
        self.patcher_csv_agent = patch('agents.orchestrator_agent.CSVManagementAgent', return_value=self.mock_csv_agent)
        self.patcher_email_agent = patch('agents.orchestrator_agent.EmailSendingAgent', return_value=self.mock_email_agent)
        self.patcher_reply_agent = patch('agents.orchestrator_agent.ReplyCheckingAgent', return_value=self.mock_reply_agent)

        self.mock_csv_constructor = self.patcher_csv_agent.start()
        self.mock_email_constructor = self.patcher_email_agent.start()
        self.mock_reply_constructor = self.patcher_reply_agent.start()

        self.patcher_config = patch('agents.orchestrator_agent.Config', TestConfigForOrchestrator)
        self.mock_config_constructor = self.patcher_config.start()
        
        self.orchestrator = OrchestratorAgent()
        # The orchestrator uses a real TemplateHandler by default. This is fine.

    def tearDown(self):
        self.patcher_csv_agent.stop()
        self.patcher_email_agent.stop()
        self.patcher_reply_agent.stop()
        self.patcher_config.stop()

    def _create_sample_contact(self, email, initial_sent_date=None, followup1_sent_date=None,
                               followup2_sent_date=None, followup3_sent_date=None,
                               reply_received=None, first_name="TestName"): # Ensure a distinct name
        contact = {
            'EMAIL': email, 'FIRST_NAME': first_name, 'JOB_TITLE': 'Tester',
            'initial_sent_date': initial_sent_date,
            'followup1_sent_date': followup1_sent_date,
            'followup2_sent_date': followup2_sent_date,
            'followup3_sent_date': followup3_sent_date,
            'reply_received': str(reply_received) if reply_received is not None else '', # Ensure string like CSV
            'COMPANY': 'TestCorp', 'LINKEDIN_URL': '', 'COMPANY_WEBSITE': '',
            'LOCATION': '', 'PHONE_NUMBER': '', 'DESCRIPTION': 'Sample Description'
        }
        return contact

    def test_run_campaign_initial_email(self):
        contact1 = self._create_sample_contact("contact1@example.com")
        self.mock_csv_agent.load_all_contacts_task.return_value = [contact1]
        self.mock_reply_agent.check_reply_task.return_value = False
        self.mock_email_agent.send_email_task.return_value = True

        self.orchestrator.run_email_campaign_task(dry_run=False, limit=1)

        self.mock_csv_agent.load_all_contacts_task.assert_called_once()
        self.mock_reply_agent.check_reply_task.assert_called_with(sender_email="contact1@example.com")
        self.mock_email_agent.send_email_task.assert_called_once()

        args, kwargs = self.mock_email_agent.send_email_task.call_args
        self.assertEqual(kwargs['recipient_email'], "contact1@example.com")
        self.assertIn("Quick question", kwargs['subject'])
        self.assertIn(contact1['FIRST_NAME'], kwargs['html_content'])

        self.mock_csv_agent.update_contact_task.assert_called_once()
        updated_contact_arg = self.mock_csv_agent.update_contact_task.call_args[0][0]
        self.assertEqual(updated_contact_arg['last_email_type'], 'initial')
        self.assertIsNotNone(updated_contact_arg['initial_sent_date'])

    def test_run_campaign_followup1_due(self):
        # Orchestrator's config uses followup1_days = 1
        initial_sent_time = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        contact1 = self._create_sample_contact("contact2@example.com", initial_sent_date=initial_sent_time)

        self.mock_csv_agent.load_all_contacts_task.return_value = [contact1]
        self.mock_reply_agent.check_reply_task.return_value = False
        self.mock_email_agent.send_email_task.return_value = True

        self.orchestrator.run_email_campaign_task(dry_run=False, limit=1)

        self.mock_reply_agent.check_reply_task.assert_called_with(sender_email="contact2@example.com")
        self.mock_email_agent.send_email_task.assert_called_once()
        args, kwargs = self.mock_email_agent.send_email_task.call_args
        self.assertIn("Did my invite get lost", kwargs['subject'])

        self.mock_csv_agent.update_contact_task.assert_called_once()
        updated_contact_arg = self.mock_csv_agent.update_contact_task.call_args[0][0]
        self.assertEqual(updated_contact_arg['last_email_type'], 'followup1')
        self.assertIsNotNone(updated_contact_arg['followup1_sent_date'])

    def test_run_campaign_dry_run(self):
        contact1 = self._create_sample_contact("contact_dry@example.com")
        self.mock_csv_agent.load_all_contacts_task.return_value = [contact1]
        self.mock_reply_agent.check_reply_task.return_value = False

        self.orchestrator.run_email_campaign_task(dry_run=True, limit=1)

        self.mock_email_agent.send_email_task.assert_not_called()
        self.mock_csv_agent.update_contact_task.assert_called_once()
        updated_contact_arg = self.mock_csv_agent.update_contact_task.call_args[0][0]
        self.assertEqual(updated_contact_arg['last_email_type'], 'initial')
        self.assertIsNotNone(updated_contact_arg['initial_sent_date'])

    def test_run_campaign_limit_respected(self):
        contact1 = self._create_sample_contact("c1@example.com")
        contact2 = self._create_sample_contact("c2@example.com")
        self.mock_csv_agent.load_all_contacts_task.return_value = [contact1, contact2]
        self.mock_reply_agent.check_reply_task.return_value = False
        self.mock_email_agent.send_email_task.return_value = True

        self.orchestrator.run_email_campaign_task(dry_run=False, limit=1)

        self.mock_email_agent.send_email_task.assert_called_once()
        self.mock_csv_agent.update_contact_task.assert_called_once()

    def test_run_campaign_reply_received_skips_contact(self):
        contact1 = self._create_sample_contact("replied@example.com", reply_received='True')
        contact2 = self._create_sample_contact("not_replied@example.com")
        
        self.mock_csv_agent.load_all_contacts_task.return_value = [contact1, contact2]
        self.mock_reply_agent.check_reply_task.return_value = False
        self.mock_email_agent.send_email_task.return_value = True

        self.orchestrator.run_email_campaign_task(dry_run=False, limit=2)

        self.mock_reply_agent.check_reply_task.assert_called_once_with(sender_email="not_replied@example.com")
        self.mock_email_agent.send_email_task.assert_called_once_with(
            recipient_email="not_replied@example.com",
            subject=unittest.mock.ANY,
            html_content=unittest.mock.ANY,
            text_content=unittest.mock.ANY
        )
        self.mock_csv_agent.update_contact_task.assert_called_once()

    def test_perform_global_reply_check_task(self):
        contact_no_reply = self._create_sample_contact("check_no_reply@example.com", reply_received='False') # Explicitly False
        contact_has_reply_pending_check = self._create_sample_contact("check_has_reply@example.com")
        contact_already_marked_replied = self._create_sample_contact("already_replied@example.com", reply_received='True')
        
        self.mock_csv_agent.load_all_contacts_task.return_value = [
            contact_no_reply, contact_has_reply_pending_check, contact_already_marked_replied
        ]
        
        def side_effect_check_reply(sender_email):
            return sender_email == "check_has_reply@example.com"
        self.mock_reply_agent.check_reply_task.side_effect = side_effect_check_reply

        self.orchestrator.perform_global_reply_check_task()

        self.mock_csv_agent.load_all_contacts_task.assert_called_once()

        self.assertEqual(self.mock_reply_agent.check_reply_task.call_count, 2)
        self.mock_reply_agent.check_reply_task.assert_any_call(sender_email="check_no_reply@example.com")
        self.mock_reply_agent.check_reply_task.assert_any_call(sender_email="check_has_reply@example.com")
        # No call for "already_replied@example.com"

        self.mock_csv_agent.update_contact_task.assert_called_once()
        updated_contact_arg = self.mock_csv_agent.update_contact_task.call_args[0][0]
        self.assertEqual(updated_contact_arg['EMAIL'], "check_has_reply@example.com")
        self.assertEqual(updated_contact_arg['reply_received'], 'True')

if __name__ == '__main__':
    # Create a dummy test_contacts.csv if it doesn't exist, for TemplateHandler path checks
    # The tests themselves mock CSV data, but TemplateHandler might be instantiated
    # and try to resolve paths relative to a CSV file if not careful.
    # However, OrchestratorAgent uses TemplateHandler independently of CSV path.
    # Template paths like 'templates/first-email.html' are resolved from CWD.

    # To run tests: python -m unittest tests.email_automation_test
    # Or if this file is executed directly:
    unittest.main(verbosity=2)
