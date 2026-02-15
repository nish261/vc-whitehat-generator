#!/usr/bin/env python3
"""
TikTok Full Setup Automation
Complete flow: Fresh BC account -> Fully configured -> White Hat campaign

Usage:
    # Process all accounts
    python tiktok_full_setup.py --all

    # Process specific number of accounts
    python tiktok_full_setup.py --count 5

    # Process single account by ID
    python tiktok_full_setup.py --account-id 550e8400-e29b-41d4-a716-446655440000

    # Dry run (fetch accounts, don't process)
    python tiktok_full_setup.py --dry-run
"""

import argparse
import csv
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from api_clients import HootServicesClient, VitalProxiesClient, SMSPoolClient, load_config, create_clients
from adspower_manager import AdsPowerManager
from tiktok_bc_setup import TikTokBCSetup
from tiktok_ads_automation import TikTokAdsAutomation


class TikTokFullSetup:
    """
    Main orchestrator for complete TikTok setup flow

    Flow per account:
    1. Fetch account from HootServices
    2. Generate proxy matching region (Vital Proxies)
    3. Create AdsPower profile with proxy
    4. Login to TikTok
    5. Setup Business Center
    6. Create advertiser account (with email/SMS verification)
    7. Create White Hat campaign
    8. Log results
    """

    def __init__(self, config_file: str = "config/tiktok_bc_setup_config.json"):
        """Initialize full setup orchestrator"""
        self.config = load_config(config_file)
        self.clients = create_clients(self.config)
        self.adspower = AdsPowerManager()
        self.results = []
        self.output_file = f"tiktok_setup_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Track processed accounts
        self.processed_file = "processed_accounts.json"
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        """Load previously processed account IDs"""
        try:
            if Path(self.processed_file).exists():
                with open(self.processed_file, 'r') as f:
                    return set(json.load(f))
        except:
            pass
        return set()

    def _save_processed_id(self, account_id: str):
        """Save processed account ID"""
        self.processed_ids.add(account_id)
        try:
            with open(self.processed_file, 'w') as f:
                json.dump(list(self.processed_ids), f)
        except:
            pass

    def preflight_check(self) -> bool:
        """Check all systems before starting"""
        print("\n" + "="*60)
        print("PREFLIGHT CHECK")
        print("="*60 + "\n")

        all_ok = True

        # Check AdsPower
        print("[1/4] Checking AdsPower...")
        if self.adspower.check_api_connection():
            print("      [OK] AdsPower connected")
        else:
            print("      [ERR] AdsPower not running")
            all_ok = False

        # Check HootServices
        print("[2/4] Checking HootServices...")
        if "hootservices" in self.clients:
            stats = self.clients["hootservices"].get_stats()
            accounts = self.clients["hootservices"].get_accounts()
            print(f"      [OK] {len(accounts)} accounts available")
            print(f"      Stats: {stats.get('successful', 0)} successful, {stats.get('business_centers', 0)} BCs")
        else:
            print("      [ERR] HootServices not configured")
            all_ok = False

        # Check Vital Proxies
        print("[3/4] Checking Vital Proxies...")
        if "vital_proxies" in self.clients:
            usage = self.clients["vital_proxies"].get_usage()
            used = float(usage.get("used", 0))
            total = float(usage.get("total", 0))
            remaining = total - used
            print(f"      [OK] {remaining:.2f}GB remaining ({used:.2f}/{total:.2f}GB used)")
            if remaining < 1:
                print("      [WARN] Low proxy data!")
        else:
            print("      [ERR] Vital Proxies not configured")
            all_ok = False

        # Check SMSPool
        print("[4/4] Checking SMSPool...")
        if "sms" in self.clients:
            balance = self.clients["sms"].get_balance()
            if balance:
                print(f"      [OK] Balance: ${balance:.2f}")
                if balance < 5:
                    print("      [WARN] Low SMS balance!")
            else:
                print("      [WARN] Could not get SMS balance")
        else:
            print("      [WARN] SMSPool not configured (SMS verification may fail)")

        print("\n" + "="*60)
        if all_ok:
            print("PREFLIGHT: ALL SYSTEMS GO")
        else:
            print("PREFLIGHT: SOME CHECKS FAILED")
        print("="*60 + "\n")

        return all_ok

    def get_pending_accounts(self, limit: Optional[int] = None) -> List[Dict]:
        """Get accounts that haven't been processed yet"""
        if "hootservices" not in self.clients:
            return []

        all_accounts = self.clients["hootservices"].get_accounts()

        # Filter out already processed
        pending = [
            acc for acc in all_accounts
            if acc["id"] not in self.processed_ids
        ]

        if limit:
            pending = pending[:limit]

        return pending

    def process_account(self, account: Dict) -> Dict:
        """
        Process a single account through the full flow

        Args:
            account: Account dict from HootServices

        Returns:
            Result dict
        """
        result = {
            "account_id": account["id"],
            "email": account["email"],
            "region": account["region"],
            "currency": account["currency"],
            "success": False,
            "logged_in": False,
            "bc_setup": False,
            "ad_account_id": None,
            "whitehat_campaign_id": None,
            "proxy_used": None,
            "adspower_profile_id": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }

        profile_id = None
        bc_setup = None
        ads_automation = None

        try:
            print(f"\n{'#'*60}")
            print(f"Processing Account: {account['email']}")
            print(f"Region: {account['region']} | Currency: {account['currency']}")
            print(f"{'#'*60}\n")

            # Step 1: Generate proxy for region
            print("[STEP 1/7] Generating proxy...")
            proxies = self.clients["vital_proxies"].generate_proxy(account["region"])

            if not proxies:
                result["error"] = "Failed to generate proxy"
                return result

            proxy_string = proxies[0]
            adspower_proxy = self.clients["vital_proxies"].format_for_adspower(proxy_string)
            result["proxy_used"] = proxy_string
            print(f"  Proxy: {proxy_string[:50]}...")

            # Step 2: Create AdsPower profile
            print("\n[STEP 2/7] Creating AdsPower profile...")
            profile_name = f"tiktok_{account['region']}_{account['id'][:8]}"
            profile_id = self.adspower.create_profile(
                profile_name=profile_name,
                proxy_string=adspower_proxy
            )

            if not profile_id:
                result["error"] = "Failed to create AdsPower profile"
                return result

            result["adspower_profile_id"] = profile_id

            # Step 3: Launch browser
            print("\n[STEP 3/7] Launching browser...")
            launch_info = self.adspower.launch_profile(profile_id)

            if not launch_info or not launch_info.get("debug_port"):
                result["error"] = "Failed to launch browser"
                return result

            debug_port = launch_info["debug_port"]
            time.sleep(3)  # Wait for browser to initialize

            # Step 4: Connect and setup BC
            print("\n[STEP 4/7] Setting up Business Center...")
            bc_setup = TikTokBCSetup(self.config)

            if not bc_setup.connect_to_adspower_browser(debug_port):
                result["error"] = "Failed to connect Selenium"
                return result

            # Set verification callbacks
            bc_setup.email_code_callback = lambda email: self._get_email_code(account["id"], email)
            bc_setup.sms_code_callback = lambda: self._get_sms_code(account["region"])

            # Run BC setup
            setup_result = bc_setup.full_setup(
                email=account["email"],
                password=account["password"],
                region=account["region"],
                business_name=f"Business {account['region']}"
            )

            result["logged_in"] = setup_result.get("logged_in", False)
            result["bc_setup"] = setup_result.get("bc_setup", False)
            result["ad_account_id"] = setup_result.get("ad_account_id")

            if not result["bc_setup"]:
                result["error"] = setup_result.get("error", "BC setup failed")
                return result

            # Step 5: Navigate to Ads Manager
            print("\n[STEP 5/7] Navigating to Ads Manager...")
            bc_setup.driver.get("https://ads.tiktok.com/i18n/home")
            time.sleep(5)

            # Step 6: Create White Hat campaign
            print("\n[STEP 6/7] Creating White Hat campaign...")
            ads_automation = TikTokAdsAutomation()
            ads_automation.driver = bc_setup.driver
            ads_automation.wait = bc_setup.wait

            campaign_result = ads_automation.create_whitehat_campaign()

            if campaign_result.get("success"):
                result["whitehat_campaign_id"] = campaign_result.get("campaign_id")
                result["success"] = True
                print(f"\n[SUCCESS] Account fully set up!")
            else:
                result["error"] = campaign_result.get("error_message", "White Hat creation failed")

            # Step 7: Mark as processed
            print("\n[STEP 7/7] Saving results...")
            self._save_processed_id(account["id"])

        except Exception as e:
            result["error"] = str(e)[:200]
            print(f"\n[ERROR] {e}")

        finally:
            # Cleanup
            if bc_setup:
                try:
                    bc_setup.cleanup()
                except:
                    pass

            if profile_id:
                print("\n[CLEANUP] Closing browser...")
                time.sleep(1)
                self.adspower.close_profile(profile_id)

        return result

    def _get_email_code(self, account_id: str, email: str) -> Optional[str]:
        """Get email verification code from HootServices"""
        if "hootservices" not in self.clients:
            return None

        print(f"  [VERIFY] Waiting for email code for {email}...")
        return self.clients["hootservices"].get_verification_code(email, max_wait=120)

    def _get_sms_code(self, region: str) -> Optional[Dict]:
        """Get SMS verification (number + code) from SMSPool"""
        if "sms" not in self.clients:
            return None

        print(f"  [VERIFY] Getting SMS number for region {region}...")
        return self.clients["sms"].get_number_and_code(region)

    def save_result(self, result: Dict):
        """Save result to CSV"""
        try:
            file_exists = Path(self.output_file).exists()

            with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'timestamp', 'account_id', 'email', 'region', 'currency',
                    'success', 'logged_in', 'bc_setup', 'ad_account_id',
                    'whitehat_campaign_id', 'adspower_profile_id', 'proxy_used', 'error'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({k: result.get(k, '') for k in fieldnames})

        except Exception as e:
            print(f"[WARN] Failed to save result: {e}")

    def run(self, count: Optional[int] = None, account_id: Optional[str] = None, dry_run: bool = False):
        """
        Run the full setup automation

        Args:
            count: Number of accounts to process (None = all)
            account_id: Specific account ID to process
            dry_run: Just show accounts, don't process
        """
        # Preflight check
        if not self.preflight_check():
            print("\n[ABORT] Preflight check failed. Fix issues and retry.")
            return

        # Get accounts to process
        if account_id:
            # Single account mode
            account = self.clients["hootservices"].get_account(account_id)
            if not account:
                print(f"[ERROR] Account not found: {account_id}")
                return
            accounts = [account]
        else:
            # Batch mode
            accounts = self.get_pending_accounts(limit=count)

        if not accounts:
            print("\n[INFO] No pending accounts to process")
            return

        print(f"\n[INFO] {len(accounts)} account(s) to process")

        if dry_run:
            print("\n[DRY RUN] Accounts that would be processed:")
            for acc in accounts:
                print(f"  - {acc['email']} ({acc['region']}) [{acc['id'][:8]}...]")
            return

        # Process accounts
        success_count = 0
        fail_count = 0

        for i, account in enumerate(accounts, 1):
            print(f"\n{'='*60}")
            print(f"ACCOUNT {i}/{len(accounts)}")
            print(f"{'='*60}")

            result = self.process_account(account)
            self.results.append(result)
            self.save_result(result)

            if result["success"]:
                success_count += 1
            else:
                fail_count += 1

            # Rate limiting between accounts
            if i < len(accounts):
                delays = self.config.get("delays", {}).get("between_accounts", [60, 120])
                wait_time = random.uniform(delays[0], delays[1])
                print(f"\n[WAIT] {wait_time:.0f}s before next account...")
                time.sleep(wait_time)

        # Summary
        print(f"\n{'='*60}")
        print("BATCH COMPLETE")
        print(f"{'='*60}")
        print(f"Total:   {len(accounts)}")
        print(f"Success: {success_count}")
        print(f"Failed:  {fail_count}")
        print(f"Results: {self.output_file}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='TikTok Full Setup Automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all pending accounts
  python tiktok_full_setup.py --all

  # Process 5 accounts
  python tiktok_full_setup.py --count 5

  # Process specific account
  python tiktok_full_setup.py --account-id 550e8400-e29b-41d4-a716-446655440000

  # Dry run (show accounts without processing)
  python tiktok_full_setup.py --dry-run

  # Skip preflight checks
  python tiktok_full_setup.py --count 5 --skip-preflight
        """
    )

    parser.add_argument('--all', action='store_true', help='Process all pending accounts')
    parser.add_argument('--count', '-n', type=int, help='Number of accounts to process')
    parser.add_argument('--account-id', '-a', help='Specific account ID to process')
    parser.add_argument('--dry-run', action='store_true', help='Show accounts without processing')
    parser.add_argument('--config', '-c', default='config/tiktok_bc_setup_config.json', help='Config file')
    parser.add_argument('--skip-preflight', action='store_true', help='Skip preflight checks')

    args = parser.parse_args()

    # Validate arguments
    if not (args.all or args.count or args.account_id or args.dry_run):
        print("Error: Specify --all, --count, --account-id, or --dry-run")
        parser.print_help()
        sys.exit(1)

    # Create orchestrator
    setup = TikTokFullSetup(config_file=args.config)

    # Determine count
    count = None
    if args.count:
        count = args.count
    elif not args.all and not args.account_id:
        count = 1  # Default to 1 if nothing specified

    # Run
    setup.run(
        count=count,
        account_id=args.account_id,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
