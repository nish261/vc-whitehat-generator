#!/usr/bin/env python3
"""Quick run - minimal questions, region comes from account"""

from lib.accounts import get_hoot_client, get_proxy_for_region
from lib.db import add_account, export_to_csv

def run():
    print("\n=== TikTok BC Quick Setup ===\n")
    
    count = input("How many BCs? [1]: ").strip()
    count = int(count) if count.isdigit() else 1
    
    print("\nType: (w)hitehat, (d)ropship, (c)pa")
    t = input("Choose [w]: ").strip().lower()
    bc_type = "dropship" if t == "d" else "cpa" if t == "c" else "whitehat"
    
    url = "https://example.com/404"
    if bc_type != "whitehat":
        url = input("Destination URL: ").strip() or url
    
    print(f"\nFetching {count} accounts...")
    client = get_hoot_client()
    accounts = client.get_accounts()
    fresh = [a for a in accounts if not a.get("used")][:count]
    
    if not fresh:
        print("No fresh accounts!")
        return
    
    for i, acc in enumerate(fresh):
        region = acc.get("region", "US")
        proxy = get_proxy_for_region(region)
        
        # Handle proxy as list or string
        if isinstance(proxy, list):
            proxy = proxy[0] if proxy else None
        
        add_account(
            account_id=acc["id"],
            email=acc["email"],
            password=acc["password"],
            region=region,
            proxy=proxy,
            bc_type=bc_type,
            destination_url=url,
            auto_pause=(bc_type == "whitehat")
        )
        print(f"[{i+1}/{len(fresh)}] {acc[email]} | {region}")
    
    csv_path = export_to_csv()
    print(f"\nQueued {len(fresh)} | CSV: {csv_path}")

if __name__ == "__main__":
    run()
