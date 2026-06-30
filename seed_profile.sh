#!/bin/bash
# ONE-TIME (and occasional re-do) setup for the MN color bot.
#
# Opens the bot's dedicated Chrome profile at the MN HPSP site so YOU can pass
# the bot-protection challenge by hand. Once the page shows the color, the trust
# cookie is saved in this profile and the automated bot can reuse it.
#
# Re-run this whenever the bot starts failing again (the trust cookie expired).
#
# This runs as a SEPARATE Chrome instance, so your normal Chrome can stay open.
set -euo pipefail

PROFILE_DIR="${CHROME_PROFILE_DIR:-$HOME/Library/Application Support/mn-color-bot-chrome}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL="https://hpsp.hlb.state.mn.us/"

mkdir -p "$PROFILE_DIR"

echo "Opening the MN site in the bot's profile:"
echo "  $PROFILE_DIR"
echo
echo ">> Pass any 'verify you are human' / challenge until you SEE the daily color."
echo ">> Then just close that Chrome window. The trust cookie is now saved."
echo

"$CHROME" --user-data-dir="$PROFILE_DIR" --no-first-run --no-default-browser-check "$URL"
