"""
Check for email replies using Gmail IMAP
"""

import imaplib
import email
import logging
from datetime import datetime, timedelta
import ssl

logger = logging.getLogger(__name__)


class ReplyChecker:
    def __init__(self, email_address, app_password):
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self._checked_cache = {}  # Cache to avoid repeated checks
        
    def has_replied(self, sender_email):
        """Check if a specific sender has replied"""
        # Check cache first
        if sender_email in self._checked_cache:
            cache_time, has_reply = self._checked_cache[sender_email]
            if datetime.now() - cache_time < timedelta(hours=1):
                return has_reply
                
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to Gmail IMAP
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=context) as mail:
                mail.login(self.email_address, self.app_password)
                mail.select('inbox')
                
                # Search for emails from this sender
                # Look for emails in the last 30 days to limit search
                date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
                search_criteria = f'(FROM "{sender_email}" SINCE {date_30_days_ago})'
                
                result, data = mail.search(None, search_criteria)
                
                if result == 'OK' and data[0]:
                    email_ids = data[0].split()
                    
                    # Check if any email is a reply (has Re: in subject or references our email)
                    for email_id in email_ids:
                        result, msg_data = mail.fetch(email_id, '(BODY[HEADER.FIELDS (SUBJECT IN-REPLY-TO REFERENCES)])')
                        if result == 'OK':
                            email_message = email.message_from_bytes(msg_data[0][1])
                            subject = email_message.get('Subject', '')
                            in_reply_to = email_message.get('In-Reply-To', '')
                            references = email_message.get('References', '')
                            
                            # Check if it's a reply
                            if 'Re:' in subject or in_reply_to or references:
                                logger.info(f"Found reply from {sender_email}")
                                self._checked_cache[sender_email] = (datetime.now(), True)
                                return True
                                
                # No reply found
                self._checked_cache[sender_email] = (datetime.now(), False)
                return False
                
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP error checking replies: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking reply from {sender_email}: {str(e)}")
            return False
            
    def get_all_replies(self):
        """Get all reply emails (for reporting purposes)"""
        replies = []
        
        try:
            context = ssl.create_default_context()
            
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=context) as mail:
                mail.login(self.email_address, self.app_password)
                mail.select('inbox')
                
                # Search for replies in the last 30 days
                date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
                search_criteria = f'(SINCE {date_30_days_ago})'
                
                result, data = mail.search(None, search_criteria)
                
                if result == 'OK' and data[0]:
                    email_ids = data[0].split()
                    
                    for email_id in email_ids[-100:]:  # Check last 100 emails
                        result, msg_data = mail.fetch(email_id, '(RFC822)')
                        if result == 'OK':
                            email_message = email.message_from_bytes(msg_data[0][1])
                            subject = email_message.get('Subject', '')
                            from_email = email.utils.parseaddr(email_message.get('From', ''))[1]
                            
                            # Check if it's a reply
                            if 'Re:' in subject or email_message.get('In-Reply-To'):
                                replies.append({
                                    'from': from_email,
                                    'subject': subject,
                                    'date': email_message.get('Date', '')
                                })
                                
                return replies
                
        except Exception as e:
            logger.error(f"Error getting all replies: {str(e)}")
            return []