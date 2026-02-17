# TikTok BC Automation Design

**Date:** 2025-02-17  
**Status:** Approved  
**Goal:** 100 accounts/day, fully automated with Hermes

---

## Overview

Hermes (the autonomous AI agent on clawdbot) orchestrates TikTok Business Center account setup and White Hat campaign creation. It uses Camoufox for anti-detect browser automation and calls Python utility scripts as tools.

**Key insight:** No middleware API server needed. Hermes IS the orchestrator — it sees screenshots, makes decisions, and executes via utility scripts.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAWDBOT SERVER                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   HERMES (Autonomous AI Agent)                              │
│   ├── Claude Sonnet 4.5                                     │
│   ├── Reads: PLAYBOOK.md (instructions)                     │
│   ├── Calls: Python utility scripts                         │
│   ├── Tracks: SQLite database                               │
│   │                                                         │
│   │   Loop per account:                                     │
│   │   1. Check DB for next queued account                   │
│   │   2. Launch Camoufox with proxy                         │
│   │   3. Screenshot → Decide → Execute → Verify             │
│   │   4. Repeat until account complete                      │
│   │   5. Update DB, close browser, next account             │
│   │                                                         │
│   └── Utilities:                                            │
│       ├── lib/browser.py      (Camoufox control)            │
│       ├── lib/actions.py      (click, type, screenshot)     │
│       ├── lib/captcha.py      (SadCaptcha API)              │
│       ├── lib/sms.py          (SMSPool API)                 │
│       ├── lib/accounts.py     (HootServices, VitalProxies)  │
│       ├── lib/db.py           (SQLite helpers)              │
│       └── lib/tiktok_api.py   (Campaign monitor)            │
│                                                             │
│   CAMPAIGN MONITOR (Cron every 5 min)                       │
│   └── Check pending campaigns via TikTok API                │
│   └── Auto-pause when approved                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Account Flow

| Step | Action | Tools Used |
|------|--------|------------|
| 1 | Fetch account from HootServices | lib/accounts.py |
| 2 | Generate proxy for region | lib/accounts.py (VitalProxies) |
| 3 | Launch Camoufox with proxy | lib/browser.py |
| 4 | Navigate to TikTok Business login | lib/actions.py |
| 5 | Login/Signup (handle captcha, SMS) | lib/actions.py, lib/captcha.py, lib/sms.py |
| 6 | Create Business Center | lib/actions.py |
| 7 | Add VAT code (FR/IT/NL) | lib/actions.py |
| 8 | Add payment method | lib/actions.py |
| 9 | Create White Hat campaign (+7 days, , 404 URL) | lib/actions.py |
| 10 | Save campaign_id, close browser | lib/db.py, lib/browser.py |

**Background:** Campaign monitor auto-pauses approved campaigns via TikTok Marketing API.

---

## File Structure

```
/root/bcs/
├── PLAYBOOK.md              # Hermes instruction manual
├── accounts.db              # SQLite database
│
├── config/
│   ├── settings.json        # Timeouts, retries
│   ├── tiktok_api.json      # TikTok Marketing API creds
│   ├── tiktok_bc_setup_config.json  # HootServices, Vital, SMS, SadCaptcha
│   └── vat_codes.json       # FR, IT, NL VAT codes
│
├── lib/                     # Utility scripts
│   ├── browser.py           # Camoufox: launch, screenshot, close
│   ├── actions.py           # click, type, wait, scroll
│   ├── captcha.py           # SadCaptcha API wrapper
│   ├── sms.py               # SMSPool API wrapper
│   ├── accounts.py          # HootServices + Vital Proxies
│   ├── db.py                # SQLite helpers
│   └── tiktok_api.py        # Campaign monitor + pause
│
├── screenshots/{account_id}/
└── logs/automation.log
```

---

## Database Schema

```sql
CREATE TABLE accounts (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    region TEXT NOT NULL,
    proxy TEXT,
    
    status TEXT DEFAULT 'queued',
    current_step TEXT,
    
    bc_id TEXT,
    campaign_id TEXT,
    campaign_status TEXT,
    
    error_log TEXT,
    attempts INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    account_id TEXT PRIMARY KEY,
    cookies TEXT,
    browser_state TEXT,
    last_screenshot TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_status ON accounts(status);
CREATE INDEX idx_campaign_status ON accounts(campaign_status);
```

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Captcha fails 3x | status=paused, move to next account |
| SMS timeout | Retry once, then status=failed |
| Unexpected UI | Screenshot, attempt recovery, pause if stuck |
| Browser crash | Relaunch, resume from current_step |
| TikTok rate limit | Wait 5 min, retry |

**Recovery:** Accounts with status=paused need manual review. Hermes flags them and continues with others.

---

## External APIs

| API | Purpose | Config Location |
|-----|---------|-----------------|
| HootServices | Fetch BC accounts | tiktok_bc_setup_config.json |
| Vital Proxies | Region-matched proxies | tiktok_bc_setup_config.json |
| SMSPool | Phone verification | tiktok_bc_setup_config.json |
| SadCaptcha | Captcha solving | tiktok_bc_setup_config.json |
| TikTok Marketing API | Campaign monitor/pause | tiktok_api.json |

---

## Scaling

- **Target:** 100 accounts/day
- **Time per account:** ~15 min average
- **Parallel:** 2-3 Hermes subagents = 8-10 hours total
- **Hermes config:** maxConcurrent=4, subagents.maxConcurrent=8

---

## Dependencies

- **Camoufox** — Anti-detect browser (open-source, Playwright-compatible)
- **Python 3.10+** — Utility scripts
- **SQLite** — State tracking
- **Hermes** — Already running on clawdbot

---

## Next Steps

1. Install Camoufox on clawdbot
2. Create SQLite database
3. Write utility scripts (lib/*.py)
4. Write PLAYBOOK.md for Hermes
5. Create campaign monitor cron job
6. Test with 1 account
7. Scale to 100/day
