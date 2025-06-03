# Email Automation Script - Product Requirements Document

## Project Overview
A simple Python script to automate email outreach and follow-up campaigns using CSV data and HTML templates.

## Core Requirements

### 1. Input Data Source
- **File**: `final.csv`
- **Required columns** (in order):
  - DESCRIPTION
  - JOB_TITLE
  - EMAIL
  - LINKEDIN_URL
  - COMPANY_WEBSITE
  - LOCATION
  - PHONE_NUMBER (can be empty)
  - FIRST_NAME

### 2. Email Templates
- **First email**: `first.html`
- **Follow-up 1**: `follow-up-1.html`
- **Follow-up 2**: `follow-up-2.html`
- **Follow-up 3**: `follow-up-3.html`

### 3. Email Configuration
- **Sender**: advayaholistic@gmail.com
- **Auth**: Gmail App Password (to be provided)
- **SMTP**: Gmail SMTP server

### 4. Core Functionality

#### 4.1 Email Sending Logic
- Send initial email using `first.html` template
- Track sent date for each email
- Schedule follow-ups based on time intervals:
  - Follow-up 1: X days after initial email
  - Follow-up 2: Y days after follow-up 1
  - Follow-up 3: Z days after follow-up 2

#### 4.2 Reply Detection
- Check for replies before sending follow-ups
- Stop follow-up sequence if reply detected
- Mark contact as "replied" in tracking

#### 4.3 Tracking System
- Add tracking columns to CSV:
  - `initial_sent_date`
  - `followup1_sent_date`
  - `followup2_sent_date`
  - `followup3_sent_date`
  - `reply_received`
  - `last_email_type`

### 5. Template Personalization
- Replace placeholders in HTML templates:
  - `{FIRST_NAME}` → Contact's first name
  - `{JOB_TITLE}` → Contact's job title
  - `{COMPANY}` → Extract from COMPANY_WEBSITE
  - Any other relevant fields from CSV

### 6. Execution Flow
1. Load CSV data
2. For each contact:
   - Check if initial email sent
   - If not, send initial email and update tracking
   - If yes, check for replies
   - If no reply, check if follow-up due
   - Send appropriate follow-up if due
3. Save updated CSV with tracking info

### 7. Configuration Options
- **Time intervals** (configurable):
  - Days between initial and follow-up 1
  - Days between follow-ups
- **Daily send limit** (to avoid spam filters)
- **Send time window** (e.g., 9 AM - 5 PM)

### 8. Error Handling
- Invalid email addresses
- Failed sends (retry logic)
- Missing required fields
- Gmail authentication errors

### 9. Logging
- Log file with:
  - Emails sent successfully
  - Failed attempts
  - Reply detections
  - Errors encountered

### 10. Simple CLI Interface
```bash
python email_automation.py [options]
  --dry-run: Preview what would be sent
  --limit N: Send only N emails
  --check-replies: Only check for replies
```

## Technical Stack
- **Language**: Python 3.x
- **Email**: smtplib, email.mime
- **Reply checking**: imaplib
- **CSV handling**: csv module or pandas
- **HTML parsing**: Built-in or BeautifulSoup
- **Scheduling**: datetime module

## Security Considerations
- Store Gmail App Password securely (environment variable)
- Don't commit credentials to repository
- Handle personal data responsibly

## Future Enhancements (Out of Scope for MVP)
- Web dashboard
- A/B testing templates
- Advanced analytics
- Multiple sender accounts
- Unsubscribe handling

## Success Metrics
- Emails sent successfully
- Reply rate tracking
- No spam complaints
- Reliable follow-up scheduling