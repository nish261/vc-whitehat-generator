"""
TikTok Captcha Solver - Playwright version
Uses SadCaptcha API for puzzle/shape captchas
"""

import requests
import base64
import time
import random
import json
from pathlib import Path
from typing import Optional, Dict

CONFIG_PATH = Path(__file__).parent.parent / "config" / "tiktok_bc_setup_config.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


class CaptchaSolver:
    """Solves TikTok captchas using SadCaptcha API"""
    
    PUZZLE_SELECTORS = [
        "#captcha-verify-image",
        ".captcha_verify_img--wrapper img",
        "img[id*=captcha]"
    ]
    
    PIECE_SELECTORS = [
        ".captcha_verify_img_slide",
        "img[class*=slide]",
        ".captcha-slider-piece"
    ]
    
    SLIDER_SELECTORS = [
        ".secsdk-captcha-drag-icon",
        ".captcha_verify_slide--slidebar",
        "[class*=drag-icon]"
    ]
    
    def __init__(self):
        config = load_config()
        captcha_config = config.get("captcha", {})
        self.api_url = captcha_config.get("api_url", "https://www.sadcaptcha.com/api/v1")
        self.api_key = captcha_config.get("api_key", "")
        self.fudge_factor = captcha_config.get("fudge_factor", -6)
    
    def detect(self, page) -> str:
        """Detect captcha type: slider, shape, rotate, or none"""
        for selector in self.PUZZLE_SELECTORS + self.PIECE_SELECTORS:
            try:
                if page.query_selector(selector):
                    return "slider"
            except:
                continue
        
        try:
            if page.query_selector("text=Select 2 objects"):
                return "shape"
        except:
            pass
        
        try:
            if page.query_selector("text=rotate") or page.query_selector("[class*=rotate]"):
                return "rotate"
        except:
            pass
        
        return "none"
    
    def solve_slider(self, page) -> bool:
        """Solve slider puzzle captcha"""
        try:
            print("[CAPTCHA] Solving slider puzzle...")
            
            puzzle_url = None
            for selector in self.PUZZLE_SELECTORS:
                try:
                    el = page.query_selector(selector)
                    if el:
                        puzzle_url = el.get_attribute("src")
                        break
                except:
                    continue
            
            piece_url = None
            for selector in self.PIECE_SELECTORS:
                try:
                    el = page.query_selector(selector)
                    if el:
                        piece_url = el.get_attribute("src")
                        break
                except:
                    continue
            
            if not puzzle_url or not piece_url:
                print("[CAPTCHA] Could not find puzzle images")
                return False
            
            puzzle_el = page.query_selector(self.PUZZLE_SELECTORS[0])
            box = puzzle_el.bounding_box() if puzzle_el else None
            puzzle_width = box["width"] if box else 340
            
            solution = self._call_sadcaptcha_slider(puzzle_url, piece_url)
            if not solution:
                return False
            
            slide_x = solution.get("slideXProportion", 0) * puzzle_width + self.fudge_factor
            print(f"[CAPTCHA] Slide distance: {slide_x}px")
            
            return self._drag_slider(page, slide_x)
            
        except Exception as e:
            print(f"[CAPTCHA] Slider error: {e}")
            return False
    
    def solve_shape(self, page) -> bool:
        """Solve shape matching captcha"""
        try:
            print("[CAPTCHA] Solving shape captcha...")
            
            captcha_el = page.query_selector(".captcha-verify-container") or page.query_selector("[class*=captcha]")
            if not captcha_el:
                print("[CAPTCHA] Could not find captcha container")
                return False
            
            screenshot = captcha_el.screenshot()
            b64_image = base64.b64encode(screenshot).decode()
            
            solution = self._call_sadcaptcha_shapes(b64_image)
            if not solution:
                return False
            
            points = solution.get("points", [])
            box = captcha_el.bounding_box()
            
            for point in points:
                x, y = point.get("x", 0), point.get("y", 0)
                page.mouse.click(box["x"] + x, box["y"] + y)
                time.sleep(random.uniform(0.3, 0.6))
            
            print(f"[CAPTCHA] Clicked {len(points)} shapes")
            return True
            
        except Exception as e:
            print(f"[CAPTCHA] Shape error: {e}")
            return False
    
    def solve(self, page, max_attempts: int = 3) -> bool:
        """Detect and solve any captcha type"""
        for attempt in range(max_attempts):
            captcha_type = self.detect(page)
            
            if captcha_type == "none":
                print("[CAPTCHA] No captcha detected")
                return True
            
            print(f"[CAPTCHA] Detected: {captcha_type} (attempt {attempt + 1}/{max_attempts})")
            
            if captcha_type == "slider":
                if self.solve_slider(page):
                    time.sleep(2)
                    if self.detect(page) == "none":
                        return True
            
            elif captcha_type == "shape":
                if self.solve_shape(page):
                    time.sleep(2)
                    if self.detect(page) == "none":
                        return True
            
            time.sleep(2)
        
        print("[CAPTCHA] Failed after max attempts")
        return False
    
    def _call_sadcaptcha_slider(self, puzzle_url: str, piece_url: str) -> Optional[Dict]:
        """Call SadCaptcha API for slider puzzle"""
        try:
            response = requests.post(
                f"{self.api_url}/puzzle",
                params={"licenseKey": self.api_key},
                json={
                    "puzzleImageUrl": puzzle_url,
                    "pieceImageUrl": piece_url
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[CAPTCHA] API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[CAPTCHA] API call failed: {e}")
            return None
    
    def _call_sadcaptcha_shapes(self, b64_image: str) -> Optional[Dict]:
        """Call SadCaptcha API for shape matching"""
        try:
            response = requests.post(
                f"{self.api_url}/shapes",
                params={"licenseKey": self.api_key},
                json={"image": b64_image},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[CAPTCHA] API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[CAPTCHA] API call failed: {e}")
            return None
    
    def _drag_slider(self, page, distance: float) -> bool:
        """Drag slider with human-like movement"""
        try:
            slider = None
            for selector in self.SLIDER_SELECTORS:
                slider = page.query_selector(selector)
                if slider:
                    break
            
            if not slider:
                print("[CAPTCHA] Could not find slider")
                return False
            
            box = slider.bounding_box()
            start_x = box["x"] + box["width"] / 2
            start_y = box["y"] + box["height"] / 2
            
            page.mouse.move(start_x, start_y)
            page.mouse.down()
            
            steps = int(distance / 5)
            for i in range(steps):
                x = start_x + (i + 1) * (distance / steps)
                y = start_y + random.uniform(-2, 2)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.01, 0.02))
            
            page.mouse.up()
            print("[CAPTCHA] Drag completed")
            return True
            
        except Exception as e:
            print(f"[CAPTCHA] Drag failed: {e}")
            return False


def solve_captcha(page, max_attempts: int = 3) -> bool:
    """Detect and solve any captcha"""
    solver = CaptchaSolver()
    return solver.solve(page, max_attempts)
