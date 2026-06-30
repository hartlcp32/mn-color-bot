# botworks.md — How we got the MN Color Bot working (playbook for future bots)

A field guide written after debugging the MN Color Bot on 2026-06-30. Read this
before building or fixing any "scrape a website on a schedule and ping me" bot.

---

## TL;DR of what was actually wrong

The bot had been failing every day. We found **three layered problems**, only the
last of which was the real blocker:

1. **Wrong run location.** It was running as a **GitHub Actions cron job** (in
   GitHub's Ubuntu cloud), not on the Mac. The cloud VM has **no screen**, so the
   non-headless Chrome couldn't open a window. Leaving the Mac on / caffeinated
   did nothing, because the Mac was never involved.
2. **A brittle git step.** When no color was found, the script never wrote
   `mn_color_history.csv`, so the workflow's `git add mn_color_history.csv` step
   hard-failed (exit 128) — that's the red ❌ we kept seeing.
3. **The real blocker: bot protection.** The target site
   (`hpsp.hlb.state.mn.us`) is now behind **Radware Bot Manager / ShieldSquare
   (perfdrive.com)**. It silently lets real humans through but bounces automated
   browsers (Selenium, curl) to a `validate.perfdrive.com` challenge. This blocks
   **every** bot — cloud or local, headless or not.

**The fix that worked:** run the bot **locally on the Mac** using a **dedicated
Chrome profile that the human passed the wall in once**. Once a real person loads
the site in that profile, the trust cookie is stored, and the automated Chrome
reusing that same profile sails right through.

---

## The general method: how to debug "my bot stopped working"

This sequence is reusable for any scheduled scraper bot.

1. **Find where it actually runs.** Cloud (GitHub Actions / cron in CI) or local
   (launchd / cron on your machine)? Check `.github/workflows/*.yml` for
   `runs-on:` and `schedule:`. A bot "on GitHub" usually runs in GitHub's cloud,
   **not** on your computer. This single fact resolves most confusion.
2. **Look at the real run logs, not just red/green.** For GitHub Actions:
   - List runs: `curl -s "https://api.github.com/repos/OWNER/REPO/actions/runs?per_page=8"`
   - Get step-by-step results for a run:
     `curl -s ".../actions/runs/RUN_ID/jobs"` and read each step's `conclusion`.
   - This told us the Python step "succeeded" but the **git step** failed —
     completely different from where we assumed.
3. **Reproduce locally with a full traceback.** The script only printed
   `str(e)` (`'NoneType' object has no attribute 'encode'` — useless). Re-running
   the exact Selenium options in a tiny standalone script with
   `traceback.print_exc()` revealed the Chrome **window was crashing**
   (`NoSuchWindowException: target window already closed`).
4. **Strip to the simplest HTTP request to see what the server really sends.**
   `curl -sL -D - "URL"` exposed the **302 redirect to validate.perfdrive.com**
   and `server: rdwr` — the smoking gun for bot protection. Always do this; a
   browser hides redirects and challenge pages behind JavaScript.

---

## How to tell a site has bot protection

Signs we saw (any one is a strong hint):

- Response header `server: rdwr` (Radware) or similar WAF/CDN bot vendors.
- A **302/redirect to a "validate", "challenge", or vendor domain** like
  `validate.perfdrive.com`, `*.shieldsquare.com`, Cloudflare `/cdn-cgi/challenge`,
  PerimeterX `_px`, DataDome, Akamai `_abck` cookies.
- Selenium gets an **empty `<body>`** (0 chars), a blank screenshot, or the tab
  **crashes** on `driver.get()`.
- `curl` and Selenium fail but **your normal browser works fine** — this is the
  signature of human-vs-bot discrimination, NOT a site outage.

Key mental model: **"the site opens for me" and "the bot is blocked" are both
true at once.** Protection is invisible to humans by design.

---

## The pattern that beats it locally: a human-seeded Chrome profile

This is the reusable trick. It works for many (not all) bot walls.

1. **Give the bot its own Chrome profile folder**, separate from your everyday
   Chrome so both can run at once and you never risk your real profile:
   `~/Library/Application Support/<bot-name>-chrome`
2. **Seed it once, by hand.** Launch real (non-automated) Chrome pointed at that
   profile, load the site, pass any challenge until you SEE the content, then
   close it. The trust cookie is now stored in that profile.
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --user-data-dir="$HOME/Library/Application Support/<bot-name>-chrome" \
     --no-first-run --no-default-browser-check "https://SITE/"
   ```
   (See `seed_profile.sh` for the working version.)
3. **Point Selenium at the same profile** so it reuses the cookie:
   ```python
   options.add_argument(f'--user-data-dir={PROFILE_DIR}')
   ```
4. **Run non-headless on a machine with a real display** (your Mac). Headless +
   automation flags are more likely to be re-challenged.
5. **Re-seed when it breaks again.** The trust cookie expires (days to weeks).
   When the bot starts failing, just re-run the seed step. That's the only
   recurring manual chore.

Caveats:
- Chrome must **not** already be running *with that same profile dir* when
  Selenium starts (it locks the dir). A separate everyday profile is fine.
- This is the kind of thing that can violate a site's terms of use. We did it
  because the user is a legitimate participant checking their *own* daily color.
- If seeding doesn't get through, the next things to try are
  `undetected-chromedriver`, or finding an alternate/official data source.

---

## Running a bot locally on a Mac (the working setup)

Files in this repo that make it go:

- **`mn_color_bot_github.py`** — the scraper. Now reads `CHROME_PROFILE_DIR`
  (env var) and adds `--user-data-dir` so it reuses the seeded profile.
- **`seed_profile.sh`** — one-time / occasional: opens the bot's profile so you
  can pass the wall by hand.
- **`run_local.sh`** — wrapper the scheduler calls. It:
  - `cd`s into the repo,
  - loads secrets from `~/.env` (`BOT_TOKEN`, `CHAT_ID`) — never commit these,
  - runs the script under `caffeinate -i` so the Mac won't idle-sleep mid-run,
  - appends output to `run_local.log`.
- **launchd job** `~/Library/LaunchAgents/com.hartley.mncolorbot.plist` — fires
  `run_local.sh` at **9:00am Central, Mon–Fri** (`StartCalendarInterval`).
  Manage it with:
  ```bash
  launchctl load   ~/Library/LaunchAgents/com.hartley.mncolorbot.plist   # enable
  launchctl unload ~/Library/LaunchAgents/com.hartley.mncolorbot.plist   # disable
  launchctl list | grep mncolorbot                                       # status
  launchctl start  com.hartley.mncolorbot                                # run now
  ```

Local vs. cloud, when to pick which:

| | Local (Mac, launchd) | Cloud (GitHub Actions) |
|---|---|---|
| Beats bot walls | ✅ via real profile | ❌ datacenter IPs blocked |
| Runs when Mac is off | ❌ | ✅ |
| Needs headless | ❌ (real screen) | ✅ (no display) |
| Good for | sites with bot protection | simple, unprotected sites/APIs |

If a future site has **no** bot protection, GitHub Actions is the easier, more
reliable choice (runs even when your Mac is asleep). Use local only when you must
defeat a wall.

---

## Secrets

- Keep tokens in `~/.env` as `KEY=value` lines. `run_local.sh` sources it.
- `.env` is git-ignored — **never** commit it.
- For the cloud path, the equivalents are GitHub repo **Secrets** referenced as
  `${{ secrets.NAME }}` in the workflow.

---

## Gotchas worth remembering

- **Chrome vs chromedriver must match major version** (e.g. Chrome 149 ↔
  chromedriver 149). A mismatch throws cryptic errors. Prefer letting Selenium
  Manager (built into Selenium ≥4.6) fetch the right driver over hardcoding a
  path — the old hardcoded mac-arm64 path here only worked by luck.
- **A script that exits 0 can still have "failed."** This bot sent a Telegram
  "failed" message but returned exit 0, so the CI step looked green. Make the
  script `sys.exit(1)` on real failure if you want the scheduler to flag it.
- **Don't trust red/green — read the step that failed.** Ours was failing in a
  totally different place (git) than where the actual problem was (the wall).
- **`curl -D -` is your fastest truth-teller.** It shows redirects, server
  headers, and challenge pages that a browser hides.

---

## Current status (2026-06-30)

✅ Runs locally on the Mac, 9am Central weekdays, via launchd.
✅ Uses a human-seeded dedicated Chrome profile to pass Radware bot protection.
✅ Successfully scraped "Denim" for Tue Jun 30 2026 and sent it to Telegram.
🚫 GitHub Actions scheduled run is disabled (kept only for manual `workflow_dispatch` testing).

### Known limitation
The bot is **send-only** — it pushes the color to Telegram on a schedule. It does
**not** listen for messages, so there is currently **no command you can text it**
(e.g. `/color`) to trigger an on-demand check. Adding that requires a separate,
always-running listener process (Telegram long-polling `getUpdates` or a webhook).
A future enhancement.
