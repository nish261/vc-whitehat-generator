"""
API Clients for TikTok BC Setup Automation
- HootServices: Account management + email verification
- Vital Proxies: Residential proxy generation
- SMS-Man: Phone verification
"""

import requests
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote


class HootServicesClient:
    """Client for HootServices TikTok BC Account API"""

    def __init__(self, api_key: str, api_url: str = "https://api.hootservices.com"):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_accounts(self) -> List[Dict]:
        """Get all accounts"""
        try:
            response = requests.get(
                f"{self.api_url}/api/user/accounts",
                headers=self.headers,
                timeout=30
            )
            data = response.json()

            if data.get("success"):
                return data.get("accounts", [])
            else:
                print(f"[HootServices] Error: {data.get('error')}")
                return []

        except Exception as e:
            print(f"[HootServices] Exception: {e}")
            return []

    def get_account(self, account_id: str) -> Optional[Dict]:
        """Get specific account by ID"""
        try:
            response = requests.get(
                f"{self.api_url}/api/user/accounts/{account_id}",
                headers=self.headers,
                timeout=30
            )
            data = response.json()

            if data.get("success"):
                return data.get("account")
            return None

        except Exception as e:
            print(f"[HootServices] Exception: {e}")
            return None

    def get_verification_code(self, email: str, max_wait: int = 120, poll_interval: int = 5) -> Optional[str]:
        """
        Get email verification code for an account

        Args:
            email: Account email
            max_wait: Maximum seconds to wait for code
            poll_interval: Seconds between polls

        Returns:
            Verification code if found, None otherwise
        """
        encoded_email = quote(email)
        start_time = time.time()

        print(f"[HootServices] Waiting for verification code for {email}...")

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.api_url}/api/user/codes?email={encoded_email}",
                    headers=self.headers,
                    timeout=30
                )
                data = response.json()

                if data.get("success") and data.get("found"):
                    code = data.get("code")
                    print(f"[HootServices] Got verification code: {code}")
                    return code

                time.sleep(poll_interval)

            except Exception as e:
                print(f"[HootServices] Poll error: {e}")
                time.sleep(poll_interval)

        print(f"[HootServices] Timeout waiting for verification code")
        return None

    def get_code_by_account_id(self, account_id: str, max_wait: int = 120, poll_interval: int = 5) -> Optional[str]:
        """Get verification code by account ID"""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.api_url}/api/user/accounts/{account_id}/code",
                    headers=self.headers,
                    timeout=30
                )
                data = response.json()

                if data.get("success") and data.get("found"):
                    return data.get("code")

                time.sleep(poll_interval)

            except Exception as e:
                print(f"[HootServices] Poll error: {e}")
                time.sleep(poll_interval)

        return None

    def get_stats(self) -> Dict:
        """Get account statistics"""
        try:
            response = requests.get(
                f"{self.api_url}/api/user/stats",
                headers=self.headers,
                timeout=30
            )
            data = response.json()

            if data.get("success"):
                return data.get("stats", {})
            return {}

        except Exception as e:
            print(f"[HootServices] Exception: {e}")
            return {}


