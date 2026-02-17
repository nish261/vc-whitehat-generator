# TikTok BC White Hat Playbook

Exact step-by-step flow for Hermes.

## Phase 1: Signup

```
1. Go to business.tiktok.com
2. Click "Sign Up"
3. Solve captcha (SadCaptcha)
4. Enter email + password
5. Get email verification code (poll HootServices)
6. Enter code
7. Select "Advertiser"
8. Fill REQUIRED fields only:
   - Business name: random from generator
   - Country: from account region
9. Phone verification if triggered:
   - Get number from SMSPool
   - Enter number
   - Get code
   - Enter code
10. Set timezone: UTC
11. Two-step verification popup: Click "Not Now"
```

## Phase 2: Verification (Billing)

```
1. Go to "Accounts" section
2. Account shows "in review"
3. Go to "Verification" section
4. If EU country: Enter VAT code
   - FR: FR90451321335
   - IT: IT00348170101
   - Other: ASK USER
5. Add payment method:
   - If "automatic" option shows: use it
   - If only "manual": proxy might be weak
6. Enter card details from config
```

## Phase 3: Assign Ad Account

```
1. Go to "Ads Manager"
2. Assign ad account to Business Center
3. Enter email code if requested (poll HootServices again)
4. Click "Launch" or "Open"
```

## Phase 4: Create White Hat Campaign

### Campaign Level
```
1. Switch to "Full Version" (not simplified)
2. Select objective: Traffic (or Reach, Video Views)
3. Leave as "Manual"
4. Click Continue
```

### Ad Group Level
```
1. UNSELECT all placements except TikTok
   - Uncheck: Pangle, News Feed Apps, etc
   - Keep only: TikTok
2. Targeting:
   - Location: same as account country
   - Age: All
   - Gender: All
   - Interests: None needed
3. Budget: $20 (minimum)
4. Schedule: +1 day ahead (so it doesnt spend)
5. Optimization goal: doesnt matter
```

### Ad Creative Level
```
1. Click "Create New"
2. Upload image from /root/bcs/creatives/images/
3. Add audio: click any random track from TikTok library
4. Click "Export video"
5. Agree to terms
6. Add text: random from templates
7. Destination URL: 404 link (e.g. mymusclechef.com/404random)
8. Click "Publish"
```

## Phase 5: Monitor & Auto-Pause

```
1. Save campaign ID to database
2. Campaign monitor (cron every 5 min) checks status
3. When status = APPROVED, auto-pause via TikTok API
```

---

## Key Things to Remember

| Rule | Why |
|------|-----|
| Gmails > temp emails | Temp emails = payment failures |
| UNSELECT other placements | Only TikTok, no Pangle |
| Schedule +1 day | So it doesnt spend money |
| Netherlands/EU | Performs well for getting active |
| VAT code required for EU | Avoids tax issues |
| Two-step: "Not Now" | Skip 2FA setup |

---

## Selectors Reference

### Signup Page
```
Sign Up button: text="Sign up" or text="Get started"
Email input: input[name="email"] or input[type="email"]
Password input: input[name="password"] or input[type="password"]
Captcha: handled by SadCaptcha
Verification code: input[placeholder*="code"]
```

### BC Setup
```
Advertiser option: text="Advertiser" or text="I want to advertise"
Country dropdown: select[name="country"] or [data-testid="country"]
Timezone: select containing "UTC"
Not Now button: text="Not now" or text="Skip"
```

### Verification
```
Accounts menu: text="Accounts"
Verification menu: text="Verification"
VAT input: input[name="vat"] or input[placeholder*="VAT"]
Add payment: text="Add payment" or text="Add card"
```

### Campaign Creation
```
Full version toggle: text="Full version" or text="Switch"
Traffic objective: text="Traffic"
Continue button: text="Continue"
Placements checkboxes: [data-testid*="placement"]
Budget input: input[name="budget"]
Schedule input: input[type="date"]
Create New ad: text="Create new" or text="Create"
Upload area: [data-testid="upload"] or input[type="file"]
Audio library: text="Music" or text="Audio"
Text input: input[placeholder*="text"] or textarea
URL input: input[name="url"] or input[placeholder*="URL"]
Publish button: text="Publish" or text="Submit"
```

---

## Error Recovery

| Error | Action |
|-------|--------|
| Captcha fails 3x | Mark account as paused, move to next |
| No automatic payment | Log warning, proxy might be weak |
| SMS timeout | Retry once, then mark failed |
| Unexpected UI | Screenshot, try to recover, pause if stuck |
| "Account suspended" | Mark failed, move to next |
