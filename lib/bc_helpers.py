"""BC setup helpers - names, VAT codes, campaign settings"""

import json
import random
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "bc_setup.json"
USED_NAMES_PATH = Path(__file__).parent.parent / "config" / "used_names.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def load_used_names():
    if USED_NAMES_PATH.exists():
        with open(USED_NAMES_PATH) as f:
            return json.load(f)
    return {"bc_names": [], "ad_account_names": [], "campaign_names": []}

def save_used_names(used):
    with open(USED_NAMES_PATH, "w") as f:
        json.dump(used, f, indent=2)

def generate_unique_name(name_type: str) -> str:
    """Generate unique name for bc/ad_account/campaign - all different"""
    config = load_config()
    used = load_used_names()
    
    key = f"{name_type}_names"
    if key not in used:
        used[key] = []
    
    # Try up to 50 times to get unique name
    for _ in range(50):
        prefix = random.choice(config["name_generator"]["prefixes"])
        suffix = random.choice(config["name_generator"]["suffixes"])
        name = f"{prefix} {suffix}"
        
        # Check not used anywhere
        all_used = used.get("bc_names", []) + used.get("ad_account_names", []) + used.get("campaign_names", [])
        if name not in all_used:
            used[key].append(name)
            save_used_names(used)
            return name
    
    # Fallback: add random number
    name = f"{prefix} {suffix} {random.randint(100, 999)}"
    used[key].append(name)
    save_used_names(used)
    return name

def generate_bc_name() -> str:
    return generate_unique_name("bc")

def generate_ad_account_name() -> str:
    return generate_unique_name("ad_account")

def generate_campaign_name() -> str:
    return generate_unique_name("campaign")

def get_timezone() -> str:
    return "UTC"

def get_vat_code(country: str) -> str:
    config = load_config()
    country = country.upper()
    
    if country not in config["vat_required_countries"]:
        return None
    
    if country in config["vat_codes"]:
        return config["vat_codes"][country]
    
    if config.get("ask_user_if_missing_vat", True):
        print(f"\n[VAT] No VAT code for {country}")
        code = input(f"Enter VAT code for {country} (or Enter to skip): ").strip()
        if code:
            config["vat_codes"][country] = code
            save_config(config)
            print(f"[VAT] Saved {country}: {code}")
            return code
    return None

def needs_vat(country: str) -> bool:
    config = load_config()
    return country.upper() in config["vat_required_countries"]

def get_campaign_objective() -> str:
    """Ask user for campaign objective"""
    config = load_config()
    objectives = config["campaign"]["objectives"]
    default = config["campaign"]["default_objective"]
    
    print("\n[CAMPAIGN] Select objective:")
    for i, obj in enumerate(objectives, 1):
        marker = " (default)" if obj == default else ""
        print(f"  {i}. {obj}{marker}")
    
    choice = input(f"Choose [1-{len(objectives)}] or Enter for {default}: ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(objectives):
        return objectives[int(choice) - 1]
    return default

def get_campaign_settings(currency: str = "USD") -> dict:
    """Get all campaign settings"""
    config = load_config()
    
    return {
        "name": generate_campaign_name(),
        "objective": config["campaign"]["default_objective"],  # Or call get_campaign_objective() to ask
        "budget": "MINIMUM",  # TikTok will use minimum for currency
        "schedule_days": config["campaign"]["schedule_days_ahead"],
        "auto_pause": config["campaign"]["auto_pause_on_approval"],
        "bid_strategy": config["campaign"]["bid_strategy"]
    }
