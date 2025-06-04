#!/bin/bash

echo "Email Automation Test Runner"
echo "============================"
echo ""
echo "This test will:"
echo "1. Send initial emails immediately"
echo "2. Send follow-up 1 after 2 minutes"
echo "3. Send follow-up 2 after 3 more minutes (5 total)"
echo "4. Send follow-up 3 after 5 more minutes (10 total)"
echo ""
echo "Make sure you have added your Gmail app password to .env.test"
echo ""

# Check if .env.test exists
if [ ! -f .env.test ]; then
    echo "ERROR: .env.test file not found!"
    exit 1
fi

# Check if Gmail password is set
if ! grep -q "GMAIL_APP_PASSWORD=.." .env.test; then
    echo "ERROR: Please add your Gmail app password to .env.test"
    echo "Edit .env.test and replace 'your-gmail-app-password-here' with your actual password"
    exit 1
fi

echo "Starting test..."
echo ""

# Run the test in a loop to check for follow-ups
echo "Running initial email send..."
python email_automation_test.py

echo ""
echo "Waiting 2 minutes for follow-up 1..."
sleep 120

echo "Checking for follow-up 1..."
python email_automation_test.py

echo ""
echo "Waiting 3 minutes for follow-up 2..."
sleep 180

echo "Checking for follow-up 2..."
python email_automation_test.py

echo ""
echo "Waiting 5 minutes for follow-up 3..."
sleep 300

echo "Checking for follow-up 3..."
python email_automation_test.py

echo ""
echo "Test complete! Check test.csv for results."