import os
import json
import sys
from playwright.sync_api import sync_playwright
# Add this import
from playwright_stealth import stealth_sync

def update_naukri_profile():
    cookies_str = os.environ.get('NAUKRI_COOKIES')
    # ... [keep your existing cookie setup code] ...

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # ... [keep your existing cookie injection code] ...

        page = context.new_page()
        
        # APPLY STEALTH MODE to bypass basic Akamai checks
        stealth_sync(page)

        print("Navigating directly to profile page...")
        page.goto("https://www.naukri.com/mnjuser/profile")
        page.wait_for_load_state("networkidle")
        
        # Check for Access Denied page
        if "Access Denied" in page.title() or "edgesuite" in page.content():
            print("❌ Blocked by Akamai WAF (Access Denied). GitHub Actions IP is blacklisted.")
            page.screenshot(path="debug_error.png")
            browser.close()
            sys.exit(1)

        # ... [keep the login check code] ...

        try:
            print("Triggering lazy load by scrolling...")
            for _ in range(4):
                page.mouse.wheel(0, 500)
                page.wait_for_timeout(1000)
            
            print("Waiting for Resume Headline section...")
            
            # FIXED SYNTAX ERROR: Use has_text instead of mixing selector types
            container_locator = page.locator("#lazyResumeHead, div:has-text('Resume headline')").first
            container_locator.wait_for(timeout=20000)
            
            # ... [keep the rest of the clicking and saving code the same] ...
