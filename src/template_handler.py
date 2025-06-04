"""
HTML template processing and personalization
"""

import logging
import os
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TemplateHandler:
    def __init__(self):
        # Match both {PLACEHOLDER} and [Placeholder] formats
        self.placeholder_pattern = re.compile(r'\{([A-Z_]+)\}')
        self.bracket_pattern = re.compile(r'\[([A-Za-z\s]+)\]')
        # Match {{FirstName}} double brace format
        self.double_brace_pattern = re.compile(r'\{\{([A-Za-z]+)\}\}')
        
    def personalize_template(self, template_file, contact_data):
        """Personalize template with contact data (works for both HTML and text)"""
        try:
            # Read template file
            with open(template_file, 'r', encoding='utf-8') as file:
                template_content = file.read()
                
            # Replace placeholders - all formats
            personalized_content = self._replace_placeholders(template_content, contact_data)
            personalized_content = self._replace_bracket_placeholders(personalized_content, contact_data)
            personalized_content = self._replace_double_brace_placeholders(personalized_content, contact_data)
            
            # Validate HTML only if it's an HTML file
            if template_file.endswith('.html'):
                self._validate_html(personalized_content)
            
            return personalized_content
            
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_file}")
            raise
        except Exception as e:
            logger.error(f"Error personalizing template: {str(e)}")
            raise
            
    def _replace_placeholders(self, template, data):
        """Replace all placeholders in template with data"""
        def replace_match(match):
            placeholder = match.group(1)
            
            # Map common placeholders
            if placeholder == 'FIRST_NAME':
                return data.get('FIRST_NAME', 'there')
            elif placeholder == 'JOB_TITLE':
                return data.get('JOB_TITLE', 'Professional')
            elif placeholder == 'COMPANY':
                return data.get('COMPANY', data.get('COMPANY_WEBSITE', 'your company'))
            elif placeholder == 'LOCATION':
                return data.get('LOCATION', '')
            elif placeholder in data:
                return data[placeholder]
            else:
                logger.warning(f"Placeholder {{{placeholder}}} not found in data")
                return match.group(0)  # Keep original placeholder
                
        return self.placeholder_pattern.sub(replace_match, template)
        
    def _replace_bracket_placeholders(self, template, data):
        """Replace [First Name] style placeholders"""
        def replace_match(match):
            placeholder = match.group(1).strip()
            
            # Map bracket placeholders to data fields
            if placeholder.lower() == 'first name':
                return data.get('FIRST_NAME', 'there')
            elif placeholder.lower() == 'job title':
                return data.get('JOB_TITLE', 'Professional')
            else:
                logger.warning(f"Placeholder [{placeholder}] not found in data")
                return match.group(0)  # Keep original placeholder
                
        return self.bracket_pattern.sub(replace_match, template)
        
    def _replace_double_brace_placeholders(self, template, data):
        """Replace {{FirstName}} style placeholders"""
        def replace_match(match):
            placeholder = match.group(1).strip()
            
            # Map double brace placeholders to data fields
            if placeholder.lower() == 'firstname':
                return data.get('FIRST_NAME', 'there')
            elif placeholder.lower() == 'jobtitle':
                return data.get('JOB_TITLE', 'Professional')
            else:
                logger.warning(f"Placeholder {{{{{placeholder}}}}} not found in data")
                return match.group(0)  # Keep original placeholder
                
        return self.double_brace_pattern.sub(replace_match, template)
        
    def _validate_html(self, html_content):
        """Basic HTML validation"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check for common issues
            if not soup.find():
                raise ValueError("Invalid HTML: No content found")
                
            # Check for unclosed tags (BeautifulSoup auto-fixes these)
            if str(soup) != html_content:
                logger.warning("HTML was auto-corrected by parser")
                
        except Exception as e:
            logger.error(f"HTML validation error: {str(e)}")
            raise
            
    def create_plain_text_version(self, html_content):
        """Create plain text version from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
                
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error creating plain text version: {str(e)}")
            return ""
            
    def get_available_templates(self):
        """List all available template files"""
        templates = []
        template_files = ['first-email.html', 'follow-up-1.html', 'follow-up-2.html', 'follow-up-3.html']
        
        for template_file in template_files:
            if os.path.exists(template_file):
                templates.append(template_file)
                
        return templates
        
    def validate_all_templates(self):
        """Validate all template files exist and are valid"""
        required_templates = ['first-email.html', 'follow-up-1.html', 'follow-up-2.html', 'follow-up-3.html']
        missing_templates = []
        invalid_templates = []
        
        for template_file in required_templates:
            if not os.path.exists(template_file):
                missing_templates.append(template_file)
            else:
                try:
                    with open(template_file, 'r', encoding='utf-8') as file:
                        content = file.read()
                        self._validate_html(content)
                except Exception as e:
                    invalid_templates.append((template_file, str(e)))
                    
        if missing_templates:
            logger.error(f"Missing templates: {missing_templates}")
            
        if invalid_templates:
            logger.error(f"Invalid templates: {invalid_templates}")
            
        return len(missing_templates) == 0 and len(invalid_templates) == 0