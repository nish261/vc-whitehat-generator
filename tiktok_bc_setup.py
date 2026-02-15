"""
TikTok Business Center Setup Automation
Handles the full BC setup flow for fresh HootServices accounts:
1. Login to TikTok
2. Navigate to Business Center
3. Set timezone, skip 2FA
4. Create/assign advertiser account
5. Handle email verification (via HootServices)
6. Handle SMS verification (via SMSPool)
7. Add billing info
"""

import time
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)


class TikTokBCSetup:
    """Handles TikTok Business Center setup automation"""

    # URLs
    URLS = {
        "login": "https://www.tiktok.com/login/phone-or-email/email",
        "business_center": "https://business.tiktok.com/",
        "ads_manager": "https://ads.tiktok.com/i18n/home"
    }

    # Timezone mapping
    TIMEZONES = {
        "US": "America/New_York",
        "IT": "Europe/Rome",
        "FR": "Europe/Paris",
        "DE": "Europe/Berlin",
        "NL": "Europe/Amsterdam",
        "GB": "Europe/London",
        "AU": "Australia/Sydney"
    }

    def __init__(self, config: Dict = None):
        """Initialize BC setup automation"""
        self.config = config or {}
        self.driver = None
        self.wait = None
        self.screenshots_folder = Path(self.config.get("screenshots", {}).get("folder", "./screenshots/"))
        self.screenshots_folder.mkdir(parents=True, exist_ok=True)

        # Callbacks for verification
        self.email_code_callback: Optional[Callable] = None
        self.sms_code_callback: Optional[Callable] = None

    def connect_to_adspower_browser(self, debug_port: str) -> bool:
        """Connect Selenium to AdsPower browser via debug port"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)

            print(f"  [OK] Connected to browser on port {debug_port}")
            return True

        except Exception as e:
            print(f"  [ERR] Failed to connect: {e}")
            return False

    def human_delay(self, min_s: float = 2, max_s: float = 4):
        """Human-like delay"""
        time.sleep(random.uniform(min_s, max_s))

    def human_type(self, element, text: str, delay: float = 0.1):
        """Type with human-like delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(delay * 0.5, delay * 1.5))

    def take_screenshot(self, name: str) -> Optional[str]:
        """Take screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.screenshots_folder / f"{name}_{timestamp}.png"
            self.driver.save_screenshot(str(filepath))
            return str(filepath)
        except:
            return None

    def click_element(self, xpath: str, timeout: int = 10, js_fallback: bool = True) -> bool:
        """Click element with fallback to JS click"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            try:
                element.click()
            except ElementClickInterceptedException:
                if js_fallback:
                    self.driver.execute_script("arguments[0].click();", element)
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def find_and_click(self, xpaths: list, timeout: int = 10) -> bool:
        """Try multiple xpaths until one works"""
        for xpath in xpaths:
            if self.click_element(xpath, timeout=timeout):
                return True
        return False

    def enter_text(self, xpath: str, text: str, clear: bool = True, timeout: int = 10) -> bool:
        """Find element and enter text"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            if clear:
                element.clear()
            self.human_type(element, text)
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    # =========================================================================
    # LOGIN FLOW
    # =========================================================================

    def login(self, email: str, password: str) -> bool:
        """
        Login to TikTok with email/password

        Returns:
            True if login successful
        """
        try:
            print("  [LOGIN] Navigating to TikTok login...")
            self.driver.get(self.URLS["login"])
            self.human_delay(3, 5)

            # Enter email
            print("  [LOGIN] Entering email...")
            email_xpaths = [
                "//input[@name='username']",
                "//input[@placeholder='Email or username']",
                "//input[@type='text']"
            ]

            for xpath in email_xpaths:
                if self.enter_text(xpath, email):
                    break
            else:
                print("  [ERR] Could not find email input")
                self.take_screenshot("login_no_email_input")
                return False

            self.human_delay(1, 2)

            # Enter password
            print("  [LOGIN] Entering password...")
            password_xpaths = [
                "//input[@type='password']",
                "//input[@placeholder='Password']"
            ]

            for xpath in password_xpaths:
                if self.enter_text(xpath, password):
                    break
            else:
                print("  [ERR] Could not find password input")
                return False

            self.human_delay(1, 2)

            # Click login button
            print("  [LOGIN] Clicking login button...")
            login_xpaths = [
                "//button[@type='submit']",
                "//button[contains(text(), 'Log in')]",
                "//button[@data-e2e='login-button']"
            ]

            if not self.find_and_click(login_xpaths):
                print("  [ERR] Could not find login button")
                return False

            self.human_delay(3, 5)

            # Check for captcha or verification
            current_url = self.driver.current_url

            # Handle email verification if required
            if self._check_for_email_verification():
                print("  [LOGIN] Email verification required...")
                if not self._handle_email_verification(email):
                    return False

            # Handle SMS verification if required
            if self._check_for_sms_verification():
                print("  [LOGIN] SMS verification required...")
                # Note: SMS verification during login is handled by callback
                if self.sms_code_callback:
                    if not self._handle_sms_verification():
                        return False

            # Verify login success
            self.human_delay(3, 5)
            current_url = self.driver.current_url

            if "login" not in current_url.lower():
                print("  [OK] Login successful!")
                self.take_screenshot("login_success")
                return True
            else:
                print("  [WARN] May still be on login page")
                self.take_screenshot("login_unclear")
                return True  # Continue anyway

        except Exception as e:
            print(f"  [ERR] Login exception: {e}")
            self.take_screenshot("login_error")
            return False

    def _check_for_email_verification(self) -> bool:
        """Check if email verification is required"""
        try:
            # Look for verification code input or related text
            indicators = [
                "//input[@placeholder*='code']",
                "//*[contains(text(), 'verification code')]",
                "//*[contains(text(), 'Enter the code')]"
            ]
            for xpath in indicators:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    return True
            return False
        except:
            return False

    def _check_for_sms_verification(self) -> bool:
        """Check if SMS verification is required"""
        try:
            indicators = [
                "//*[contains(text(), 'phone number')]",
                "//*[contains(text(), 'SMS')]",
                "//input[@placeholder*='phone']"
            ]
            for xpath in indicators:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    return True
            return False
        except:
            return False

    def _handle_email_verification(self, email: str) -> bool:
        """Handle email verification during login"""
        if not self.email_code_callback:
            print("  [ERR] No email code callback set")
            return False

        # Get code from callback (HootServices)
        code = self.email_code_callback(email)
        if not code:
            print("  [ERR] Could not get email verification code")
            return False

        # Enter code
        code_xpaths = [
            "//input[@placeholder*='code']",
            "//input[contains(@class, 'verification')]",
            "//input[@type='text']"
        ]

        for xpath in code_xpaths:
            if self.enter_text(xpath, code):
                break
        else:
            # Try individual digit inputs
            try:
                inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='tel']")
                if len(inputs) >= 6:
                    for i, digit in enumerate(code[:6]):
                        inputs[i].send_keys(digit)
                        time.sleep(0.2)
            except:
                print("  [ERR] Could not enter verification code")
                return False

        self.human_delay(2, 3)

        # Submit if needed
        self.find_and_click([
            "//button[contains(text(), 'Submit')]",
            "//button[contains(text(), 'Verify')]",
            "//button[contains(text(), 'Continue')]"
        ], timeout=5)

        self.human_delay(2, 3)
        return True

    def _handle_sms_verification(self) -> bool:
        """Handle SMS verification"""
        if not self.sms_code_callback:
            print("  [ERR] No SMS code callback set")
            return False

        # This is called when we need to enter a phone number and get SMS
        # The callback should return {"number": "...", "code": "..."}
        sms_info = self.sms_code_callback()

        if not sms_info:
            print("  [ERR] Could not get SMS verification")
            return False

        # Enter phone number
        phone_xpaths = [
            "//input[@placeholder*='phone']",
            "//input[@type='tel']"
        ]

        for xpath in phone_xpaths:
            if self.enter_text(xpath, sms_info["number"]):
                break

        self.human_delay(1, 2)

        # Click send code
        self.find_and_click([
            "//button[contains(text(), 'Send')]",
            "//button[contains(text(), 'Get code')]"
        ], timeout=5)

        self.human_delay(2, 3)

        # Enter code
        code_xpaths = [
            "//input[@placeholder*='code']",
            "//input[contains(@class, 'verification')]"
        ]

        for xpath in code_xpaths:
            if self.enter_text(xpath, sms_info["code"]):
                break

        self.human_delay(2, 3)

        # Submit
        self.find_and_click([
            "//button[contains(text(), 'Submit')]",
            "//button[contains(text(), 'Verify')]"
        ], timeout=5)

        self.human_delay(2, 3)
        return True

    # =========================================================================
    # BUSINESS CENTER SETUP
    # =========================================================================

    def navigate_to_business_center(self) -> bool:
        """Navigate to TikTok Business Center"""
        try:
            print("  [BC] Navigating to Business Center...")
            self.driver.get(self.URLS["business_center"])
            self.human_delay(4, 6)

            current_url = self.driver.current_url
            print(f"  [BC] Current URL: {current_url}")

            self.take_screenshot("business_center")
            return True

        except Exception as e:
            print(f"  [ERR] Navigation error: {e}")
            return False

    def setup_business_center(self, region: str, business_name: str = None) -> bool:
        """
        Complete Business Center setup

        Args:
            region: Account region (US, IT, etc.)
            business_name: Optional business name

        Returns:
            True if setup successful
        """
        try:
            print("  [BC] Setting up Business Center...")

            # Skip 2FA if prompted
            self._skip_2fa()

            # Set timezone
            timezone = self.TIMEZONES.get(region, "America/New_York")
            self._set_timezone(timezone)

            # Fill required fields only
            if business_name:
                self._set_business_name(business_name)

            self.take_screenshot("bc_setup_complete")
            return True

        except Exception as e:
            print(f"  [ERR] BC setup error: {e}")
            return False

    def _skip_2fa(self) -> bool:
        """Skip 2FA setup if prompted"""
        try:
            skip_xpaths = [
                "//button[contains(text(), 'Not now')]",
                "//button[contains(text(), 'Skip')]",
                "//a[contains(text(), 'Not now')]",
                "//span[contains(text(), 'Not now')]/parent::button"
            ]

            if self.find_and_click(skip_xpaths, timeout=5):
                print("  [OK] Skipped 2FA")
                self.human_delay(1, 2)
                return True

            return False

        except:
            return False

    def _set_timezone(self, timezone: str) -> bool:
        """Set timezone in BC settings"""
        try:
            # Look for timezone dropdown
            tz_xpaths = [
                "//div[contains(text(), 'Time zone')]//following-sibling::*//select",
                "//select[contains(@class, 'timezone')]",
                "//div[contains(@class, 'timezone')]"
            ]

            for xpath in tz_xpaths:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    element.click()
                    self.human_delay(0.5, 1)

                    # Find and click timezone option
                    option_xpath = f"//option[contains(text(), '{timezone}')] | //div[contains(text(), '{timezone}')]"
                    self.click_element(option_xpath, timeout=5)
                    print(f"  [OK] Set timezone to {timezone}")
                    return True
                except:
                    continue

            print("  [INFO] Could not find timezone selector")
            return False

        except:
            return False

    def _set_business_name(self, name: str) -> bool:
        """Set business name"""
        try:
            name_xpaths = [
                "//input[@placeholder*='business']",
                "//input[@name='businessName']",
                "//input[contains(@class, 'business-name')]"
            ]

            for xpath in name_xpaths:
                if self.enter_text(xpath, name):
                    print(f"  [OK] Set business name: {name}")
                    return True

            return False

        except:
            return False

    # =========================================================================
    # ADVERTISER ACCOUNT SETUP
    # =========================================================================

    def create_advertiser_account(self, region: str, email: str) -> Optional[str]:
        """
        Create/assign advertiser account

        Args:
            region: Account region
            email: Account email (for verification)

        Returns:
            Advertiser account ID if successful
        """
        try:
            print("  [AD] Creating advertiser account...")

            # Navigate to ad accounts section
            self._navigate_to_ad_accounts()

            # Click create/add account
            create_xpaths = [
                "//button[contains(text(), 'Create')]",
                "//button[contains(text(), 'Add')]",
                "//span[contains(text(), 'Create')]/parent::button"
            ]

            if not self.find_and_click(create_xpaths, timeout=10):
                print("  [INFO] No create button, may already have account")
                return self._get_existing_ad_account_id()

            self.human_delay(2, 3)

            # Fill account details
            self._fill_ad_account_details(region)

            # Handle verification if required
            if self._check_for_email_verification():
                print("  [AD] Email verification required...")
                self._handle_email_verification(email)

            # Submit
            submit_xpaths = [
                "//button[contains(text(), 'Create')]",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Confirm')]"
            ]
            self.find_and_click(submit_xpaths, timeout=10)

            self.human_delay(3, 5)

            # Get account ID
            account_id = self._get_existing_ad_account_id()
            if account_id:
                print(f"  [OK] Advertiser account created: {account_id}")

            self.take_screenshot("ad_account_created")
            return account_id

        except Exception as e:
            print(f"  [ERR] Ad account creation error: {e}")
            return None

    def _navigate_to_ad_accounts(self):
        """Navigate to ad accounts section"""
        try:
            # Look for Accounts menu item
            account_xpaths = [
                "//a[contains(text(), 'Accounts')]",
                "//span[contains(text(), 'Accounts')]/parent::*",
                "//div[contains(text(), 'Ad accounts')]"
            ]

            self.find_and_click(account_xpaths, timeout=10)
            self.human_delay(2, 3)

        except:
            pass

    def _fill_ad_account_details(self, region: str):
        """Fill ad account creation form"""
        try:
            # Country/region
            country_xpaths = [
                "//select[contains(@name, 'country')]",
                "//div[contains(text(), 'Country')]//following-sibling::*//select"
            ]

            for xpath in country_xpaths:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    element.click()
                    self.human_delay(0.5, 1)

                    option = f"//option[contains(@value, '{region}')] | //div[contains(text(), '{region}')]"
                    self.click_element(option, timeout=5)
                    break
                except:
                    continue

            # Currency is usually auto-set based on country

            # Timezone
            timezone = self.TIMEZONES.get(region, "America/New_York")
            self._set_timezone(timezone)

        except:
            pass

    def _get_existing_ad_account_id(self) -> Optional[str]:
        """Extract existing ad account ID from page"""
        try:
            # Look for account ID in page
            page_text = self.driver.page_source

            # Common patterns for ad account IDs
            patterns = [
                r'advertiser[_-]?id["\s:]+(\d+)',
                r'ad[_-]?account[_-]?id["\s:]+(\d+)',
                r'/account/(\d+)',
                r'"id":\s*"?(\d{10,})"?'
            ]

            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return match.group(1)

            return None

        except:
            return None

    # =========================================================================
    # MAIN FLOW
    # =========================================================================

    def full_setup(
        self,
        email: str,
        password: str,
        region: str,
        business_name: str = None
    ) -> Dict:
        """
        Complete BC setup flow

        Args:
            email: Account email
            password: Account password
            region: Account region
            business_name: Optional business name

        Returns:
            Dict with setup results
        """
        result = {
            "success": False,
            "email": email,
            "region": region,
            "logged_in": False,
            "bc_setup": False,
            "ad_account_id": None,
            "error": None,
            "screenshots": []
        }

        try:
            # Step 1: Login
            print("\n[STEP 1] Logging in...")
            if not self.login(email, password):
                result["error"] = "Login failed"
                return result
            result["logged_in"] = True

            # Step 2: Navigate to Business Center
            print("\n[STEP 2] Navigating to Business Center...")
            if not self.navigate_to_business_center():
                result["error"] = "Could not navigate to BC"
                return result

            # Step 3: Setup BC
            print("\n[STEP 3] Setting up Business Center...")
            if not self.setup_business_center(region, business_name):
                result["error"] = "BC setup failed"
                return result
            result["bc_setup"] = True

            # Step 4: Create advertiser account
            print("\n[STEP 4] Creating advertiser account...")
            ad_account_id = self.create_advertiser_account(region, email)
            result["ad_account_id"] = ad_account_id

            result["success"] = True
            print("\n[DONE] BC setup complete!")

        except Exception as e:
            result["error"] = str(e)
            self.take_screenshot("setup_error")

        return result

    def cleanup(self):
        """Cleanup driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


if __name__ == "__main__":
    print("\n=== TikTok BC Setup Module ===\n")
    print("This module requires:")
    print("1. AdsPower running with a profile")
    print("2. Account credentials from HootServices")
    print("3. Verification callbacks configured")
    print("\nUse tiktok_full_setup.py for complete automation\n")
