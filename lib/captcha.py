"""
TikTok Captcha Solver using official SadCaptcha library
"""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "tiktok_bc_setup_config.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def get_api_key() -> str:
    config = load_config()
    return config.get("captcha", {}).get("api_key", "")

def solve_captcha_playwright(page, max_attempts: int = 3) -> bool:
    """
    Solve TikTok captcha using official SadCaptcha library with Playwright
    """
    try:
        from tiktok_captcha_solver import PlaywrightSolver
        
        api_key = get_api_key()
        if not api_key:
            print("[CAPTCHA] No API key configured!")
            return False
        
        solver = PlaywrightSolver(page, api_key)
        
        for attempt in range(max_attempts):
            print(f"[CAPTCHA] Solving attempt {attempt + 1}/{max_attempts}...")
            
            try:
                solver.solve_captcha_if_present()
                print("[CAPTCHA] Solved successfully!")
                return True
            except Exception as e:
                print(f"[CAPTCHA] Attempt {attempt + 1} failed: {e}")
        
        print("[CAPTCHA] All attempts failed")
        return False
        
    except ImportError:
        print("[CAPTCHA] tiktok-captcha-solver not installed!")
        print("[CAPTCHA] Run: pip install tiktok-captcha-solver")
        return False
    except Exception as e:
        print(f"[CAPTCHA] Error: {e}")
        return False

# Convenience alias
solve_captcha = solve_captcha_playwright
