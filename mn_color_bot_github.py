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

def get_mn_color(retry_count=3):
    """Fetch the current color from HPSP website with retry logic"""
    url = "https://hpsp.hlb.state.mn.us/"

    for attempt in range(retry_count):
        if attempt > 0:
            print(f"Retry attempt {attempt + 1} of {retry_count}...")
            time.sleep(5)  # Wait before retry

        # Configure Chrome options to avoid bot detection
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Remove headless to appear more like a real browser
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Reuse a persistent, human-blessed Chrome profile so the site's bot
        # protection (Radware/perfdrive) treats us as a returning real user.
        # Seed it once by hand via seed_profile.sh, then this reuses its cookies.
        profile_dir = os.environ.get(
            'CHROME_PROFILE_DIR',
            os.path.expanduser('~/Library/Application Support/mn-color-bot-chrome'))
        if profile_dir:
            options.add_argument(f'--user-data-dir={profile_dir}')

        driver = None

        try:
            print("Setting up Chrome driver...")
            # Direct path to ChromeDriver to avoid webdriver-manager issues
            chromedriver_path = os.path.expanduser("~/.wdm/drivers/chromedriver/mac64/149.0.7827.155/chromedriver-mac-arm64/chromedriver")
            if not os.path.exists(chromedriver_path):
                # Fallback to webdriver-manager
                chromedriver_path = ChromeDriverManager().install()
                # Fix the path if it's pointing to the wrong file
                if chromedriver_path.endswith("THIRD_PARTY_NOTICES.chromedriver"):
                    chromedriver_path = chromedriver_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver")

            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)

            # Execute JavaScript to make browser appear more human-like
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })

            print(f"Loading {url}...")
            driver.get(url)
            time.sleep(20)  # Wait longer for page to fully load

            # Save screenshot for debugging
            driver.save_screenshot('/tmp/mn_page_screenshot.png')
            print("Screenshot saved to /tmp/mn_page_screenshot.png")

            # Get page text
            body = driver.find_element(By.TAG_NAME, "body")
            page_text = body.text if body else ""

            # Debug: Save page content to file
            with open('/tmp/mn_page_content.txt', 'w') as f:
                f.write(page_text)
            print(f"Page content saved to /tmp/mn_page_content.txt (length: {len(page_text)} chars)")

            # Check if page is blocked
            if "bot" in page_text.lower() or "captcha" in page_text.lower() or len(page_text) < 100:
                print(f"Bot detection or empty page on attempt {attempt + 1}")
                if driver:
                    driver.quit()
                continue  # Try again

            # Look for color phrase
            lines = page_text.split('\n')

            for i, line in enumerate(lines):
                if "The colors on" in line and ":" in line:
                    date_str = line.split("The colors on")[-1].split(":")[0].strip()

                    # Get all colors (could be multiple lines)
                    colors = []
                    for j in range(i+1, min(i+10, len(lines))):
                        line_text = lines[j].strip()
                        if line_text and line_text != ':':
                            # Stop if we hit navigation/login elements
                            if line_text.lower() in ['login', 'welcome', 'username', 'password', 'navigate']:
                                break
                            colors.append(line_text)
                        elif not line_text and colors:
                            # Empty line after colors, stop collecting
                            break

                    if colors:
                        color_str = " and ".join(colors)
                        print(f"✅ Found colors: {color_str} for {date_str}")
                        if driver:
                            driver.quit()
                        return {'color': color_str, 'date': date_str}

            print(f"No color found on attempt {attempt + 1}")
            if driver:
                driver.quit()

        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if driver:
                driver.quit()
            continue

    # All retries failed
    print("❌ No color found after all retries")
    return {'color': None, 'date': None}

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