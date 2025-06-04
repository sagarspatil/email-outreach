# Google Sheets Integration Plan

## Overview
Replace the current local CSV file handling with Google Sheets integration to enable real-time data access and collaborative data management.

**Target Sheet**: https://docs.google.com/spreadsheets/d/1fZVHJ7Qyiz5KFABIK05aYamU39wKpAhSGzEClau0SDI/edit?gid=625326026
**Sheet Name**: main
**Columns**: DESCRIPTION, JOB TITLE, EMAIL, LINKEDIN_URL, COMPANY_WEBSITE, LOCATION, PHONE_NUMBER, FIRST_NAME

## Main Tasks

### 1. Project Setup and Dependencies
- **1.1** Create new branch `google-sheets-integration`
- **1.2** Add required Python packages to requirements.txt
  - `gspread` (recommended for simplicity)
  - `google-auth` and `google-auth-oauthlib` (for authentication)
  - Alternative: `google-api-python-client` with `pandas`
- **1.3** Update project documentation

### 2. Authentication Setup
- **2.1** Create Google Cloud Project (if not exists)
- **2.2** Enable Google Sheets API
- **2.3** Create Service Account credentials
- **2.4** Download JSON credentials file
- **2.5** Share Google Sheet with service account email
- **2.6** Implement secure credential handling
  - Store credentials path in environment variable
  - Add credentials file to .gitignore
  - Create .env.example with required variables

### 3. Google Sheets Handler Implementation
- **3.1** Create new module `src/sheets_handler.py`
- **3.2** Implement authentication function
- **3.3** Implement sheet connection function
- **3.4** Implement data reading functions
  - Read all data
  - Read specific ranges
  - Handle column mapping
- **3.5** Implement data validation
  - Verify required columns exist
  - Handle missing or malformed data
- **3.6** Add error handling and logging

### 4. CSV Handler Migration
- **4.1** Analyze current `csv_handler.py` functionality
- **4.2** Create abstraction layer for data source
- **4.3** Update existing functions to work with Sheets data
- **4.4** Maintain backward compatibility (optional)
- **4.5** Update data processing pipeline

### 5. Configuration Updates
- **5.1** Update `config.py` with Sheets-related settings
- **5.2** Add environment variables for:
  - Google Sheets credentials path
  - Spreadsheet ID
  - Sheet name
  - Column mappings (if needed)

### 6. Integration and Testing
- **6.1** Update email automation to use Sheets handler
- **6.2** Test data reading functionality
- **6.3** Test email processing with Sheets data
- **6.4** Create unit tests for new functionality
- **6.5** Test error scenarios (network issues, permission errors)

### 7. Documentation and Cleanup
- **7.1** Update README with setup instructions
- **7.2** Document authentication process
- **7.3** Update existing documentation
- **7.4** Remove or archive old CSV-related code
- **7.5** Clean up unused dependencies

## Technical Approach

### Recommended Library: gspread
**Pros:**
- Simple, intuitive API
- Built specifically for Google Sheets
- Good documentation and community support
- Handles authentication seamlessly

**Cons:**
- Less flexible than google-api-python-client
- Fewer advanced features

### Authentication Strategy: Service Account
**Pros:**
- No user interaction required
- Suitable for automation
- More secure for server applications

**Steps:**
1. Create service account in Google Cloud Console
2. Generate JSON key file
3. Share sheet with service account email
4. Use credentials in application

### Data Processing Approach
```python
# Pseudo-code structure
class SheetsHandler:
    def __init__(self, credentials_path, sheet_id, sheet_name):
        # Initialize connection
        
    def get_all_data(self):
        # Return list of dictionaries with proper column mapping
        
    def validate_data(self, data):
        # Ensure required fields are present
        
    def process_contacts(self):
        # Replace current CSV processing logic
```

## Potential Challenges and Solutions

### 1. Rate Limiting
**Challenge**: Google Sheets API has rate limits
**Solution**: 
- Implement exponential backoff
- Cache data locally when appropriate
- Batch operations when possible

### 2. Network Connectivity
**Challenge**: Requires internet connection
**Solution**:
- Implement proper error handling
- Consider fallback mechanisms
- Add retry logic with timeouts

### 3. Data Consistency
**Challenge**: Sheet data can change between reads
**Solution**:
- Read all required data at once
- Implement data validation
- Handle schema changes gracefully

### 4. Security
**Challenge**: Protecting API credentials
**Solution**:
- Use environment variables
- Never commit credentials to version control
- Implement proper file permissions

### 5. Performance
**Challenge**: API calls slower than local file access
**Solution**:
- Minimize API calls
- Implement smart caching
- Read data in appropriate batch sizes

## Environment Variables Required
```
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=1fZVHJ7Qyiz5KFABIK05aYamU39wKpAhSGzEClau0SDI
GOOGLE_SHEETS_SHEET_NAME=main
```

## Success Criteria
- [ ] Email automation works seamlessly with Google Sheets data
- [ ] No loss of existing functionality
- [ ] Proper error handling for all edge cases
- [ ] Clear documentation for setup and usage
- [ ] Secure credential management
- [ ] Comprehensive testing of integration

## Timeline Estimate
- Setup and Dependencies: 30 minutes
- Authentication Setup: 45 minutes
- Core Implementation: 2-3 hours
- Integration and Testing: 1-2 hours
- Documentation: 30 minutes

**Total: 4-6 hours**