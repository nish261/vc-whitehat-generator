"""SMS verification utilities - wraps existing api_clients.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api_clients import SMSPoolClient
import json

CONFIG_PATH = Path(__file__).parent.parent / "config" / "tiktok_bc_setup_config.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_sms_client() -> SMSPoolClient:
    """Get SMSPool client"""
    config = load_config()
    sms = config["sms"]
    return SMSPoolClient(
        api_key=sms["api_key"],
        api_url=sms["api_url"],
        poll_interval=sms["poll_interval"],
        max_wait=sms["max_wait_seconds"]
    )


def order_phone_number(region: str) -> dict:
    """
    Order a phone number for TikTok verification
    
    Returns:
        {"order_id": str, "phone_number": str} or None
    """
    client = get_sms_client()
    result = client.order_number(region, service="tiktok")
    
    if result:
        print(f"[SMS] Got number: {result.get(phone_number)}")
        return result
    
    print(f"[SMS] Failed to order number for {region}")
    return None


def get_sms_code(order_id: str, max_wait: int = 120) -> str:
    """
    Poll for SMS verification code
    
    Args:
        order_id: Order ID from order_phone_number
        max_wait: Max seconds to wait
        
    Returns:
        Verification code or None
    """
    client = get_sms_client()
    code = client.get_code(order_id, max_wait=max_wait)
    
    if code:
        print(f"[SMS] Got code: {code}")
        return code
    
    print(f"[SMS] Timeout waiting for code")
    return None


def cancel_order(order_id: str) -> bool:
    """Cancel SMS order if not used"""
    client = get_sms_client()
    return client.cancel_order(order_id)
