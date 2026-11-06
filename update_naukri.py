import os
import json
import sys
from playwright.sync_api import sync_playwright, TimeoutError
from playwright_stealth import Stealth

def update_naukri_profile():
    cookies_str = os.environ.get('NAUKRI_COOKIES')

    if not cookies_str:
        print("❌ NAUKRI_COOKIES secret is missing or empty!")
        sys.exit(1)

    # NEW PATTERN FOR PLAYWRIGHT STEALTH v2.x
    with Stealth().use_sync(sync_playwright()) as p:
        # Launch with arguments to help bypass basic bot detection
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Set a large viewport so elements render, and use a realistic User-Agent
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            raw_cookies = json.loads(cookies_str)
            clean_cookies = []
            
            for cookie in raw_cookies:
                clean_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie["path"],
                    "secure": cookie.get("secure", False),
                    "httpOnly": cookie.get("httpOnly", False)
                }
                if "expirationDate" in cookie:
                    clean_cookie["expires"] = cookie["expirationDate"]
                if cookie.get("sameSite"):
                    clean_cookie["sameSite"] = "None" if cookie["sameSite"] == "no_restriction" else cookie["sameSite"].capitalize()
                
                clean_cookies.append(clean_cookie)

            context.add_cookies(clean_cookies)
            print("✅ Session cookies injected successfully.")
        except Exception as e:
            print(f"❌ Failed to parse cookies: {str(e)}")
            sys.exit(1)

        page = context.new_page()

        print("Navigating directly to profile page...")
        page.goto("https://www.naukri.com/mnjuser/profile")
        page.wait_for_load_state("networkidle")

        # Check for Access Denied page (Akamai WAF block)
        if "Access Denied" in page.title() or "edgesuite" in page.content():
            print("❌ Blocked by Akamai WAF (Access Denied). GitHub Actions IP is blacklisted.")
            page.screenshot(path="debug_error.png")
            browser.close()
            sys.exit(1)

        if "login" in page.url.lower():
            print("❌ Cookie bypass failed. Redirected to login page.")
            page.screenshot(path="debug_error.png")
            browser.close()
            sys.exit(1)
            
        print("✅ Successfully accessed profile page.")

        try:
            print("Triggering lazy load by scrolling...")
            for _ in range(4):
                page.mouse.wheel(0, 500)
                page.wait_for_timeout(1000)
            
            print("Waiting for Resume Headline section...")
            
            # Use valid playwright locators
            container_locator = page.locator("#lazyResumeHead, div:has-text('Resume headline')").first
            container_locator.wait_for(timeout=20000)
            
            # Click the Edit Button
            edit_btn = container_locator.locator(".edit.icon, span.edit, .widgetHead .edit").first
            edit_btn.click()
            
            # Wait for textarea to appear
            page.wait_for_selector("textarea", timeout=10000)
            
            text_area = page.locator(".resumeHeadlineEdit textarea, #lazyResumeHead textarea, textarea").first
            current_text = text_area.input_value().strip()
            print(f"Current headline: '{current_text}'")
            
            # Modify text (toggle trailing dot)
            if not current_text:
                new_text = "Software Engineer | Amazon Pay | Java, AWS, Distributed Systems"
            elif current_text.endswith("."):
                new_text = current_text[:-1] 
            else:
                new_text = current_text + "."
                
            print(f"New headline target: '{new_text}'")
            
            text_area.fill(new_text)
            page.wait_for_timeout(1000)
            
            # Click Save
            save_btn = page.locator("button:has-text('Save'), button:has-text('Submit')").first
            save_btn.click()
            
            page.wait_for_timeout(3500)
            print("✅ Resume Headline updated successfully.")
            
        except Exception as e:
            print(f"❌ Automation failed: {str(e)}")
            page.screenshot(path="debug_error.png")
            print("📸 Saved debug_error.png. Upload this as a GitHub Actions artifact to debug.")
            browser.close()
            sys.exit(1)
            
        browser.close()

if __name__ == "__main__":
    update_naukri_profile()
