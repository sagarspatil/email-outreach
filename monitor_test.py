#!/usr/bin/env python3
"""
Monitor the test email automation progress
"""

import time
import csv
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()


def read_csv_status():
    """Read current status from test.csv"""
    contacts = []
    try:
        with open('test.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                contacts.append(row)
    except Exception as e:
        console.print(f"[red]Error reading CSV: {e}[/red]")
    return contacts


def create_status_table(contacts):
    """Create a status table showing email progress"""
    table = Table(title=f"Email Test Progress - {datetime.now().strftime('%H:%M:%S')}")
    
    table.add_column("Email", style="cyan")
    table.add_column("Initial", style="green")
    table.add_column("Follow-up 1\n(2 min)", style="yellow")
    table.add_column("Follow-up 2\n(+3 min)", style="yellow")
    table.add_column("Follow-up 3\n(+5 min)", style="yellow")
    table.add_column("Reply", style="magenta")
    
    for contact in contacts:
        email = contact.get('EMAIL', '')
        initial = "✓" if contact.get('initial_sent_date') else "⏳"
        fu1 = "✓" if contact.get('followup1_sent_date') else "⏳"
        fu2 = "✓" if contact.get('followup2_sent_date') else "⏳"
        fu3 = "✓" if contact.get('followup3_sent_date') else "⏳"
        reply = "✓" if contact.get('reply_received') == 'True' else "✗"
        
        table.add_row(email, initial, fu1, fu2, fu3, reply)
    
    return table


def main():
    console.print("[bold cyan]Monitoring Email Test Progress[/bold cyan]")
    console.print("Press Ctrl+C to stop monitoring\n")
    
    try:
        with Live(create_status_table([]), refresh_per_second=1, console=console) as live:
            while True:
                contacts = read_csv_status()
                live.update(create_status_table(contacts))
                time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


if __name__ == '__main__':
    main()