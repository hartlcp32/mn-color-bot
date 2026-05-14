#!/usr/bin/env python3
import webbrowser
import subprocess
import time

print("=" * 50)
print("MN COLOR BOT - GITHUB SETUP HELPER")
print("=" * 50)

# Try to get GitHub username from git config
try:
    result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
    username = result.stdout.strip()
    if not username:
        username = input("\nEnter your GitHub username: ")
except:
    username = input("\nEnter your GitHub username: ")

print(f"\n✓ GitHub username: {username}")

# Build URLs
secrets_url = f"https://github.com/{username}/mn-color-bot/settings/secrets/actions/new"
actions_url = f"https://github.com/{username}/mn-color-bot/actions"

print("\nI'll open the pages you need in your browser...")
print("\n" + "=" * 50)

print("\n📝 STEP 1: Add BOT_TOKEN Secret")
print("-" * 30)
print("Name: BOT_TOKEN")
print("Value: 8724516924:AAGPHdHJbndJ5L6-8lplE1yUFJeKnFDO-zg")
print("\nOpening secrets page...")
webbrowser.open(secrets_url)

input("\nPress Enter after you've added BOT_TOKEN...")

print("\n📝 STEP 2: Add CHAT_ID Secret")
print("-" * 30)
print("Name: CHAT_ID")
print("Value: 7318493574")
print("\nOpening secrets page again...")
webbrowser.open(secrets_url)

input("\nPress Enter after you've added CHAT_ID...")

print("\n✅ STEP 3: Test the Bot")
print("-" * 30)
print("Opening Actions page...")
print("Click 'Daily MN Color Check' then 'Run workflow'")
webbrowser.open(actions_url)

print("\n" + "=" * 50)
print("✓ Setup complete!")
print("The bot will run automatically every weekday at 9 AM CST")
print("=" * 50)