class VitalProxiesClient:
    """Client for Vital Proxies Residential Proxy API"""

    # Map account regions to proxy country codes
    REGION_MAP = {
        "US": "us",
        "IT": "it",
        "FR": "fr",
        "DE": "de",
        "NL": "nl",
        "GB": "gb",
        "AU": "au",
        "CA": "ca",
        "ES": "es",
        "BR": "br"
    }

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.vital-proxies.com",
        provider: str = "royal",
        ttl: int = 3600,
        proxy_format: str = "user:pass@ip:port"
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.provider = provider
        self.ttl = ttl
        self.proxy_format = proxy_format
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }

    def get_usage(self) -> Dict:
        """Get data usage for current provider"""
        try:
            response = requests.post(
                f"{self.api_url}/customer/usage",
                headers=self.headers,
                json={"provider": self.provider},
                timeout=30
            )
            data = response.json()

            if data.get("success"):
                return data.get("data", {})
            return {}

        except Exception as e:
            print(f"[VitalProxies] Exception: {e}")
            return {}

    def generate_proxy(self, region: str, quantity: int = 1) -> List[str]:
        """
        Generate residential proxy for a region

        Args:
            region: Account region (US, IT, FR, etc.)
            quantity: Number of proxies to generate

        Returns:
            List of proxy strings
        """
        country_code = self.REGION_MAP.get(region.upper(), region.lower())

        try:
            response = requests.post(
                f"{self.api_url}/customer/generate",
                headers=self.headers,
                json={
                    "provider": self.provider,
                    "is_sticky": True,
                    "quantity": quantity,
                    "format": self.proxy_format,
                    "location": country_code,
                    "ttl": self.ttl
                },
                timeout=30
            )
            data = response.json()

            if data.get("success"):
                proxies = data.get("data", [])
                print(f"[VitalProxies] Generated {len(proxies)} proxy(s) for {country_code.upper()}")
                return proxies
            else:
                print(f"[VitalProxies] Error: {data.get('error')}")
                return []

        except Exception as e:
            print(f"[VitalProxies] Exception: {e}")
            return []

    def format_for_adspower(self, proxy_string: str) -> str:
        """
        Convert proxy string to AdsPower format

        Input: user:pass@ip:port
        Output: ip:port:user:pass
        """
        try:
            if "@" in proxy_string:
                auth, server = proxy_string.split("@")
                user, password = auth.split(":")
                host, port = server.split(":")
                return f"{host}:{port}:{user}:{password}"
            return proxy_string
        except:
            return proxy_string


class SMSPoolClient:
    """Client for SMSPool Phone Verification API"""

    # TikTok service ID for SMSPool
    TIKTOK_SERVICE_ID = "924"

    # Country ID mapping for SMSPool
    COUNTRY_MAP = {
        "US": "1",
        "IT": "14",
        "FR": "12",
        "DE": "9",
        "NL": "5",
        "GB": "2",
        "AU": "7",
        "CA": "20",
        "ES": "8",
        "BR": "6"
    }

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.smspool.net",
        poll_interval: int = 5,
        max_wait: int = 120
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.poll_interval = poll_interval
        self.max_wait = max_wait
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }

    def get_balance(self) -> Optional[float]:
        """Get account balance"""
        try:
            response = requests.post(
                f"{self.api_url}/request/balance",
                headers=self.headers,
                timeout=30
            )
            data = response.json()
            balance = data.get("balance")
            if balance:
                print(f"[SMSPool] Balance: ${balance}")
                return float(balance)
            return None

        except Exception as e:
            print(f"[SMSPool] Exception: {e}")
            return None

    def get_number(self, region: str, service_id: str = None) -> Optional[Dict]:
        """
        Get a phone number for TikTok verification

        Args:
            region: Account region (US, IT, etc.)
            service_id: Service ID (default: TikTok = 924)

        Returns:
            Dict with 'order_id' and 'number' if successful
        """
        country_id = self.COUNTRY_MAP.get(region.upper(), "1")
        service = service_id or self.TIKTOK_SERVICE_ID

        try:
            response = requests.post(
                f"{self.api_url}/purchase/sms",
                headers=self.headers,
                data={
                    "country": country_id,
                    "service": service
                },
                timeout=30
            )
            data = response.json()

            if data.get("success") == 1 or data.get("order_id"):
                result = {
                    "order_id": data.get("order_id"),
                    "number": data.get("phonenumber") or data.get("number"),
                    "country": data.get("country")
                }
                print(f"[SMSPool] Got number: {result['number']}")
                return result
            else:
                print(f"[SMSPool] Error getting number: {data}")
                return None

        except Exception as e:
            print(f"[SMSPool] Exception: {e}")
            return None

    def check_sms(self, order_id: str) -> Optional[str]:
        """
        Check if SMS code has been received

        Args:
            order_id: Order ID from get_number

        Returns:
            SMS code if received, None otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/sms/check",
                headers=self.headers,
                data={"orderid": order_id},
                timeout=30
            )
            data = response.json()

            # SMSPool returns sms field with the code
            sms_code = data.get("sms")
            if sms_code and sms_code != "":
                return sms_code

            return None

        except Exception as e:
            print(f"[SMSPool] Exception: {e}")
            return None

    def get_sms(self, order_id: str) -> Optional[str]:
        """
        Wait for SMS code

        Args:
            order_id: Order ID from get_number

        Returns:
            SMS code if received, None otherwise
        """
        start_time = time.time()

        print(f"[SMSPool] Waiting for SMS code (order: {order_id})...")

        while time.time() - start_time < self.max_wait:
            code = self.check_sms(order_id)
            if code:
                print(f"[SMSPool] Got SMS code: {code}")
                return code

            time.sleep(self.poll_interval)

        print(f"[SMSPool] Timeout waiting for SMS")
        return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel/refund an order"""
        try:
            response = requests.post(
                f"{self.api_url}/sms/cancel",
                headers=self.headers,
                data={"orderid": order_id},
                timeout=30
            )
            data = response.json()
            return data.get("success") == 1

        except Exception as e:
            print(f"[SMSPool] Exception: {e}")
            return False

    def get_number_and_code(self, region: str) -> Optional[Dict]:
        """
        Complete flow: get number, wait for code

        Returns:
            Dict with 'number', 'code', 'order_id' if successful
        """
        # Get number
        number_info = self.get_number(region)
        if not number_info:
            return None

        # Wait for code
        code = self.get_sms(number_info["order_id"])

        if code:
            return {
                "number": number_info["number"],
                "code": code,
                "order_id": number_info["order_id"]
            }
        else:
            # Cancel to get refund
            self.cancel_order(number_info["order_id"])
            return None


