# Email Automation Script

A simple Python script to automate email outreach and follow-up campaigns using CSV data and HTML templates.

## Features

- **Automated Email Sending**: Send personalized initial and follow-up emails
- **Smart Reply Detection**: Automatically stops follow-ups when replies are detected
- **CSV-based Contact Management**: Track all email activity in your CSV file
- **Template Personalization**: Use placeholders to customize emails for each recipient
- **Configurable Time Intervals**: Set custom delays between follow-ups
- **Rich CLI Interface**: Beautiful progress display with detailed status updates
- **Command Line Options**: Dry-run, limit, and reply-check modes

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd email-automation

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your Gmail App Password:

```
GMAIL_APP_PASSWORD=your-16-character-app-password
```

To get a Gmail App Password:
1. Go to https://myaccount.google.com/security
2. Enable 2-factor authentication
3. Search for "App passwords"
4. Generate a new app password for "Mail"

### 3. Prepare Your Data

Create a `final.csv` file with these columns:
```
DESCRIPTION,JOB_TITLE,EMAIL,LINKEDIN_URL,COMPANY_WEBSITE,LOCATION,PHONE_NUMBER,FIRST_NAME
```

Example:
```csv
"Software Engineer","Senior Developer","john.doe@example.com","https://linkedin.com/in/johndoe","https://example.com","San Francisco, CA","","John"
```

### 4. Email Templates

The following HTML email templates are included:
- `first-email.html` - Initial outreach email
- `follow-up-1.html` - First follow-up (sent after 3 days)
- `follow-up-2.html` - Second follow-up (sent after 5 days)
- `follow-up-3.html` - Third follow-up (sent after 7 days)

Templates use these placeholders:
- `{FIRST_NAME}` - Recipient's first name
- `{JOB_TITLE}` - Recipient's job title

### 5. Run the Script

```bash
# Dry run - preview what would be sent
python email_automation.py --dry-run

# Send emails with a limit
python email_automation.py --limit 5

# Check for replies only
python email_automation.py --check-replies

# Normal run
python email_automation.py
```

## How It Works

1. **Initial Email**: Sent to contacts who haven't been emailed yet
2. **Follow-ups**: Sent based on configured intervals:
   - Follow-up 1: After 3 days
   - Follow-up 2: After 5 days from follow-up 1
   - Follow-up 3: After 7 days from follow-up 2
3. **Reply Detection**: Checks IMAP for replies before sending follow-ups
4. **Tracking**: Updates CSV with sent dates and reply status
5. **Rich Progress Display**: Shows detailed progress with contact names, email types, and status

## CSV Tracking Columns

The script automatically adds these columns to track progress:
- `initial_sent_date` - When first email was sent
- `followup1_sent_date` - When follow-up 1 was sent
- `followup2_sent_date` - When follow-up 2 was sent
- `followup3_sent_date` - When follow-up 3 was sent
- `reply_received` - True if recipient replied
- `last_email_type` - Type of last email sent

## Configuration Options

Edit `.env` to customize:

```bash
# Email settings
SENDER_EMAIL=advayaholistic@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Follow-up intervals (days)
FOLLOWUP1_DAYS=3
FOLLOWUP2_DAYS=5
FOLLOWUP3_DAYS=7

# Send limits
DAILY_SEND_LIMIT=50

# Send time window (24-hour format) - Optional
# If not set, emails can be sent at any time
SEND_START_HOUR=9
SEND_END_HOUR=17
```

## Logging

All activity is logged to:
- Console output with rich formatting
- `email_automation.log` file for detailed debugging

## Security Notes

- Never commit your `.env` file
- Use Gmail App Passwords, not your regular password
- The script creates automatic backups of your CSV before updates

## Troubleshooting

### Gmail Authentication Failed
- Ensure 2-factor authentication is enabled
- Use a 16-character App Password, not your regular password
- Check that "Less secure app access" is not needed (App Passwords bypass this)

### No Emails Sending
- If using send time window, check if you're within the configured hours
- Verify email addresses are valid
- Check the log file for errors
- Ensure follow-up intervals have passed (3, 5, or 7 days)

### Templates Not Found
- Ensure all 4 template files exist in the project directory
- Check file names match exactly (including .html extension)

## License

This project is for personal use as specified in the requirements.