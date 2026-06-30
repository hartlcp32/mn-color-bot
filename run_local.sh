#!/bin/bash
# Run the MN color bot locally on this Mac (non-headless, real Chrome window).
# Loads BOT_TOKEN / CHAT_ID from ~/.env. Wrapped in caffeinate so the Mac
# won't idle-sleep mid-run.
set -euo pipefail

REPO_DIR="$HOME/Documents/GitHub/mn-color-bot"
LOG_FILE="$REPO_DIR/run_local.log"

cd "$REPO_DIR"

# Load credentials from ~/.env (BOT_TOKEN=..., CHAT_ID=...)
if [ -f "$HOME/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.env"
  set +a
fi

echo "===== Run started $(date '+%Y-%m-%d %H:%M:%S %Z') =====" >> "$LOG_FILE"
caffeinate -i /opt/homebrew/bin/python3 mn_color_bot_github.py >> "$LOG_FILE" 2>&1
echo "===== Run finished $(date '+%Y-%m-%d %H:%M:%S %Z') (exit $?) =====" >> "$LOG_FILE"
