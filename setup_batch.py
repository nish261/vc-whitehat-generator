#!/usr/bin/env python3
"""
Interactive batch setup for TikTok BC automation
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

CONFIG_PATH = Path(__file__).parent / "config"

def load_specifics():
    with open(CONFIG_PATH / "bc_specifics.json") as f:
        return json.load(f)

def interactive_setup():
    specs = load_specifics()
    
    print("\n" + "=" * 60)
    print("  TikTok BC Batch Setup")
    print("=" * 60)
    
    # 1. How many BCs?
    print("\n[1] How many BCs do you want to create?")
    count = input("    Enter number (1-100): ").strip()
    count = int(count) if count.isdigit() else 1
    
    # 2. BC Type
    print("\n[2] What type of BCs?")
    for key, val in specs["bc_types"].items():
        print(f"    {key}: {val[description]}")
    bc_type = input("    Choose (whitehat/dropship/cpa): ").strip().lower()
    if bc_type not in specs["bc_types"]:
        bc_type = "whitehat"
    
    # 3. Regions
    print("\n[3] Which regions?")
    print("    Available:", ", ".join(specs["regions"].keys()))
    regions_input = input("    Enter regions (comma-separated, or all): ").strip()
    if regions_input.lower() == "all":
        regions = list(specs["regions"].keys())
    else:
        regions = [r.strip().upper() for r in regions_input.split(",")]
        regions = [r for r in regions if r in specs["regions"]]
    if not regions:
        regions = ["IT"]
    
    # 4. Custom URL (for dropship/cpa)
    destination_url = specs["bc_types"][bc_type].get("url", "https://example.com/404")
    if bc_type != "whitehat":
        print(f"\n[4] Destination URL?")
        url_input = input(f"    Enter URL (or press Enter for default): ").strip()
        if url_input:
            destination_url = url_input
    
    # 5. Schedule
    print(f"\n[5] Campaign start date?")
    default_days = specs["bc_types"][bc_type]["schedule_days"]
    print(f"    Default: {default_days} days from now")
    days_input = input(f"    Days ahead (or press Enter for {default_days}): ").strip()
    schedule_days = int(days_input) if days_input.isdigit() else default_days
    
    # 6. Budget per region
    print(f"\n[6] Budget settings:")
    budgets = {}
    for region in regions:
        currency = specs["regions"][region]["currency"]
        min_budget = specs["currencies"][currency]["min_budget"]
        symbol = specs["currencies"][currency]["symbol"]
        print(f"    {region} ({currency}): minimum {symbol}{min_budget}")
        budgets[region] = min_budget
    
    custom_budget = input("    Use minimum budgets? (Y/n): ").strip().lower()
    if custom_budget == "n":
        for region in regions:
            currency = specs["regions"][region]["currency"]
            symbol = specs["currencies"][currency]["symbol"]
            b = input(f"    {region} budget ({symbol}): ").strip()
            if b.isdigit():
                budgets[region] = int(b)
    
    # 7. Confirmation
    print("\n" + "=" * 60)
    print("  BATCH SUMMARY")
    print("=" * 60)
    print(f"  Count:       {count} BCs")
    print(f"  Type:        {bc_type}")
    print(f"  Regions:     {, .join(regions)}")
    print(f"  URL:         {destination_url}")
    print(f"  Start:       +{schedule_days} days")
    print(f"  Budgets:     {budgets}")
    print(f"  Auto-pause:  {specs[bc_types][bc_type][auto_pause]}")
    print("=" * 60)
    
    confirm = input("\n  Proceed? (y/N): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return None
    
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch = {
        "id": batch_id,
        "count": count,
        "bc_type": bc_type,
        "regions": regions,
        "destination_url": destination_url,
        "schedule_days": schedule_days,
        "budgets": budgets,
        "auto_pause": specs["bc_types"][bc_type]["auto_pause"],
        "specs": specs,
        "created_at": datetime.now().isoformat()
    }
    
    batch_path = CONFIG_PATH / f"batch_{batch_id}.json"
    with open(batch_path, "w") as f:
        json.dump(batch, f, indent=2)
    
    print(f"\n  Batch config saved: {batch_path}")
    return batch


def queue_accounts_for_batch(batch):
    from lib.accounts import get_hoot_client, get_proxy_for_region
    from lib.db import add_account
    from datetime import datetime, timedelta
    
    specs = batch["specs"]
    client = get_hoot_client()
    accounts = client.get_accounts()
    fresh = [a for a in accounts if not a.get("used")]
    
    queued = 0
    region_idx = 0
    
    for acc in fresh:
        if queued >= batch["count"]:
            break
        
        region = batch["regions"][region_idx % len(batch["regions"])]
        region_idx += 1
        
        region_spec = specs["regions"][region]
        currency = region_spec["currency"]
        timezone = region_spec["timezone"]
        budget = batch["budgets"].get(region, specs["currencies"][currency]["min_budget"])
        
        schedule_start = (datetime.now() + timedelta(days=batch["schedule_days"])).strftime("%Y-%m-%d")
        
        proxy = get_proxy_for_region(region)
        
        add_account(
            account_id=acc["id"],
            email=acc["email"],
            password=acc["password"],
            region=region,
            proxy=proxy,
            batch_id=batch["id"],
            bc_type=batch["bc_type"],
            destination_url=batch["destination_url"],
            budget=budget,
            currency=currency,
            timezone=timezone,
            schedule_start=schedule_start,
            auto_pause=batch["auto_pause"]
        )
        
        queued += 1
        print(f"  [{queued}/{batch[count]}] {acc[email]} | {region} | {currency}{budget}")
    
    print(f"\n  Total queued: {queued}")
    return queued


if __name__ == "__main__":
    batch = interactive_setup()
    if batch:
        print("\n  Queueing accounts...")
        queue_accounts_for_batch(batch)
        print("\n  Done! Run Hermes to process.")
