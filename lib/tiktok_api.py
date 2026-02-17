"""TikTok Marketing API utilities for campaign monitoring"""

import requests
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, List

CONFIG_PATH = Path(__file__).parent.parent / "config" / "tiktok_api.json"
BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_access_token(auth_code: str = None) -> Optional[str]:
    """Get access token (requires auth_code from OAuth flow)"""
    config = load_config()
    
    if config.get("access_token"):
        return config["access_token"]
    
    if not auth_code:
        print("[TT_API] No access token or auth code")
        return None
    
    try:
        response = requests.post(
            f"{BASE_URL}/oauth2/access_token/",
            json={
                "app_id": config["app_id"],
                "secret": config["secret"],
                "auth_code": auth_code
            },
            timeout=30
        )
        
        data = response.json()
        if data.get("code") == 0:
            token = data["data"]["access_token"]
            config["access_token"] = token
            save_config(config)
            return token
            
    except Exception as e:
        print(f"[TT_API] Token error: {e}")
    
    return None


def get_campaign_status(access_token: str, advertiser_id: str, campaign_id: str) -> Optional[str]:
    """Get campaign status"""
    try:
        response = requests.get(
            f"{BASE_URL}/campaign/get/",
            headers={"Access-Token": access_token},
            params={
                "advertiser_id": advertiser_id,
                "filtering": json.dumps({"campaign_ids": [campaign_id]})
            },
            timeout=30
        )
        
        data = response.json()
        if data.get("code") == 0:
            campaigns = data.get("data", {}).get("list", [])
            if campaigns:
                status = campaigns[0].get("operation_status")
                print(f"[TT_API] Campaign {campaign_id} status: {status}")
                return status
                
    except Exception as e:
        print(f"[TT_API] Get status error: {e}")
    
    return None


def pause_campaign(access_token: str, advertiser_id: str, campaign_id: str) -> bool:
    """Pause a campaign"""
    try:
        response = requests.post(
            f"{BASE_URL}/campaign/status/update/",
            headers={"Access-Token": access_token},
            json={
                "advertiser_id": advertiser_id,
                "campaign_ids": [campaign_id],
                "operation_status": "DISABLE"
            },
            timeout=30
        )
        
        data = response.json()
        if data.get("code") == 0:
            print(f"[TT_API] Paused campaign {campaign_id}")
            return True
        else:
            print(f"[TT_API] Pause failed: {data.get(message)}")
            
    except Exception as e:
        print(f"[TT_API] Pause error: {e}")
    
    return False


def check_and_pause_approved_campaigns(accounts: List[Dict]) -> List[str]:
    """Check campaigns and pause any that are approved"""
    config = load_config()
    access_token = config.get("access_token")
    
    if not access_token:
        print("[TT_API] No access token configured")
        return []
    
    paused = []
    
    for account in accounts:
        campaign_id = account.get("campaign_id")
        advertiser_id = account.get("bc_id")
        
        if not campaign_id or not advertiser_id:
            continue
        
        status = get_campaign_status(access_token, advertiser_id, campaign_id)
        
        if status == "CAMPAIGN_STATUS_ENABLE":
            if pause_campaign(access_token, advertiser_id, campaign_id):
                paused.append(campaign_id)
    
    return paused
