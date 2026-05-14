# MN Daily Color Bot

This bot automatically checks the Minnesota HPSP daily color and sends it to you via Telegram every weekday at 9:00 AM CST.

## Setup Instructions

### 1. Fork/Create Repository
1. Go to GitHub and create a new repository called `mn-color-bot`
2. Make it public (required for free GitHub Actions)

### 2. Upload Files
Upload these files to your repository:
- `.github/workflows/daily-color-check.yml`
- `mn_color_bot_github.py`
- `requirements.txt`
- This `README.md`

### 3. Add Secrets
Go to your repository's Settings → Secrets and variables → Actions

Add these two secrets:
- `BOT_TOKEN`: Your Telegram bot token (8724516924:AAGPHdHJbndJ5L6-8lplE1yUFJeKnFDO-zg)
- `CHAT_ID`: Your Telegram chat ID (7318493574)

### 4. Enable GitHub Actions
1. Go to the Actions tab in your repository
2. Enable workflows if prompted

### 5. Test It
1. Go to Actions tab
2. Click on "Daily MN Color Check" workflow
3. Click "Run workflow" → "Run workflow" to test manually

## Features
- ✅ Runs automatically every weekday at 9:00 AM CST
- ✅ Sends color via Telegram
- ✅ Keeps history in `mn_color_history.csv`
- ✅ Completely free using GitHub Actions
- ✅ No need to keep your computer on

## Manual Testing
You can trigger the bot manually anytime:
1. Go to Actions tab
2. Select "Daily MN Color Check"
3. Click "Run workflow"

## Color History
The bot maintains a CSV file with all historical colors. This file is automatically updated and committed back to the repository.

## Troubleshooting
- Check the Actions tab for any error messages
- Ensure your secrets are set correctly
- The workflow runs at 2:00 PM UTC (9:00 AM CST)

## Schedule
The bot runs Monday through Friday at 9:00 AM CST.
To change the schedule, edit the cron expression in `.github/workflows/daily-color-check.yml`