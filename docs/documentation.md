# Email Automation System Documentation

## Overview

This is a comprehensive email automation system designed for outreach campaigns with intelligent follow-up sequences. The system manages contact lists, personalizes email templates, tracks responses, and automates follow-up emails based on configurable time intervals.

## System Architecture

### Core Components

1. **EmailAutomation (`email_automation.py`)** - Main orchestrator
2. **Config (`config.py`)** - Configuration management
3. **CSVHandler (`csv_handler.py`)** - Contact data management
4. **EmailSender (`email_sender.py`)** - SMTP email delivery
5. **ReplyChecker (`reply_checker.py`)** - IMAP reply detection
6. **TemplateHandler (`template_handler.py`)** - HTML template processing

## How It Works

### 1. Configuration System (`config.py`)

The `Config` class manages all system settings through environment variables:

- **Email Settings**: Gmail credentials and SMTP configuration
- **Timing**: Follow-up intervals (default: 3 days between each)
- **Limits**: Daily send limits (default: 50 emails)
- **Send Window**: Operating hours (default: 9 AM - 5 PM)

Key features:
- Environment variable support with sensible defaults
- Built-in validation for required settings
- Time window checking for appropriate sending hours

### 2. Contact Management (`csv_handler.py`)

The `CSVHandler` class handles all contact data operations:

**Required CSV Columns:**
- `DESCRIPTION`, `JOB_TITLE`, `EMAIL`, `LINKEDIN_URL`
- `COMPANY_WEBSITE`, `LOCATION`, `PHONE_NUMBER`, `FIRST_NAME`

**Tracking Columns (auto-added):**
- `initial_sent_date`, `followup1_sent_date`, `followup2_sent_date`, `followup3_sent_date`
- `reply_received`, `last_email_type`

Key features:
- Automatic backup creation before saves
- Data validation and cleaning
- Company name extraction from website URLs
- Statistics generation for reporting

### 3. Email Delivery (`email_sender.py`)

The `EmailSender` class handles SMTP email delivery:

- **Gmail SMTP**: Uses Gmail's SMTP server with app passwords
- **Retry Logic**: 3 attempts with exponential backoff
- **Error Handling**: Specific handling for authentication and recipient errors
- **Security**: SSL/TLS encryption for all communications

### 4. Reply Detection (`reply_checker.py`)

The `ReplyChecker` class monitors for email responses:

- **IMAP Integration**: Connects to Gmail via secure IMAP
- **Smart Detection**: Identifies replies using subject lines, In-Reply-To headers, and References
- **Caching**: 1-hour cache to avoid redundant checks
- **Time-Limited Search**: Searches only last 30 days for performance

### 5. Template Processing (`template_handler.py`)

The `TemplateHandler` class personalizes HTML email templates:

**Supported Placeholder Formats:**
- `{FIRST_NAME}`, `{JOB_TITLE}`, `{COMPANY}`, `{LOCATION}`
- `[First Name]`, `[Job Title]` (bracket format)

Key features:
- HTML validation using BeautifulSoup
- Fallback values for missing data
- Plain text conversion capability
- Template existence validation

### 6. Main Automation Engine (`email_automation.py`)

The `EmailAutomation` class orchestrates the entire process:

## Email Flow Logic

### Decision Tree for Each Contact:

```
1. Load contact from CSV
2. Check if reply already received → Skip if yes
3. Check for new replies via IMAP → Mark and skip if found
4. Determine email type based on tracking:
   - No initial_sent_date → Send initial email
   - Initial sent + X days passed → Send follow-up 1
   - Follow-up 1 sent + Y days passed → Send follow-up 2
   - Follow-up 2 sent + Z days passed → Send follow-up 3
5. Personalize template with contact data
6. Send email (or simulate in dry-run mode)
7. Update tracking information
8. Save updated CSV
```

### Email Templates

The system uses four HTML templates:
- `first-email.html` - Initial outreach
- `follow-up-1.html` - First follow-up
- `follow-up-2.html` - Second follow-up  
- `follow-up-3.html` - Final follow-up

Each template supports personalization with contact data and company information.

## Usage

### Command Line Interface

