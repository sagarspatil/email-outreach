import pandas as pd
from datetime import datetime, timedelta

# Load the CSV
df = pd.read_csv('../data/final_clean.csv')

# Current time
now = datetime.now()

# Count statistics
total_contacts = len(df)
initial_sent = df['initial_sent_date'].notna().sum()
replies_received = df['reply_received'].sum() if 'reply_received' in df.columns else 0

# Check who needs follow-up 1
needs_followup1 = 0
eligible_for_followup1 = []

for idx, row in df.iterrows():
    if pd.notna(row.get('initial_sent_date')) and pd.isna(row.get('followup1_sent_date')):
        # Check if they haven't replied
        if row.get('reply_received', False) != True:
            initial_date = pd.to_datetime(row['initial_sent_date'])
            days_since_initial = (now - initial_date).days
            if days_since_initial >= 3:
                needs_followup1 += 1
                eligible_for_followup1.append({
                    'email': row['EMAIL'],
                    'name': row.get('FIRST_NAME', 'Unknown'),
                    'days_since_initial': days_since_initial
                })

print(f"Email Campaign Status:")
print(f"=====================")
print(f"Total contacts: {total_contacts}")
print(f"Initial emails sent: {initial_sent}")
print(f"Replies received: {replies_received}")
print(f"Contacts needing follow-up 1: {needs_followup1}")
print(f"\nFirst 10 contacts who need follow-up 1:")
for i, contact in enumerate(eligible_for_followup1[:10]):
    print(f"{i+1}. {contact['name']} ({contact['email']}) - {contact['days_since_initial']} days since initial email")