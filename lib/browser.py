"""Camoufox browser control utilities"""

from pathlib import Path
from datetime import datetime
from camoufox.sync_api import Camoufox

SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"


class Browser:
    """Camoufox browser wrapper for Hermes"""
    
    def __init__(self, proxy: str = None, region: str = "US"):
        self.proxy = proxy
        self.region = region
        self._camoufox = None
        self._browser = None
        self._context = None
        self.page = None
        self.account_id = None
    
    def launch(self, account_id: str = None, headless: bool = True) -> bool:
        """Launch Camoufox browser with anti-fingerprinting"""
        try:
            self.account_id = account_id or "unknown"
            
            screenshot_dir = SCREENSHOTS_DIR / self.account_id
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Build proxy config for Playwright
            proxy_config = None
            if self.proxy:
                if "@" in self.proxy:
                    auth, host = self.proxy.rsplit("@", 1)
                    user, passwd = auth.split(":", 1)
                    ip, port = host.split(":")
                    proxy_config = {
                        "server": f"http://{ip}:{port}",
                        "username": user,
                        "password": passwd
                    }
                else:
                    proxy_config = {"server": f"http://{self.proxy}"}
            
            # Launch Camoufox as context manager style
            self._camoufox = Camoufox(headless=headless, geoip=True)
            self._browser = self._camoufox.__enter__()
            
            # Create context with proxy
            if proxy_config:
                self._context = self._browser.new_context(proxy=proxy_config)
            else:
                self._context = self._browser.new_context()
            
            self.page = self._context.new_page()
            
            print(f"[BROWSER] Launched for {self.account_id}")
            return True
            
        except Exception as e:
            print(f"[BROWSER] Launch error: {e}")
            return False
    
    def goto(self, url: str, wait_until: str = "networkidle") -> bool:
        """Navigate to URL"""
        try:
            self.page.goto(url, wait_until=wait_until, timeout=30000)
            print(f"[BROWSER] Navigated to {url}")
            return True
        except Exception as e:
            print(f"[BROWSER] Navigation error: {e}")
            return False
    
    def screenshot(self, name: str = None) -> str:
        """Take screenshot, return path"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name or screenshot}_{timestamp}.png"
            path = SCREENSHOTS_DIR / self.account_id / filename
            
            self.page.screenshot(path=str(path), full_page=False)
            print(f"[BROWSER] Screenshot: {path}")
            return str(path)
        except Exception as e:
            print(f"[BROWSER] Screenshot error: {e}")
            return ""
    
    def close(self):
        """Close browser"""
        try:
            if self._context:
                self._context.close()
            if self._camoufox:
                self._camoufox.__exit__(None, None, None)
            print(f"[BROWSER] Closed")
        except Exception as e:
            print(f"[BROWSER] Close error: {e}")
    
    def get_page(self):
        """Get Playwright page object for direct manipulation"""
        return self.page
    
    def current_url(self) -> str:
        """Get current page URL"""
        return self.page.url if self.page else ""


def launch_browser(account_id: str, proxy: str = None, region: str = "US", headless: bool = True):
    """Launch browser and return Browser instance"""
    browser = Browser(proxy=proxy, region=region)
    if browser.launch(account_id=account_id, headless=headless):
        return browser
    return None
