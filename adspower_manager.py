"""
AdsPower Profile Manager
Handles creation, launching, and management of AdsPower browser profiles
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple


class AdsPowerManager:
    """Manages AdsPower browser profiles for automation"""

    def __init__(self, config_file: str = "config/adspower_config.json"):
        """Initialize AdsPower manager with configuration"""
        self.config = self._load_config(config_file)
        self.api_url = self.config.get("api_url", "http://localhost:50325")
        self.profile_prefix = self.config.get("profile_name_prefix", "TikTok_BC_")

    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                config_path = Path(__file__).parent / config_file

            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config from {config_file}: {e}")
            return {
                "api_url": "http://localhost:50325",
                "create_profiles": True,
                "cleanup_on_error": False,
                "profile_name_prefix": "TikTok_BC_"
            }

    def parse_proxy(self, proxy_string: str) -> Dict:
        """
        Parse proxy string into AdsPower-compatible format

        Supports formats:
        - host:port:user:pass
        - protocol://user:pass@host:port
        - host:port

        Args:
            proxy_string: Proxy string to parse

        Returns:
            Dict with proxy configuration
        """
        if not proxy_string or proxy_string.strip() == "":
            return None

        proxy_config = {
            "proxy_soft": "no_proxy",
            "proxy_type": self.config.get("default_proxy_type", "http")
        }

        try:
            # Handle protocol://user:pass@host:port format
            if "://" in proxy_string:
                parts = proxy_string.split("://")
                proxy_config["proxy_type"] = parts[0]  # http, socks5, etc.
                rest = parts[1]

                if "@" in rest:
                    auth, server = rest.split("@")
                    user, password = auth.split(":")
                    host, port = server.split(":")

                    proxy_config.update({
                        "proxy_soft": "other",
                        "proxy_host": host,
                        "proxy_port": port,
                        "proxy_user": user,
                        "proxy_password": password
                    })
                else:
                    host, port = rest.split(":")
                    proxy_config.update({
                        "proxy_soft": "other",
                        "proxy_host": host,
                        "proxy_port": port
                    })
            else:
                # Handle host:port:user:pass or host:port format
                parts = proxy_string.split(":")

                if len(parts) >= 2:
                    proxy_config.update({
                        "proxy_soft": "other",
                        "proxy_host": parts[0],
                        "proxy_port": parts[1]
                    })

                    if len(parts) >= 4:
                        proxy_config.update({
                            "proxy_user": parts[2],
                            "proxy_password": parts[3]
                        })

            return proxy_config

        except Exception as e:
            print(f"Error parsing proxy string '{proxy_string}': {e}")
            return None

    def create_profile(
        self,
        profile_name: str,
        proxy_string: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new AdsPower browser profile

        Args:
            profile_name: Name for the profile
            proxy_string: Proxy configuration string
            user_agent: Custom user agent (optional)

        Returns:
            Profile ID (user_id) if successful, None otherwise
        """
        try:
            # Build profile configuration
            profile_data = {
                "name": f"{self.profile_prefix}{profile_name}",
                "group_id": "0",
                "domain_name": "",
                "open_urls": [],
                "repeat_config": []
            }

            # Add proxy configuration
            if proxy_string:
                proxy_config = self.parse_proxy(proxy_string)
                if proxy_config:
                    profile_data.update(proxy_config)

            # Add fingerprint settings
            fingerprint = self.config.get("fingerprint_settings", {})
            if fingerprint.get("random_ua", True) and not user_agent:
                profile_data["random_ua"] = "1"
            elif user_agent:
                profile_data["user_agent"] = user_agent

            if fingerprint.get("random_canvas", True):
                profile_data["canvas"] = "1"

            if fingerprint.get("random_webgl", True):
                profile_data["webgl"] = "1"

            if "webrtc" in fingerprint:
                profile_data["webrtc"] = fingerprint["webrtc"]

            if "timezone" in fingerprint:
                profile_data["timezone"] = fingerprint["timezone"]

            if "language" in fingerprint:
                profile_data["language"] = fingerprint["language"]

            if "platform" in fingerprint:
                profile_data["platform"] = fingerprint["platform"]

            # Create profile via API
            response = requests.post(
                f"{self.api_url}/api/v1/user/create",
                json=profile_data,
                timeout=30
            )

            result = response.json()

            if result.get("code") == 0:
                profile_id = result.get("data", {}).get("id")
                print(f"  ✓ Created AdsPower profile: {profile_name} (ID: {profile_id})")
                return profile_id
            else:
                error_msg = result.get("msg", "Unknown error")
                print(f"  ✗ Failed to create profile: {error_msg}")
                return None

        except Exception as e:
            print(f"  ✗ Exception creating AdsPower profile: {e}")
            return None

    def launch_profile(self, profile_id: str) -> Optional[Dict]:
        """
        Launch an AdsPower browser profile

        Args:
            profile_id: The profile ID to launch

        Returns:
            Dict with 'debug_port' and 'webdriver_path' if successful, None otherwise
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/browser/start",
                params={"user_id": profile_id, "launch_args": []},
                timeout=60
            )

            result = response.json()

            if result.get("code") == 0:
                data = result.get("data", {})

                # AdsPower returns debug info in different formats
                debug_address = data.get("ws", {}).get("selenium", "")
                webdriver_path = data.get("webdriver", "")

                # Extract debug port from address like "127.0.0.1:9222"
                debug_port = None
                if debug_address:
                    if ":" in debug_address:
                        debug_port = debug_address.split(":")[-1]

                print(f"  ✓ Launched profile {profile_id} (Debug port: {debug_port})")

                return {
                    "debug_port": debug_port,
                    "debug_address": debug_address,
                    "webdriver_path": webdriver_path
                }
            else:
                error_msg = result.get("msg", "Unknown error")
                print(f"  ✗ Failed to launch profile: {error_msg}")
                return None

        except Exception as e:
            print(f"  ✗ Exception launching AdsPower profile: {e}")
            return None

    def close_profile(self, profile_id: str) -> bool:
        """
        Close an AdsPower browser profile

        Args:
            profile_id: The profile ID to close

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/browser/stop",
                params={"user_id": profile_id},
                timeout=30
            )

            result = response.json()

            if result.get("code") == 0:
                print(f"  ✓ Closed profile {profile_id}")
                return True
            else:
                error_msg = result.get("msg", "Unknown error")
                print(f"  ⚠️  Failed to close profile: {error_msg}")
                return False

        except Exception as e:
            print(f"  ⚠️  Exception closing AdsPower profile: {e}")
            return False

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete an AdsPower browser profile

        Args:
            profile_id: The profile ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/user/delete",
                json={"user_ids": [profile_id]},
                timeout=30
            )

            result = response.json()

            if result.get("code") == 0:
                print(f"  ✓ Deleted profile {profile_id}")
                return True
            else:
                error_msg = result.get("msg", "Unknown error")
                print(f"  ⚠️  Failed to delete profile: {error_msg}")
                return False

        except Exception as e:
            print(f"  ⚠️  Exception deleting AdsPower profile: {e}")
            return False

    def get_profile_info(self, profile_id: str) -> Optional[Dict]:
        """
        Get information about a profile

        Args:
            profile_id: The profile ID

        Returns:
            Profile information dict if successful, None otherwise
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/user/list",
                params={"user_id": profile_id},
                timeout=30
            )

            result = response.json()

            if result.get("code") == 0:
                profiles = result.get("data", {}).get("list", [])
                if profiles:
                    return profiles[0]

            return None

        except Exception as e:
            print(f"  ⚠️  Exception getting profile info: {e}")
            return None

    def check_api_connection(self) -> bool:
        """
        Check if AdsPower API is accessible

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/browser/list",
                timeout=5
            )

            result = response.json()
            return result.get("code") == 0

        except Exception as e:
            print(f"  ✗ Cannot connect to AdsPower API at {self.api_url}: {e}")
            print(f"  Make sure AdsPower is running and API is enabled")
            return False


