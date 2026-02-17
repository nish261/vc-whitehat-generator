#!/usr/bin/env python3
"""
Campaign Monitor - runs via cron every 5 minutes
Checks pending campaigns and pauses any that are approved
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.db import get_pending_campaigns, update_account
from lib.tiktok_api import check_and_pause_approved_campaigns

def main():
    print("[MONITOR] Checking pending campaigns...")
    
    pending = get_pending_campaigns()
    print(f"[MONITOR] Found {len(pending)} pending campaigns")
    
    if not pending:
        return
    
    paused = check_and_pause_approved_campaigns(pending)
    print(f"[MONITOR] Paused {len(paused)} campaigns")
    
    for campaign_id in paused:
        for acc in pending:
            if acc.get("campaign_id") == campaign_id:
                update_account(acc["id"], campaign_status="paused")
                print(f"[MONITOR] Updated account {acc[id]} - campaign paused")


if __name__ == "__main__":
    main()
