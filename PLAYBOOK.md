# TikTok BC Automation Playbook

This playbook guides Hermes through automating TikTok Business Center setup.

## Quick Start

```bash
cd /root/bcs
source venv/bin/activate
```

## Available Tools

| Module | Function | Description |
|--------|----------|-------------|
| lib.db | `get_next_queued_account()` | Get next account to process |
| lib.db | `update_account(id, **kwargs)` | Update account status |
| lib.db | `add_account(id, email, pwd, region, proxy)` | Add account to queue |
| lib.accounts | `fetch_fresh_account()` | Get new account from HootServices |
| lib.accounts | `get_proxy_for_region(region)` | Generate proxy |
| lib.browser | `launch_browser(account_id, proxy, headless)` | Start Camoufox |
| lib.actions | `click(page, selector)` | Click element |
| lib.actions | `type_text(page, selector, text)` | Type with delays |
| lib.actions | `fill(page, selector, text)` | Fill input fast |
| lib.actions | `wait_for(page, selector)` | Wait for element |
| lib.captcha | `solve_captcha(page)` | Solve any TikTok captcha |
| lib.sms | `order_phone_number(region)` | Get phone number |
| lib.sms | `get_sms_code(order_id)` | Get SMS code |

## Account Processing Flow

### Step 1: Get Account

```python
from lib.db import get_next_queued_account, update_account, add_account
from lib.accounts import fetch_fresh_account, get_proxy_for_region

# Option A: Get from queue
account = get_next_queued_account()

# Option B: Fetch fresh and add to queue
if not account:
    fresh = fetch_fresh_account()
    if fresh:
        proxy = get_proxy_for_region(fresh["region"])
        add_account(fresh["id"], fresh["email"], fresh["password"], fresh["region"], proxy)
        account = get_next_queued_account()
```

### Step 2: Launch Browser

```python
from lib.browser import launch_browser

browser = launch_browser(
    account_id=account["id"],
    proxy=account["proxy"],
    region=account["region"],
    headless=True
)

page = browser.get_page()
update_account(account["id"], status="in_progress", current_step="browser_launched")
```

### Step 3: Navigate to TikTok Business

```python
browser.goto("https://business.tiktok.com/")
browser.screenshot("landing")
```

### Step 4: Login

```python
from lib.actions import click, type_text, fill, wait_for
from lib.captcha import solve_captcha

# Click login
click(page, "text=Log in")
wait_for(page, "input[name=email]")

# Enter credentials
type_text(page, "input[name=email]", account["email"])
type_text(page, "input[name=password]", account["password"])
click(page, "button[type=submit]")

# Handle captcha
solve_captcha(page)

browser.screenshot("after_login")
update_account(account["id"], current_step="logged_in")
```

### Step 5: Handle Email Verification (if needed)

```python
from lib.accounts import get_email_verification_code

if wait_for(page, "text=verification code", timeout=5000):
    code = get_email_verification_code(account["email"])
    if code:
        type_text(page, "input[placeholder*=code]", code)
        click(page, "button[type=submit]")
```

### Step 6: Handle Phone Verification (if needed)

```python
from lib.sms import order_phone_number, get_sms_code

if wait_for(page, "text=phone number", timeout=5000):
    sms = order_phone_number(account["region"])
    type_text(page, "input[type=tel]", sms["phone_number"])
    click(page, "text=Send code")
    
    code = get_sms_code(sms["order_id"])
    if code:
        type_text(page, "input[placeholder*=code]", code)
        click(page, "button[type=submit]")
```

### Step 7: Create Business Center

```python
if wait_for(page, "text=Create Business Center"):
    click(page, "text=Create Business Center")

type_text(page, "input[name=business_name]", f"Business {account[id][:8]}")
click(page, "text=Create")

browser.screenshot("bc_created")
update_account(account["id"], current_step="bc_created")
```

### Step 8: Add VAT Code

```python
import json
with open("config/tiktok_bc_setup_config.json") as f:
    config = json.load(f)

vat_codes = config["billing"]["vat_codes"]
region = account["region"]

if region in vat_codes:
    click(page, "text=Tax Information")
    type_text(page, "input[name=vat]", vat_codes[region])
    click(page, "text=Save")
```

### Step 9: Add Payment Method

```python
card = config["billing"]["card"]

click(page, "text=Payment")
click(page, "text=Add Card")

type_text(page, "input[name=card_number]", card["number"])
type_text(page, "input[name=expiry]", card["expiry"])
type_text(page, "input[name=cvv]", card["cvv"])

click(page, "text=Save")
browser.screenshot("payment_added")
update_account(account["id"], current_step="payment_added")
```

### Step 10: Create White Hat Campaign

```python
from datetime import datetime, timedelta

click(page, "text=Create Campaign")

# Campaign name
type_text(page, "input[name=campaign_name]", f"WH_{account[id][:8]}")

# Start date (+7 days)
start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
fill(page, "input[name=start_date]", start_date)

# Budget $10
fill(page, "input[name=budget]", "10")

# 404 URL
fill(page, "input[name=url]", "https://example.com/404")

click(page, "text=Create")
browser.screenshot("campaign_created")

# Get campaign ID
campaign_id = page.url.split("/")[-1]
update_account(
    account["id"],
    status="complete",
    current_step="campaign_created",
    campaign_id=campaign_id,
    campaign_status="pending"
)
```

### Step 11: Cleanup

```python
browser.close()
print(f"Completed account {account[id]}")
```

## Error Handling

**Captcha fails 3x:**
```python
update_account(account["id"], status="paused", error_log="Captcha failed 3x")
browser.screenshot("captcha_failed")
browser.close()
```

**Unexpected state:**
```python
browser.screenshot("unexpected_state")
update_account(account["id"], status="paused", error_log="Unexpected UI")
```

## Campaign Monitor

The monitor runs via cron every 5 minutes to auto-pause approved campaigns:
```bash
python monitor_campaigns.py
```

## After Every Run: Export CSV

**IMPORTANT: After completing any account (success or failure), always export CSV:**

```python
from lib.db import export_to_csv

csv_path = export_to_csv()
print(f"CSV exported to: {csv_path}")
# Provide this file to user as attachment
```

The CSV includes all columns: id, email, password, region, proxy, status, current_step, bc_id, campaign_id, campaign_status, error_log, attempts, created_at, updated_at
