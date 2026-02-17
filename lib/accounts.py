"""Account and proxy utilities - wraps existing api_clients.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api_clients import HootServicesClient, VitalProxiesClient
import json

CONFIG_PATH = Path(__file__).parent.parent / "config" / "tiktok_bc_setup_config.json"


def load_config():
    """Load config from JSON"""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_hoot_client() -> HootServicesClient:
    """Get HootServices client"""
    config = load_config()
    return HootServicesClient(
        api_key=config["hootservices"]["api_key"],
        api_url=config["hootservices"]["api_url"]
    )


def get_proxy_client() -> VitalProxiesClient:
    """Get Vital Proxies client"""
    config = load_config()
    vp = config["vital_proxies"]
    return VitalProxiesClient(
        api_key=vp["api_key"],
        api_url=vp["api_url"],
        provider=vp["provider"],
        ttl=vp["ttl"]
    )


def fetch_fresh_account():
    """Fetch a fresh account from HootServices"""
    client = get_hoot_client()
    accounts = client.get_accounts()
    
    fresh = [a for a in accounts if a.get("status") == "fresh" or not a.get("used")]
    
    if fresh:
        account = fresh[0]
        print(f"[ACCOUNTS] Got fresh account: {account.get(email)}")
        return account
    
    print("[ACCOUNTS] No fresh accounts available")
    return None


def get_proxy_for_region(region: str) -> str:
    """Generate proxy for region"""
    client = get_proxy_client()
    proxy = client.generate_proxy(region)
    
    if proxy:
        print(f"[ACCOUNTS] Got proxy for {region}: {proxy[:30]}...")
        return proxy
    
    print(f"[ACCOUNTS] Failed to get proxy for {region}")
    return None


def get_email_verification_code(email: str, max_wait: int = 120) -> str:
    """Poll HootServices for email verification code"""
    client = get_hoot_client()
    code = client.get_verification_code(email, max_wait=max_wait)
    return code