```bash
# Normal operation
python email_automation.py

# Preview mode (no actual sending)
python email_automation.py --dry-run

# Send limited number of emails
python email_automation.py --limit 10

# Only check for replies
python email_automation.py --check-replies
```

### Environment Variables

Create a `.env` file with:
```
SENDER_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
CSV_FILE=final.csv
DAILY_SEND_LIMIT=50
SEND_START_HOUR=9
SEND_END_HOUR=17
FOLLOWUP1_DAYS=3
FOLLOWUP2_DAYS=3
FOLLOWUP3_DAYS=3
```

## Data Flow

1. **Initialization**: Load configuration and initialize all components
2. **Contact Loading**: Read contacts from CSV with validation
3. **Reply Checking**: Check for new replies via IMAP
4. **Email Processing**: For each contact:
   - Determine appropriate email type
   - Personalize template
   - Send email if within limits and time window
   - Update tracking data
5. **Data Persistence**: Save updated contact data with backups

## Security Features

- **Credential Management**: Environment variables for sensitive data
- **SSL/TLS**: Encrypted connections for both SMTP and IMAP
- **App Passwords**: Uses Gmail app passwords instead of main password
- **Data Backup**: Automatic backups before CSV modifications
- **Error Recovery**: Backup restoration on save failures

## Logging and Monitoring

The system provides comprehensive logging:
- Email send success/failure
- Reply detections
- Error conditions
- Processing statistics
- File operations

Logs are written to both `email_automation.log` and console output.

## Error Handling

- **Network Issues**: Automatic retry with exponential backoff
- **Authentication**: Clear error messages for credential problems
- **Data Validation**: Comprehensive validation of CSV data and email addresses
- **File Operations**: Backup and recovery for data safety
- **Template Issues**: Validation and helpful error messages

## Performance Considerations

- **Reply Caching**: 1-hour cache to avoid redundant IMAP checks
- **Time-Limited Searches**: IMAP searches limited to 30 days
- **Batch Processing**: Efficient CSV operations with single save
- **Connection Management**: Proper connection cleanup and resource management

## Testing Framework

The codebase includes comprehensive tests:
- `config_test.py` - Configuration validation tests
- `email_automation_test.py` - Main automation logic tests
- `monitor_test.py` - System monitoring tests
- `run_test.sh` - Test execution script

## File Structure

```
├── README.md               # Project overview
├── requirements.txt        # Python dependencies
├── src/                    # Source code
│   ├── email_automation.py # Main entry point
│   ├── config.py          # Configuration management
│   ├── csv_handler.py     # Contact data operations
│   ├── email_sender.py    # SMTP email delivery
│   ├── reply_checker.py   # IMAP reply detection
│   └── template_handler.py # HTML template processing
├── tests/                  # Test suite
│   ├── email_automation_test.py # Main automation tests
│   ├── config_test.py     # Configuration tests
│   ├── monitor_test.py    # System monitoring tests
│   └── run_test.sh        # Test execution script
├── templates/              # Email templates
│   ├── first-email.html   # Initial email template
│   ├── first-email.txt    # Plain text version
│   ├── follow-up-1.html   # First follow-up template
│   ├── follow-up-1.txt    # Plain text version
│   ├── follow-up-2.html   # Second follow-up template
│   ├── follow-up-2.txt    # Plain text version
│   ├── follow-up-3.html   # Final follow-up template
│   └── follow-up-3.txt    # Plain text version
├── data/                   # Data files and logs
│   ├── final.csv          # Production contact data
│   ├── test.csv           # Test contact data
│   └── *.log              # Application logs
└── docs/                   # Documentation
    ├── documentation.md    # This documentation
    └── prd.md             # Product requirements
```

## Dependencies

```
smtplib, imaplib (built-in)
email.mime (built-in)
csv, logging, datetime (built-in)
beautifulsoup4
python-dotenv
ssl, re, os (built-in)
```

## Best Practices

1. **Always run dry-run first** to preview emails
2. **Monitor logs** for delivery issues
3. **Respect sending limits** to avoid spam filters
4. **Keep templates updated** and personalized
5. **Regular reply checking** to maintain good sender reputation
6. **Backup CSV files** before major operations

This system provides a robust, scalable solution for automated email outreach while maintaining security, deliverability, and professional standards.