def test_adspower_manager():
    """Test AdsPower manager functionality"""
    print("\n=== Testing AdsPower Manager ===\n")

    manager = AdsPowerManager()

    # Test API connection
    print("[1/5] Testing API connection...")
    if not manager.check_api_connection():
        print("  ✗ FAILED: Cannot connect to AdsPower API")
        return
    print("  ✓ PASSED: API connection successful\n")

    # Test proxy parsing
    print("[2/5] Testing proxy parsing...")
    test_proxies = [
        "proxy.example.com:8080:user:pass",
        "http://user:pass@proxy.com:8080",
        "proxy.com:8080"
    ]
    for proxy in test_proxies:
        result = manager.parse_proxy(proxy)
        print(f"  {proxy} -> {result}")
    print()

    # Test profile creation
    print("[3/5] Testing profile creation...")
    test_profile_name = f"test_{int(time.time())}"
    profile_id = manager.create_profile(
        profile_name=test_profile_name,
        proxy_string="proxy.test.com:8080:testuser:testpass"
    )

    if not profile_id:
        print("  ✗ FAILED: Could not create profile")
        return
    print()

    # Test profile launch
    print("[4/5] Testing profile launch...")
    launch_info = manager.launch_profile(profile_id)

    if not launch_info:
        print("  ✗ FAILED: Could not launch profile")
        manager.delete_profile(profile_id)
        return
    print()

    # Wait a bit
    print("  Waiting 3 seconds...")
    time.sleep(3)

    # Test profile close
    print("[5/5] Testing profile close and cleanup...")
    manager.close_profile(profile_id)
    time.sleep(1)
    manager.delete_profile(profile_id)

    print("\n=== All Tests Completed ===\n")


if __name__ == "__main__":
    test_adspower_manager()