def load_config(config_file: str = "config/tiktok_bc_setup_config.json") -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def create_clients(config: Dict = None) -> Dict:
    """Create all API clients from config"""
    if config is None:
        config = load_config()

    clients = {}

    # HootServices
    hs_config = config.get("hootservices", {})
    if hs_config.get("api_key"):
        clients["hootservices"] = HootServicesClient(
            api_key=hs_config["api_key"],
            api_url=hs_config.get("api_url", "https://api.hootservices.com")
        )

    # Vital Proxies
    vp_config = config.get("vital_proxies", {})
    if vp_config.get("api_key"):
        clients["vital_proxies"] = VitalProxiesClient(
            api_key=vp_config["api_key"],
            api_url=vp_config.get("api_url", "https://api.vital-proxies.com"),
            provider=vp_config.get("provider", "royal"),
            ttl=vp_config.get("ttl", 3600),
            proxy_format=vp_config.get("format", "user:pass@ip:port")
        )

    # SMSPool
    sms_config = config.get("sms", {})
    if sms_config.get("api_key"):
        clients["sms"] = SMSPoolClient(
            api_key=sms_config["api_key"],
            api_url=sms_config.get("api_url", "https://api.smspool.net"),
            poll_interval=sms_config.get("poll_interval", 5),
            max_wait=sms_config.get("max_wait_seconds", 120)
        )

    return clients


# Test functions
if __name__ == "__main__":
    print("\n=== API Clients Test ===\n")

    config = load_config()
    clients = create_clients(config)

    # Test HootServices
    if "hootservices" in clients:
        print("[Testing HootServices]")
        hs = clients["hootservices"]
        stats = hs.get_stats()
        print(f"  Stats: {stats}")
        accounts = hs.get_accounts()
        print(f"  Accounts: {len(accounts)}")
        if accounts:
            print(f"  Sample: {accounts[0]['email']} ({accounts[0]['region']})")
        print()

    # Test Vital Proxies
    if "vital_proxies" in clients:
        print("[Testing Vital Proxies]")
        vp = clients["vital_proxies"]
        usage = vp.get_usage()
        print(f"  Usage: {usage}")
        print()

    # Test SMSPool
    if "sms" in clients:
        print("[Testing SMSPool]")
        sms = clients["sms"]
        balance = sms.get_balance()
        print(f"  Balance: ${balance}")
        print()

    print("=== Done ===\n")
