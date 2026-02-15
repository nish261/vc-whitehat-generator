#!/usr/bin/env python3
"""
TikTok White Hat Campaign Creator
Standalone script for creating dummy/warming campaigns on TikTok Ads Manager

Usage:
    # Batch mode from CSV
    python tiktok_whitehat_creator.py --input accounts.csv --output results.csv

    # Single account mode
    python tiktok_whitehat_creator.py --email user@email.com --password Pass123! --bc_id 12345678

    # With custom config
    python tiktok_whitehat_creator.py --input accounts.csv --config config/whitehat_config.json
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

from adspower_manager import AdsPowerManager
from tiktok_ads_automation import TikTokAdsAutomation


class WhiteHatCreator:
    """Orchestrates White Hat campaign creation across multiple accounts"""

    def __init__(self, config_file: str = "config/whitehat_config.json"):
        """Initialize White Hat creator"""
        self.config = self._load_config(config_file)
        self.adspower = AdsPowerManager()
        self.results = []
        self.output_file = None

    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load config: {e}")

        return {
            "delays": {"between_accounts": [45, 90]},
            "retries": {"max_retries": 3, "retry_delay": [5, 10]}
        }

    def load_accounts_from_csv(self, csv_file: str) -> List[Dict]:
        """
        Load accounts from CSV file

        Expected columns: email, password, business_center_id, proxy, status
        """
        accounts = []

        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Skip already processed accounts
                    status = row.get('status', 'pending').lower()
                    if status in ['completed', 'success', 'done']:
                        continue

                    accounts.append({
                        'email': row.get('email', '').strip(),
                        'password': row.get('password', '').strip(),
                        'business_center_id': row.get('business_center_id', '').strip(),
                        'proxy': row.get('proxy', '').strip(),
                        'status': status
                    })

            print(f"[INFO] Loaded {len(accounts)} pending accounts from {csv_file}")
            return accounts

        except Exception as e:
            print(f"[ERR] Failed to load CSV: {e}")
            return []

    def save_result(self, result: Dict):
        """Save result to output file"""
        if not self.output_file:
            return

        try:
            # Check if file exists to determine if we need headers
            file_exists = Path(self.output_file).exists()

            with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'timestamp', 'email', 'business_center_id', 'whitehat_campaign_id',
                    'landing_url', 'status', 'screenshot_path', 'error_message',
                    'steps_completed', 'proxy'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'email': result.get('email', ''),
                    'business_center_id': result.get('business_center_id', ''),
                    'whitehat_campaign_id': result.get('campaign_id', ''),
                    'landing_url': result.get('landing_url', ''),
                    'status': 'success' if result.get('success') else 'failed',
                    'screenshot_path': result.get('screenshot_path', ''),
                    'error_message': result.get('error_message', ''),
                    'steps_completed': ','.join(result.get('steps_completed', [])),
                    'proxy': result.get('proxy', '')
                })

        except Exception as e:
            print(f"[WARN] Failed to save result: {e}")

    def process_account(
        self,
        email: str,
        password: str,
        business_center_id: str,
        proxy: Optional[str] = None
    ) -> Dict:
        """
        Process a single account to create White Hat campaign

        Args:
            email: Account email
            password: Account password
            business_center_id: TikTok Business Center ID
            proxy: Optional proxy string

        Returns:
            Dict with result
        """
        result = {
            'email': email,
            'business_center_id': business_center_id,
            'proxy': proxy,
            'success': False,
            'campaign_id': None,
            'landing_url': None,
            'screenshot_path': None,
            'error_message': None,
            'steps_completed': []
        }

        profile_id = None
        automation = None

        try:
            print(f"\n{'='*60}")
            print(f"Processing: {email}")
            print(f"Business Center ID: {business_center_id}")
            print(f"{'='*60}\n")

            # Step 1: Create AdsPower profile
            print("[1/4] Creating AdsPower profile...")

            profile_name = f"whitehat_{email.split('@')[0]}_{int(time.time())}"
            profile_id = self.adspower.create_profile(
                profile_name=profile_name,
                proxy_string=proxy
            )

            if not profile_id:
                result['error_message'] = "Failed to create AdsPower profile"
                return result

            result['steps_completed'].append('profile_created')

            # Step 2: Launch browser
            print("[2/4] Launching browser...")

            launch_info = self.adspower.launch_profile(profile_id)

            if not launch_info or not launch_info.get('debug_port'):
                result['error_message'] = "Failed to launch AdsPower browser"
                return result

            debug_port = launch_info['debug_port']
            result['steps_completed'].append('browser_launched')

            # Wait for browser to fully initialize
            time.sleep(3)

            # Step 3: Connect Selenium and create automation
            print("[3/4] Connecting Selenium...")

            automation = TikTokAdsAutomation()

            if not automation.connect_to_adspower_browser(debug_port):
                result['error_message'] = "Failed to connect Selenium to browser"
                return result

            result['steps_completed'].append('selenium_connected')

            # Step 4: Create White Hat campaign
            print("[4/4] Creating White Hat campaign...")

            campaign_result = automation.create_whitehat_campaign()

            # Merge results
            result['success'] = campaign_result.get('success', False)
            result['campaign_id'] = campaign_result.get('campaign_id')
            result['landing_url'] = campaign_result.get('landing_url')
            result['screenshot_path'] = campaign_result.get('screenshot_path')
            result['error_message'] = campaign_result.get('error_message')
            result['steps_completed'].extend(campaign_result.get('steps_completed', []))

            if result['success']:
                print(f"\n[SUCCESS] White Hat campaign created for {email}")
                if result['campaign_id']:
                    print(f"          Campaign ID: {result['campaign_id']}")
            else:
                print(f"\n[FAILED] Could not create campaign for {email}")
                print(f"         Error: {result['error_message']}")

        except Exception as e:
            result['error_message'] = f"Exception: {str(e)[:200]}"
            print(f"[ERR] Exception processing {email}: {e}")

        finally:
            # Cleanup
            if automation:
                try:
                    automation.cleanup()
                except:
                    pass

            if profile_id:
                print("\n[CLEANUP] Closing browser profile...")
                time.sleep(1)
                self.adspower.close_profile(profile_id)

                # Optionally delete profile (uncomment if desired)
                # self.adspower.delete_profile(profile_id)

        return result

    def run_batch(self, input_file: str, output_file: str):
        """
        Run batch processing of accounts from CSV

        Args:
            input_file: Path to input CSV
            output_file: Path to output CSV
        """
        self.output_file = output_file

        # Check AdsPower connection
        print("\n[PREFLIGHT] Checking AdsPower connection...")

        if not self.adspower.check_api_connection():
            print("[ERR] AdsPower is not running or API is not accessible")
            print("      Please start AdsPower and enable the local API")
            return

        print("[OK] AdsPower connected\n")

        # Load accounts
        accounts = self.load_accounts_from_csv(input_file)

        if not accounts:
            print("[ERR] No accounts to process")
            return

        # Process each account
        total = len(accounts)
        success_count = 0
        fail_count = 0

        for i, account in enumerate(accounts, 1):
            print(f"\n{'#'*60}")
            print(f"Account {i}/{total}")
            print(f"{'#'*60}")

            result = self.process_account(
                email=account['email'],
                password=account['password'],
                business_center_id=account['business_center_id'],
                proxy=account.get('proxy')
            )

            self.results.append(result)
            self.save_result(result)

            if result['success']:
                success_count += 1
            else:
                fail_count += 1

            # Rate limiting between accounts
            if i < total:
                delays = self.config.get("delays", {}).get("between_accounts", [45, 90])
                wait_time = random.uniform(delays[0], delays[1])
                print(f"\n[WAIT] Waiting {wait_time:.0f}s before next account...")
                time.sleep(wait_time)

        # Print summary
        print(f"\n{'='*60}")
        print("BATCH COMPLETE")
        print(f"{'='*60}")
        print(f"Total:   {total}")
        print(f"Success: {success_count}")
        print(f"Failed:  {fail_count}")
        print(f"Results: {output_file}")
        print(f"{'='*60}\n")

    def run_single(
        self,
        email: str,
        password: str,
        business_center_id: str,
        proxy: Optional[str] = None,
        output_file: Optional[str] = None
    ):
        """
        Run single account processing

        Args:
            email: Account email
            password: Account password
            business_center_id: TikTok Business Center ID
            proxy: Optional proxy string
            output_file: Optional output file
        """
        if output_file:
            self.output_file = output_file

        # Check AdsPower connection
        print("\n[PREFLIGHT] Checking AdsPower connection...")

        if not self.adspower.check_api_connection():
            print("[ERR] AdsPower is not running or API is not accessible")
            return

        print("[OK] AdsPower connected\n")

        # Process the account
        result = self.process_account(
            email=email,
            password=password,
            business_center_id=business_center_id,
            proxy=proxy
        )

        if output_file:
            self.save_result(result)

        # Print result
        print(f"\n{'='*60}")
        print("RESULT")
        print(f"{'='*60}")
        print(f"Email:       {result['email']}")
        print(f"Status:      {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Campaign ID: {result.get('campaign_id', 'N/A')}")
        print(f"Landing URL: {result.get('landing_url', 'N/A')}")

        if result.get('error_message'):
            print(f"Error:       {result['error_message']}")

        if result.get('screenshot_path'):
            print(f"Screenshot:  {result['screenshot_path']}")

        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='TikTok White Hat Campaign Creator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Batch mode from CSV
  python tiktok_whitehat_creator.py --input accounts.csv --output results.csv

  # Single account mode
  python tiktok_whitehat_creator.py --email user@email.com --password Pass123! --bc_id 12345678

  # With proxy
  python tiktok_whitehat_creator.py --email user@email.com --password Pass123! --bc_id 12345678 --proxy host:port:user:pass

  # With custom config
  python tiktok_whitehat_creator.py --input accounts.csv --config config/whitehat_config.json
        """
    )

    # Batch mode arguments
    parser.add_argument('--input', '-i', help='Input CSV file with accounts')
    parser.add_argument('--output', '-o', help='Output CSV file for results')

    # Single account arguments
    parser.add_argument('--email', '-e', help='Account email')
    parser.add_argument('--password', '-p', help='Account password')
    parser.add_argument('--bc_id', '-b', help='Business Center ID')
    parser.add_argument('--proxy', help='Proxy string (host:port:user:pass)')

    # Config
    parser.add_argument('--config', '-c', default='config/whitehat_config.json',
                        help='Config file path')

    args = parser.parse_args()

    # Validate arguments
    if args.input:
        # Batch mode
        if not args.output:
            args.output = f"whitehat_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        creator = WhiteHatCreator(config_file=args.config)
        creator.run_batch(args.input, args.output)

    elif args.email and args.password and args.bc_id:
        # Single account mode
        creator = WhiteHatCreator(config_file=args.config)
        creator.run_single(
            email=args.email,
            password=args.password,
            business_center_id=args.bc_id,
            proxy=args.proxy,
            output_file=args.output
        )

    else:
        print("Error: Either provide --input for batch mode or --email, --password, --bc_id for single mode")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
