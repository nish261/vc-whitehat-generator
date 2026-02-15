"""
TikTok Ads Manager Automation Module
Handles Selenium-based automation for TikTok Ads campaign creation (White Hat)
"""

import time
import random
import json
import string
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)


class TikTokAdsAutomation:
    """Handles TikTok Ads Manager automation for White Hat campaign creation"""

    # Multiple selector strategies for each element (TikTok UI changes frequently)
    SELECTORS = {
        "create_campaign": [
            "//button[contains(text(), 'Create')]",
            "//button[contains(@class, 'create')]",
            "[data-e2e='create-campaign']",
            "//span[contains(text(), 'Create')]/parent::button",
            "//div[contains(text(), 'Create campaign')]",
        ],
        "traffic_objective": [
            "//div[contains(text(), 'Traffic')]",
            "//span[contains(text(), 'Traffic')]",
            "[data-e2e='objective-traffic']",
            "//div[@class and contains(., 'Traffic')]//input[@type='radio']/..",
        ],
        "continue_button": [
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'Next')]",
            "//span[contains(text(), 'Continue')]/parent::button",
            "[data-e2e='continue-btn']",
        ],
        "placements_tiktok": [
            "//div[contains(text(), 'TikTok')]//preceding-sibling::input[@type='checkbox']",
            "//label[contains(text(), 'TikTok')]//input[@type='checkbox']",
            "//span[contains(text(), 'TikTok')]/ancestor::label//input",
        ],
        "placements_other": [
            "//div[contains(text(), 'Pangle')]//preceding-sibling::input[@type='checkbox']",
            "//div[contains(text(), 'News Feed')]//preceding-sibling::input[@type='checkbox']",
        ],
        "budget_input": [
            "//input[@placeholder='Budget']",
            "//input[contains(@name, 'budget')]",
            "//label[contains(text(), 'Budget')]//following-sibling::input",
            "[data-e2e='budget-input']",
        ],
        "schedule_date": [
            "//input[contains(@placeholder, 'date')]",
            "[data-e2e='schedule-date']",
            "//div[contains(text(), 'Start date')]//following-sibling::input",
        ],
        "upload_image": [
            "//input[@type='file']",
            "//input[@accept*='image']",
            "[data-e2e='upload-media']",
        ],
        "ad_text_input": [
            "//textarea[contains(@placeholder, 'text')]",
            "//input[contains(@placeholder, 'headline')]",
            "[data-e2e='ad-text-input']",
        ],
        "url_input": [
            "//input[@placeholder='URL']",
            "//input[contains(@placeholder, 'url')]",
            "//input[contains(@name, 'url')]",
            "[data-e2e='destination-url']",
        ],
        "publish_button": [
            "//button[contains(text(), 'Publish')]",
            "//button[contains(text(), 'Submit')]",
            "//button[contains(text(), 'Launch')]",
            "//span[contains(text(), 'Publish')]/parent::button",
            "[data-e2e='publish-btn']",
        ],
        "add_audio": [
            "//button[contains(text(), 'Add audio')]",
            "//div[contains(text(), 'Add audio')]",
            "[data-e2e='add-audio']",
        ],
        "audio_option": [
            "//div[@class and contains(@class, 'audio')]//div[1]",
            "//div[contains(@class, 'music-item')][1]",
        ],
        "confirm_audio": [
            "//button[contains(text(), 'Confirm')]",
            "//button[contains(text(), 'Use')]",
            "//button[contains(text(), 'Apply')]",
        ],
    }

    def __init__(self, config_file: str = "config/whitehat_config.json"):
        """Initialize TikTok Ads automation with configuration"""
        self.config = self._load_config(config_file)
        self.driver = None
        self.wait = None
        self.screenshots_folder = Path(self.config.get("screenshots", {}).get("folder", "./screenshots/"))
        self.screenshots_folder.mkdir(parents=True, exist_ok=True)
        self.images_folder = Path(self.config.get("images_folder", "./whitehat_images/"))
        self.used_images = set()

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
                "ads_manager_url": "https://ads.tiktok.com/i18n/home",
                "element_wait_timeout": 20,
                "delays": {"min_delay": 2, "max_delay": 4}
            }

    def connect_to_adspower_browser(self, debug_port: str) -> bool:
        """
        Connect Selenium to AdsPower browser via debug port

        Args:
            debug_port: Chrome debug port from AdsPower

        Returns:
            True if connected successfully
        """
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

            # Disable automation flags
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(
                self.driver,
                self.config.get("element_wait_timeout", 20)
            )

            print(f"  [OK] Connected to AdsPower browser on port {debug_port}")
            return True

        except Exception as e:
            print(f"  [ERR] Failed to connect to AdsPower browser: {e}")
            return False

    def human_delay(self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None):
        """Add human-like delay"""
        delays = self.config.get("delays", {})
        min_delay = min_seconds or delays.get("min_delay", 2)
        max_delay = max_seconds or delays.get("max_delay", 4)
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def human_type(self, element, text: str):
        """Type text with human-like delays"""
        typing_delay = self.config.get("delays", {}).get("typing_delay", 0.1)
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(typing_delay * 0.5, typing_delay * 1.5))

    def take_screenshot(self, name: str) -> Optional[str]:
        """Take screenshot and save to screenshots folder"""
        if not self.config.get("screenshots", {}).get("enabled", True):
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshots_folder / filename
            self.driver.save_screenshot(str(filepath))
            print(f"  [IMG] Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"  [WARN] Failed to take screenshot: {e}")
            return None

    def find_element_with_fallback(self, selector_key: str, timeout: int = 10) -> Optional:
        """
        Try multiple selectors to find an element

        Args:
            selector_key: Key from SELECTORS dict
            timeout: Timeout per selector attempt

        Returns:
            WebElement if found, None otherwise
        """
        selectors = self.SELECTORS.get(selector_key, [])

        for selector in selectors:
            try:
                # Determine selector type
                if selector.startswith("//"):
                    by = By.XPATH
                elif selector.startswith("["):
                    by = By.CSS_SELECTOR
                else:
                    by = By.XPATH

                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                return element
            except (TimeoutException, NoSuchElementException):
                continue

        return None

    def click_element_with_fallback(self, selector_key: str, timeout: int = 10) -> bool:
        """
        Try to click an element using multiple selectors

        Args:
            selector_key: Key from SELECTORS dict
            timeout: Timeout per selector attempt

        Returns:
            True if clicked successfully
        """
        selectors = self.SELECTORS.get(selector_key, [])

        for selector in selectors:
            try:
                if selector.startswith("//"):
                    by = By.XPATH
                elif selector.startswith("["):
                    by = By.CSS_SELECTOR
                else:
                    by = By.XPATH

                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )

                # Try regular click first
                try:
                    element.click()
                    return True
                except ElementClickInterceptedException:
                    # Try JavaScript click as fallback
                    self.driver.execute_script("arguments[0].click();", element)
                    return True

            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                continue

        return False

    def generate_404_url(self) -> str:
        """Generate a 404 URL based on config"""
        landing_config = self.config.get("landing_page", {})

        base_domain = landing_config.get("base_domain", "example.com")
        path_prefix = landing_config.get("path_prefix", "/products/")
        slug_length = landing_config.get("random_slug_length", 12)
        use_https = landing_config.get("use_https", True)

        # Generate random slug
        random_slug = ''.join(random.choices(string.ascii_lowercase + string.digits, k=slug_length))

        protocol = "https" if use_https else "http"
        return f"{protocol}://{base_domain}{path_prefix}{random_slug}"

    def get_random_image(self) -> Optional[str]:
        """
        Get a random image from the images folder
        Uses no-repeat-until-exhausted logic

        Returns:
            Path to image file or None if no images available
        """
        if not self.images_folder.exists():
            print(f"  [WARN] Images folder does not exist: {self.images_folder}")
            return None

        # Get all image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        all_images = [
            str(f) for f in self.images_folder.iterdir()
            if f.suffix.lower() in image_extensions
        ]

        if not all_images:
            print(f"  [WARN] No images found in {self.images_folder}")
            return None

        # Get unused images
        unused_images = [img for img in all_images if img not in self.used_images]

        # If all images used, reset
        if not unused_images:
            self.used_images.clear()
            unused_images = all_images

        # Select random image
        selected = random.choice(unused_images)
        self.used_images.add(selected)

        return selected

    def get_random_ad_text(self) -> str:
        """Get random ad text from config templates"""
        ad_config = self.config.get("ad_text", {})
        templates = ad_config.get("templates", ["Shop Now", "Limited Offer"])
        return random.choice(templates)

    # =========================================================================
    # STEP-BY-STEP CAMPAIGN CREATION METHODS
    # =========================================================================

    def navigate_to_ads_manager(self) -> bool:
        """
        Step 1: Navigate to TikTok Ads Manager

        Returns:
            True if navigation successful
        """
        try:
            print("  [1/12] Navigating to TikTok Ads Manager...")

            ads_url = self.config.get("ads_manager_url", "https://ads.tiktok.com/i18n/home")
            self.driver.get(ads_url)

            page_load_wait = self.config.get("delays", {}).get("page_load_wait", 5)
            time.sleep(page_load_wait)

            # Check if we're logged in by looking for create button or account indicators
            current_url = self.driver.current_url

            if "login" in current_url.lower() or "signin" in current_url.lower():
                print("  [ERR] Not logged in to TikTok Ads Manager")
                self.take_screenshot("error_not_logged_in")
                return False

            print(f"  [OK] Navigated to Ads Manager: {current_url}")
            self.human_delay()
            return True

        except Exception as e:
            print(f"  [ERR] Failed to navigate to Ads Manager: {e}")
            self.take_screenshot("error_navigation")
            return False

    def create_new_campaign(self) -> bool:
        """
        Step 2: Start new campaign and select Traffic objective

        Returns:
            True if campaign creation started
        """
        try:
            print("  [2/12] Starting new campaign creation...")

            # Click Create button
            if not self.click_element_with_fallback("create_campaign", timeout=15):
                print("  [ERR] Could not find Create Campaign button")
                self.take_screenshot("error_no_create_button")
                return False

            print("  [OK] Clicked Create Campaign")
            self.human_delay(2, 4)

            # Select Traffic objective
            print("  [2b/12] Selecting Traffic objective...")

            if not self.click_element_with_fallback("traffic_objective", timeout=10):
                print("  [WARN] Could not find Traffic objective, trying alternatives...")
                # Try clicking on any objective card
                try:
                    objectives = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'objective')]")
                    if objectives:
                        objectives[1].click()  # Traffic is usually second
                except:
                    pass

            print("  [OK] Selected campaign objective")
            self.human_delay()

            # Click Continue
            if not self.click_element_with_fallback("continue_button", timeout=10):
                print("  [WARN] No continue button found, may auto-advance")

            self.human_delay(2, 3)
            return True

        except Exception as e:
            print(f"  [ERR] Failed to create campaign: {e}")
            self.take_screenshot("error_create_campaign")
            return False

    def configure_campaign_settings(self) -> bool:
        """
        Step 3: Configure campaign-level settings (minimal changes)

        Returns:
            True if settings configured
        """
        try:
            print("  [3/12] Configuring campaign settings...")

            # This is mostly pass-through - we leave defaults
            # Just wait for the page and click continue if available

            self.human_delay(2, 3)

            # Click Continue to move to ad group level
            if not self.click_element_with_fallback("continue_button", timeout=10):
                print("  [INFO] No continue button, checking if auto-advanced")

            print("  [OK] Campaign settings configured")
            self.human_delay()
            return True

        except Exception as e:
            print(f"  [ERR] Failed to configure campaign settings: {e}")
            return False

    def configure_placements(self) -> bool:
        """
        Step 4: Turn off improper placements (keep only TikTok)

        Returns:
            True if placements configured
        """
        try:
            print("  [4/12] Configuring placements...")

            # Look for placement options and uncheck non-TikTok ones
            placement_config = self.config.get("placements", {})

            if placement_config.get("tiktok_only", True):
                # Try to find and uncheck Pangle, News Feed, etc.
                try:
                    # Find all placement checkboxes
                    checkboxes = self.driver.find_elements(
                        By.XPATH,
                        "//input[@type='checkbox'][ancestor::div[contains(@class, 'placement')]]"
                    )

                    for checkbox in checkboxes:
                        try:
                            label_text = checkbox.find_element(By.XPATH, "./ancestor::label").text.lower()

                            # Keep TikTok checked, uncheck others
                            if "tiktok" not in label_text and checkbox.is_selected():
                                checkbox.click()
                                print(f"    [OK] Unchecked placement: {label_text}")
                                self.human_delay(0.5, 1)
                        except:
                            continue

                except Exception as e:
                    print(f"  [WARN] Could not modify placements: {e}")

            print("  [OK] Placements configured")
            self.human_delay()
            return True

        except Exception as e:
            print(f"  [ERR] Failed to configure placements: {e}")
            return False

    def set_targeting(self) -> bool:
        """
        Step 5: Set targeting (mostly defaults)

        Returns:
            True if targeting set
        """
        try:
            print("  [5/12] Setting targeting...")

            targeting_config = self.config.get("targeting", {})

            if targeting_config.get("leave_defaults", True):
                print("  [INFO] Leaving targeting at defaults")
                self.human_delay()
                return True

            # If we need to set specific country
            if targeting_config.get("use_home_country", True):
                country = targeting_config.get("default_country", "US")

                try:
                    # Look for location/country input
                    country_input = self.driver.find_element(
                        By.XPATH,
                        "//input[contains(@placeholder, 'location') or contains(@placeholder, 'country')]"
                    )
                    country_input.clear()
                    self.human_type(country_input, country)
                    self.human_delay(1, 2)

                    # Click on first suggestion
                    suggestion = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{country}')]"))
                    )
                    suggestion.click()
                    print(f"  [OK] Set location to {country}")
                except:
                    print(f"  [INFO] Could not set specific location, using defaults")

            self.human_delay()
            return True

        except Exception as e:
            print(f"  [ERR] Failed to set targeting: {e}")
            return False

    def set_budget_schedule(self) -> bool:
        """
        Step 6: Set budget ($20) and schedule (+1 day)

        Returns:
            True if budget and schedule set
        """
        try:
            print("  [6/12] Setting budget and schedule...")

            campaign_config = self.config.get("campaign", {})
            budget = campaign_config.get("budget_usd", 20)
            delay_days = campaign_config.get("start_delay_days", 1)

            # Set budget
            budget_element = self.find_element_with_fallback("budget_input", timeout=10)

            if budget_element:
                budget_element.clear()
                self.human_type(budget_element, str(budget))
                print(f"  [OK] Set budget to ${budget}")
            else:
                print("  [WARN] Could not find budget input")

            self.human_delay()

            # Set schedule to start +1 day
            try:
                # Look for schedule/date picker
                date_inputs = self.driver.find_elements(
                    By.XPATH,
                    "//input[contains(@type, 'date') or contains(@class, 'date')]"
                )

                if date_inputs:
                    future_date = (datetime.now() + timedelta(days=delay_days)).strftime("%Y-%m-%d")

                    # Click to open date picker
                    date_inputs[0].click()
                    self.human_delay(1, 2)

                    # Try to set the date
                    date_inputs[0].clear()
                    date_inputs[0].send_keys(future_date)
                    date_inputs[0].send_keys(Keys.ENTER)

                    print(f"  [OK] Set start date to {future_date}")
                else:
                    print("  [INFO] No date input found, using default schedule")

            except Exception as e:
                print(f"  [INFO] Could not set custom schedule: {e}")

            # Click Continue to ad level
            self.human_delay()
            self.click_element_with_fallback("continue_button", timeout=10)

            print("  [OK] Budget and schedule configured")
            self.human_delay()
            return True

        except Exception as e:
            print(f"  [ERR] Failed to set budget/schedule: {e}")
            return False

    def create_ad_creative(self) -> bool:
        """
        Steps 7-10: Upload image, add audio, add text

        Returns:
            True if creative created
        """
        try:
            print("  [7/12] Creating ad creative...")

            # Step 7: Navigate to ad creation section
            self.human_delay(2, 3)

            # Step 8: Upload image
            print("  [8/12] Uploading image...")

            image_path = self.get_random_image()

            if image_path:
                try:
                    # Find file input
                    upload_input = self.find_element_with_fallback("upload_image", timeout=15)

                    if upload_input:
                        upload_input.send_keys(image_path)
                        print(f"  [OK] Uploaded image: {Path(image_path).name}")

                        # Wait for upload to complete
                        time.sleep(5)
                    else:
                        # Try clicking upload button first
                        upload_buttons = self.driver.find_elements(
                            By.XPATH,
                            "//button[contains(text(), 'Upload')] | //div[contains(text(), 'Upload')]"
                        )
                        if upload_buttons:
                            upload_buttons[0].click()
                            self.human_delay()

                            # Now find file input
                            upload_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                            upload_input.send_keys(image_path)
                            time.sleep(5)

                except Exception as e:
                    print(f"  [WARN] Could not upload image: {e}")
            else:
                print("  [WARN] No image available to upload")

            self.human_delay()

            # Step 9: Add audio
            print("  [9/12] Adding audio...")

            audio_config = self.config.get("audio", {})

            if audio_config.get("select_random", True):
                try:
                    # Click Add Audio button
                    if self.click_element_with_fallback("add_audio", timeout=10):
                        self.human_delay(1, 2)

                        # Click first audio option
                        if self.click_element_with_fallback("audio_option", timeout=10):
                            self.human_delay(0.5, 1)

                            # Confirm/Use audio
                            self.click_element_with_fallback("confirm_audio", timeout=5)
                            print("  [OK] Added audio")
                        else:
                            print("  [INFO] No audio options found, skipping")
                    else:
                        if audio_config.get("skip_if_unavailable", True):
                            print("  [INFO] Audio button not found, skipping")

                except Exception as e:
                    print(f"  [INFO] Could not add audio: {e}")

            self.human_delay()

            # Step 10: Add text overlay
            print("  [10/12] Adding ad text...")

            ad_text = self.get_random_ad_text()

            try:
                text_input = self.find_element_with_fallback("ad_text_input", timeout=10)

                if text_input:
                    text_input.clear()
                    self.human_type(text_input, ad_text)
                    print(f"  [OK] Added ad text: {ad_text}")
                else:
                    # Try to find any textarea for ad copy
                    textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                    if textareas:
                        textareas[0].clear()
                        self.human_type(textareas[0], ad_text)
                        print(f"  [OK] Added ad text (textarea): {ad_text}")

            except Exception as e:
                print(f"  [INFO] Could not add text: {e}")

            self.human_delay()
            print("  [OK] Ad creative created")
            return True

        except Exception as e:
            print(f"  [ERR] Failed to create ad creative: {e}")
            self.take_screenshot("error_creative")
            return False

    def set_landing_url(self) -> bool:
        """
        Step 11: Configure the landing page URL (404 URL)

        Returns:
            True if URL set
        """
        try:
            print("  [11/12] Setting landing URL...")

            # Generate 404 URL
            landing_url = self.generate_404_url()

            # Find URL input
            url_input = self.find_element_with_fallback("url_input", timeout=10)

            if url_input:
                url_input.clear()
                self.human_type(url_input, landing_url)
                print(f"  [OK] Set landing URL: {landing_url}")
            else:
                # Try alternative approaches
                try:
                    # Look for destination/link section
                    url_inputs = self.driver.find_elements(
                        By.XPATH,
                        "//input[contains(@placeholder, 'http') or contains(@placeholder, 'URL') or contains(@placeholder, 'url')]"
                    )

                    if url_inputs:
                        url_inputs[0].clear()
                        self.human_type(url_inputs[0], landing_url)
                        print(f"  [OK] Set landing URL (alt): {landing_url}")
                    else:
                        print("  [WARN] Could not find URL input field")
                        return False

                except Exception as e:
                    print(f"  [ERR] Failed to set URL: {e}")
                    return False

            self.human_delay()
            return True

        except Exception as e:
            print(f"  [ERR] Failed to set landing URL: {e}")
            return False

    def publish_campaign(self) -> Tuple[bool, Optional[str]]:
        """
        Step 12: Publish the campaign

        Returns:
            Tuple of (success, campaign_id)
        """
        try:
            print("  [12/12] Publishing campaign...")

            # Click Publish/Submit button
            if not self.click_element_with_fallback("publish_button", timeout=15):
                print("  [ERR] Could not find Publish button")
                self.take_screenshot("error_no_publish")
                return False, None

            print("  [OK] Clicked Publish")

            # Wait for confirmation
            self.human_delay(3, 5)

            # Try to extract campaign ID from URL or page
            campaign_id = None

            try:
                current_url = self.driver.current_url

                # Look for campaign ID in URL
                import re
                id_match = re.search(r'campaign[_-]?id[=:/](\d+)', current_url, re.IGNORECASE)

                if id_match:
                    campaign_id = id_match.group(1)
                else:
                    # Try to find on page
                    id_elements = self.driver.find_elements(
                        By.XPATH,
                        "//*[contains(text(), 'Campaign ID')]//following-sibling::*"
                    )
                    if id_elements:
                        campaign_id = id_elements[0].text.strip()

            except:
                pass

            # Take success screenshot
            screenshot_path = self.take_screenshot("success_published")

            if campaign_id:
                print(f"  [OK] Campaign published! ID: {campaign_id}")
            else:
                print("  [OK] Campaign published! (ID not extracted)")

            return True, campaign_id

        except Exception as e:
            print(f"  [ERR] Failed to publish campaign: {e}")
            self.take_screenshot("error_publish")
            return False, None

    # =========================================================================
    # MAIN WORKFLOW
    # =========================================================================

    def create_whitehat_campaign(self) -> Dict:
        """
        Complete White Hat campaign creation workflow

        Returns:
            Dict with results
        """
        result = {
            "success": False,
            "campaign_id": None,
            "landing_url": None,
            "screenshot_path": None,
            "error_message": None,
            "steps_completed": []
        }

        steps = [
            ("navigate", self.navigate_to_ads_manager),
            ("create_campaign", self.create_new_campaign),
            ("campaign_settings", self.configure_campaign_settings),
            ("placements", self.configure_placements),
            ("targeting", self.set_targeting),
            ("budget_schedule", self.set_budget_schedule),
            ("creative", self.create_ad_creative),
            ("landing_url", self.set_landing_url),
        ]

        try:
            for step_name, step_func in steps:
                if not step_func():
                    result["error_message"] = f"Failed at step: {step_name}"
                    result["screenshot_path"] = self.take_screenshot(f"error_{step_name}")
                    return result

                result["steps_completed"].append(step_name)

            # Final step: Publish
            success, campaign_id = self.publish_campaign()

            if success:
                result["success"] = True
                result["campaign_id"] = campaign_id
                result["landing_url"] = self.generate_404_url()  # For reference
                result["screenshot_path"] = self.take_screenshot("success_final")
                result["steps_completed"].append("publish")
            else:
                result["error_message"] = "Failed to publish campaign"

        except Exception as e:
            result["error_message"] = f"Exception: {str(e)[:200]}"
            result["screenshot_path"] = self.take_screenshot("error_exception")

        return result

    def cleanup(self):
        """Cleanup Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


if __name__ == "__main__":
    print("\n=== TikTok Ads Automation Module ===\n")
    print("This module requires:")
    print("1. AdsPower running with an active profile")
    print("2. Profile logged into TikTok Ads Manager")
    print("3. Debug port from AdsPower")
    print("\nUse tiktok_whitehat_creator.py for full automation\n")
