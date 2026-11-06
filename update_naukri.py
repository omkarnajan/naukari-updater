import os
import json
import sys
from playwright.sync_api import sync_playwright, TimeoutError

def update_naukri_profile():
    cookies_str = os.environ.get('NAUKRI_COOKIES')
    resume_path = "Omkar_Najan_Resume.pdf"

    if not cookies_str:
        print("❌ NAUKRI_COOKIES secret is missing or empty!")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            raw_cookies = json.loads(cookies_str)
            clean_cookies = []
            
            # Automatically clean and format the cookies for Playwright
            for cookie in raw_cookies:
                clean_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie["path"],
                    "secure": cookie.get("secure", False),
                    "httpOnly": cookie.get("httpOnly", False)
                }
                # Translate expirationDate to expires
                if "expirationDate" in cookie:
                    clean_cookie["expires"] = cookie["expirationDate"]
                
                # Map SameSite values correctly
                if cookie.get("sameSite"):
                    if cookie["sameSite"] == "no_restriction":
                        clean_cookie["sameSite"] = "None"
                    else:
                        clean_cookie["sameSite"] = cookie["sameSite"].capitalize()
                
                clean_cookies.append(clean_cookie)

            context.add_cookies(clean_cookies)
            print("✅ Session cookies injected successfully.")
        except Exception as e:
            print(f"❌ Failed to parse or inject cookies JSON: {str(e)}")
            sys.exit(1)

        page = context.new_page()

        print("Navigating directly to profile page...")
        page.goto("https://www.naukri.com/mnjuser/profile")
        page.wait_for_load_state("networkidle")

        if "login" in page.url.lower():
            print("❌ Cookie bypass failed. Naukri redirected to the login page. Your cookies may have expired.")
            browser.close()
            sys.exit(1)
            
        print("✅ Successfully accessed profile page.")

        # ==========================================
        # ACTION 1: Upload the Resume PDF (COMMENTED OUT)
        # ==========================================
        # try:
        #     print("Attempting PDF upload...")
        #     page.set_input_files("input[type='file'][id='attachCV']", resume_path)
        #     page.wait_for_selector(f"div[title='{resume_path}']", timeout=15000)
        #     print("✅ PDF uploaded successfully.")
        # except TimeoutError:
        #     print("⚠️ PDF upload success message not found. Moving to text toggle.")

        # ==========================================
        # ACTION 2: Update the Resume Headline
        # ==========================================
        try:
            print("Attempting Resume Headline update...")
            
            # 1. SCROLL and WAIT for the main lazy-loaded container
            page.wait_for_selector("#lazyResumeHead", timeout=15000)
            resume_container = page.locator("#lazyResumeHead")
            resume_container.scroll_into_view_if_needed()
            page.wait_for_timeout(2000) # Give React time to hydrate the UI
            
            # 2. Click the Edit Button using robust selectors
            # Matches behavior in JS: "span.edit.icon, .edit.icon, span.edit, .edit"
            edit_btn = resume_container.locator(".edit.icon, span.edit, .widgetHead .edit").first
            edit_btn.click()
            
            # Wait for textarea to appear
            page.wait_for_selector("textarea", timeout=10000)
            
            # Locate the textarea inside the active lightbox/editor
            text_area = page.locator(".resumeHeadlineEdit textarea, #lazyResumeHead textarea, textarea").first
            current_text = text_area.input_value().strip()
            print(f"Current headline: '{current_text}'")
            
            # 3. Modify text (toggle trailing dot to register a difference)
            if not current_text:
                new_text = "Software Engineer | Amazon Pay | Java, AWS, Distributed Systems"
            elif current_text.endswith("."):
                new_text = current_text[:-1]  # Remove dot
            else:
                new_text = current_text + "." # Add dot
                
            print(f"New headline target: '{new_text}'")
            
            # Fill the new text (Playwright handles React's onChange events nicely via fill)
            text_area.fill(new_text)
            page.wait_for_timeout(500)
            
            # 4. Click Save
            # Look for generic save buttons in the container (like the JS does)
            save_btn = page.locator("button:has-text('Save'), button:has-text('Submit'), form button[type='submit']").first
            save_btn.click()
            
            # Wait for save modal to disappear / process
            page.wait_for_timeout(3500)
            print("✅ Resume Headline updated successfully.")
            
        except Exception as e:
            # Tell GitHub to fail the action if this breaks!
            print(f"❌ Text toggle failed: {str(e)}")
            browser.close()
            sys.exit(1)
            
        browser.close()

if __name__ == "__main__":
    update_naukri_profile()
