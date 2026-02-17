"""Browser action utilities for Hermes"""

import time
import random
from typing import Optional


def human_delay(min_sec: float = 0.5, max_sec: float = 1.5):
    """Random human-like delay"""
    time.sleep(random.uniform(min_sec, max_sec))


def click(page, selector: str, timeout: int = 10000) -> bool:
    """Click element with human-like behavior"""
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        if element:
            human_delay(0.2, 0.5)
            element.click()
            print(f"[ACTION] Clicked: {selector}")
            return True
    except Exception as e:
        print(f"[ACTION] Click failed on {selector}: {e}")
    return False


def type_text(page, selector: str, text: str, delay: float = 0.05, timeout: int = 10000) -> bool:
    """Type text with human-like delays"""
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        if element:
            element.click()
            human_delay(0.1, 0.3)
            
            for char in text:
                page.keyboard.type(char, delay=random.uniform(delay * 0.5, delay * 1.5) * 1000)
            
            print(f"[ACTION] Typed {len(text)} chars into {selector}")
            return True
    except Exception as e:
        print(f"[ACTION] Type failed on {selector}: {e}")
    return False


def fill(page, selector: str, text: str, timeout: int = 10000) -> bool:
    """Fill input (faster than type, less human)"""
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        if element:
            element.fill(text)
            print(f"[ACTION] Filled: {selector}")
            return True
    except Exception as e:
        print(f"[ACTION] Fill failed on {selector}: {e}")
    return False


def wait_for(page, selector: str, timeout: int = 10000) -> bool:
    """Wait for element to appear"""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        print(f"[ACTION] Found: {selector}")
        return True
    except:
        print(f"[ACTION] Timeout waiting for: {selector}")
        return False


def wait_for_navigation(page, timeout: int = 30000) -> bool:
    """Wait for page navigation"""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
        return True
    except:
        return False


def get_text(page, selector: str, timeout: int = 5000) -> Optional[str]:
    """Get text content of element"""
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        if element:
            return element.text_content()
    except:
        pass
    return None


def exists(page, selector: str, timeout: int = 2000) -> bool:
    """Check if element exists"""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except:
        return False


def scroll_down(page, pixels: int = 300):
    """Scroll page down"""
    page.evaluate(f"window.scrollBy(0, {pixels})")
    human_delay(0.3, 0.6)


def select_option(page, selector: str, value: str, timeout: int = 10000) -> bool:
    """Select dropdown option"""
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        if element:
            page.select_option(selector, value)
            print(f"[ACTION] Selected {value} in {selector}")
            return True
    except Exception as e:
        print(f"[ACTION] Select failed on {selector}: {e}")
    return False


def press_key(page, key: str):
    """Press keyboard key"""
    page.keyboard.press(key)
    print(f"[ACTION] Pressed: {key}")
