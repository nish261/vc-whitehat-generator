# TikTok BC White Hat Generator

Automated TikTok Business Center setup + White Hat campaign creation.

## What It Does

1. Fetches fresh BC accounts from HootServices
2. Generates region-matched proxies (VitalProxies)
3. Launches anti-detect browser (Camoufox)
4. Logs into TikTok, handles captcha (SadCaptcha) + SMS verification (SMSPool)
5. Creates Business Center with random name, VAT code if needed
6. Creates Ad Account + Campaign (REACH objective, minimum budget)
7. Schedules campaign +7 days, auto-pauses when approved

## Setup

### 1. Install Dependencies

```bash
cd /root/bcs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy example config and fill in your keys:

```bash
cp config/tiktok_bc_setup_config.example.json config/tiktok_bc_setup_config.json
```

Edit `config/tiktok_bc_setup_config.json` with:
- HootServices API key
- Vital Proxies API key
- SMSPool API key
- SadCaptcha API key
- Payment card details
- VAT codes

### 3. Add Creative Assets

Put your images in:
```
creatives/images/
```

## Usage

### Quick Run

```bash
source venv/bin/activate
python3 run.py
```

Asks:
1. How many BCs?
2. Type? (whitehat/dropship/cpa)
3. URL? (if not whitehat)

### With Hermes (AI Agent)

Hermes reads `PLAYBOOK.md` and processes accounts autonomously.

## File Structure

```
├── config/
│   ├── tiktok_bc_setup_config.json  # API keys (gitignored)
│   ├── bc_setup.json                 # BC/campaign settings
│   ├── ad_group.json                 # Targeting settings
│   └── ad_creative.json              # Creative settings
├── lib/
│   ├── db.py           # SQLite state tracking
│   ├── browser.py      # Camoufox control
│   ├── actions.py      # Click, type, wait
│   ├── accounts.py     # HootServices + VitalProxies
│   ├── sms.py          # SMSPool
│   ├── captcha.py      # SadCaptcha
│   ├── bc_helpers.py   # Name generator, VAT codes
│   └── tiktok_api.py   # Campaign monitor
├── creatives/images/   # Your ad images
├── run.py              # Quick start script
├── PLAYBOOK.md         # Instructions for Hermes
└── monitor_campaigns.py # Cron: auto-pause approved campaigns
```

## Campaign Settings

| Setting | Value |
|---------|-------|
| Objective | REACH (asks user) |
| Budget | Minimum per currency |
| Schedule | +7 days |
| Auto-pause | On approval |
| Bid strategy | Lowest cost (auto) |
| Targeting | Same as account region |
| Age/Gender | All |
| Placements | TikTok only |

## Cron Job

Auto-pause approved campaigns every 5 min:

```bash
*/5 * * * * cd /root/bcs && source venv/bin/activate && python monitor_campaigns.py
```

## Exports

After each run, CSV exported to `exports/accounts_TIMESTAMP.csv`
