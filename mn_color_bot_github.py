#!/usr/bin/env python3
"""
MN Color Bot for GitHub Actions
Simplified version that runs once and exits
"""
import os
import csv
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Get credentials from environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram_message(message):
    """Send a message via Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        if result.get('ok'):
            print(f"✅ Telegram message sent successfully")
        else:
            print(f"❌ Failed to send message: {result}")
        return result
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return None

def get_mn_color():
    """Fetch the current color from HPSP website"""
    url = "https://hpsp.hlb.state.mn.us/"

    # Configure Chrome options for headless mode
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = None

    try:
        print("Setting up Chrome driver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        print(f"Loading {url}...")
        driver.get(url)
        time.sleep(15)  # Wait for page to fully load

        # Get page text
        body = driver.find_element(By.TAG_NAME, "body")
        page_text = body.text if body else ""

        # Look for color phrase
        lines = page_text.split('\n')

        for i, line in enumerate(lines):
            if "The colors on" in line and ":" in line:
                date_str = line.split("The colors on")[-1].split(":")[0].strip()

                # Get the next non-empty line as the color
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip() and lines[j].strip() != ':':
                        color = lines[j].strip()
                        print(f"✅ Found color: {color} for {date_str}")
                        return {'color': color, 'date': date_str}

        print("❌ No color found on page")
        return {'color': None, 'date': None}

    except Exception as e:
        print(f"Error fetching color: {e}")
        return {'color': None, 'date': None}

    finally:
        if driver:
            driver.quit()

def log_color_to_csv(color, date_str):
    """Log color to CSV file"""
    log_file = 'mn_color_history.csv'

    # Initialize file if it doesn't exist
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Day', 'Color', 'Timestamp'])

    # Append new color entry
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        day_name = datetime.now().strftime('%A')

        with open(log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date_str or datetime.now().strftime('%Y-%m-%d'),
                           day_name, color, timestamp])
        print(f"✅ Logged to CSV: {color}")
    except Exception as e:
        print(f"Error logging to CSV: {e}")

def main():
    """Main function"""
    print("=" * 50)
    print("MN COLOR BOT - GitHub Actions")
    print(f"Time: {datetime.now()}")
    print("=" * 50)

    # Verify credentials
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Error: BOT_TOKEN or CHAT_ID not set in environment variables")
        return

    # Get current color
    color_info = get_mn_color()

    if color_info['color']:
        # Send Telegram message
        message = (
            f"🎨 <b>Minnesota Daily Color</b>\n\n"
            f"📅 Date: {color_info['date'] or 'Today'}\n"
            f"🎯 Color: <b>{color_info['color']}</b>\n"
            f"⏰ Time: {datetime.now().strftime('%H:%M')} CST\n\n"
            f"🔗 <a href='https://hpsp.hlb.state.mn.us/'>View on HPSP website</a>"
        )
        send_telegram_message(message)

        # Log to CSV
        log_color_to_csv(color_info['color'], color_info['date'])
    else:
        # Send failure message
        message = (
            f"⚠️ <b>MN Color Check Failed</b>\n"
            f"Could not fetch today's color\n"
            f"Time: {datetime.now().strftime('%H:%M')} CST\n\n"
            f"🔗 <a href='https://hpsp.hlb.state.mn.us/'>Check manually on HPSP website</a>"
        )
        send_telegram_message(message)

    print("✅ Bot execution completed")

if __name__ == "__main__":
    main()