# TikTok BC White Hat Generator - Session Notes

## Project Overview

Automated TikTok Business Center setup + White Hat campaign creation using Hermes (AI agent).

---

## Architecture

```
Hermes (AI Agent on clawdbot)
    ↓
Python utility scripts (lib/)
    ↓
├── Camoufox (anti-detect browser)
├── HootServices (BC accounts + email verification)
├── VitalProxies (region-matched proxies)
├── SMSPool (phone verification)
├── SadCaptcha (captcha solving)
└── TikTok Marketing API (campaign monitor)
```

---

## Cost Breakdown (Per Account)

| Service | Cost |
|---------|------|
| HootServices | $0.50 |
| VitalProxies | ~$0.20 |
| SMSPool | ~$0.75 |
| SadCaptcha | ~$0.01 |
| **TOTAL** | **~$1.50** |

Plus TikTok deposit ($10 min) - recoverable when auto-paused

**100 accounts/day = ~$150/day**

---

## Exact Flow (From Transcript)

### Phase 1: Signup
1. Go to business.tiktok.com
2. Click "Sign Up"
3. Solve captcha (SadCaptcha)
4. Enter email + password (from HootServices)
5. Get email verification code (poll HootServices API)
6. Select "Advertiser"
7. Fill REQUIRED fields only
8. Phone verification if triggered (SMSPool)
9. Set timezone: UTC
10. Two-step popup: Click "Not Now"

### Phase 2: Verification (Billing)
1. Go to "Accounts" section (shows "in review")
2. Go to "Verification" section
3. Enter VAT code if EU:
   - FR: FR90451321335
   - IT: IT00348170101
   - Other countries: Ask user
4. Add payment method (automatic if available)
5. Enter card details

### Phase 3: Assign Ad Account
1. Go to "Ads Manager"
2. Assign ad account to Business Center
3. Enter email code if requested
4. Click Launch

### Phase 4: White Hat Campaign
**Campaign Level:**
- Switch to "Full Version"
- Objective: Traffic (or Reach, Video Views)
- Leave as Manual
- Continue

**Ad Group Level:**
- UNSELECT all placements except TikTok (no Pangle!)
- Location: same as account country
- Age/Gender: All
- Budget: $20 (ad account min), $10 (campaign min)
- Schedule: +1 day ahead (so it doesnt spend)

**Ad Creative:**
- Upload image from creatives folder
- Add random audio from TikTok library
- Add random text overlay
- URL: 404 link
- Publish

### Phase 5: Monitor
- Save campaign ID
- Cron job checks every 5 min
- Auto-pause when approved (before it spends)

---

## Key Settings

| Setting | Value |
|---------|-------|
| BC Name | Random generator ("Digital Solutions" etc) |
| Ad Account Name | Random generator (unique) |
| Campaign Name | Random generator (unique) |
| Timezone | UTC |
| Objective | TRAFFIC (default) |
| Budget | Minimum per currency |
| Placements | TikTok ONLY |
| Targeting | Same region, all ages |
| Auto-pause | On approval |

---

## Important Rules

1. **Gmails > temp emails** - Temp emails cause payment failures
2. **UNSELECT other placements** - TikTok only, no Pangle
3. **Schedule +1 day** - So campaign doesnt spend
4. **Netherlands/EU** - Performs well for getting active
5. **VAT code required for EU** - Avoids tax issues
6. **Two-step: "Not Now"** - Skip 2FA setup
7. **Automatic payment** - If not showing, proxy might be weak

---

## Payment Solution (TODO)

**Problem:** 3D Secure OTP when adding card

**Solution:** Airwallex (AU-based)
- Virtual cards via API
- SMS OTP (can intercept)
- Made for ad buying

**Setup needed:**
1. Create Airwallex business account
2. Create virtual cards via API
3. Set SMS to receivable number
4. Bot enters 3DS code

---

## File Structure

```
/root/bcs/
├── config/
│   ├── tiktok_bc_setup_config.json  # API keys (gitignored)
│   ├── bc_setup.json                 # Name generator, VAT codes
│   ├── campaign.json                 # Campaign settings
│   ├── ad_group.json                 # Targeting
│   ├── ad_creative.json              # Creative settings
│   └── flow.json                     # Exact step-by-step flow
├── lib/
│   ├── db.py           # SQLite tracking
│   ├── browser.py      # Camoufox
│   ├── actions.py      # Click, type, wait
│   ├── accounts.py     # HootServices + VitalProxies
│   ├── sms.py          # SMSPool
│   ├── captcha.py      # SadCaptcha
│   ├── bc_helpers.py   # Name generator, VAT
│   └── tiktok_api.py   # Campaign monitor
├── creatives/images/   # Ad images go here
├── run.py              # Quick start
├── PLAYBOOK.md         # Hermes instructions
├── monitor_campaigns.py # Cron job
└── README.md           # Setup guide
```

---

## Quick Commands

```bash
# SSH to server
ssh root@77.42.72.129

# Activate environment
cd /root/bcs && source venv/bin/activate

# Run quick setup
python3 run.py

# Check balances
python3 -c "from lib.sms import get_sms_client; print(get_sms_client().get_balance())"

# Export CSV
python3 -c "from lib.db import export_to_csv; export_to_csv()"
```

---

## Current Balances

- SMSPool: $7.31 (~7-14 accounts)
- HootServices: 39 accounts ready

---

## TODO

- [ ] Set up Airwallex for payment automation
- [ ] Add card details to config
- [ ] Upload images to creatives/images/
- [ ] Test 1 account end-to-end
- [ ] Scale to 100/day

---

## GitHub

Repo: https://github.com/nish261/vc-whitehat-generator

**Not in repo (gitignored):**
- API keys
- accounts.db
- screenshots
- exports

**Example config included** - copy and fill in your keys
