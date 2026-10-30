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

        # Action 1: Upload the Resume PDF
        try:
            print("Attempting PDF upload...")
            page.set_input_files("input[type='file'][id='attachCV']", resume_path)
            page.wait_for_selector("text=successfully uploaded", timeout=10000)
            print("✅ PDF uploaded successfully.")
        except TimeoutError:
            print("⚠️ PDF upload success message not found. Moving to text toggle.")

        # Action 2: Toggle a space in the Resume Headline
        try:
            print("Attempting Resume Headline update...")
            page.click("xpath=//span[contains(text(), 'Resume headline')]/following-sibling::span[contains(@class, 'edit')]")
            
            page.wait_for_selector("textarea[id='resumeHeadlineTxt']", timeout=5000)
            current_text = page.input_value("textarea[id='resumeHeadlineTxt']")
            
            new_text = current_text[:-1] if current_text.endswith(' ') else current_text + ' '
                
            page.fill("textarea[id='resumeHeadlineTxt']", new_text)
            page.click("form[name='resumeHeadlineForm'] button[type='submit']")
            page.wait_for_selector("text=Resume Headline has been successfully saved", timeout=10000)
            print("✅ Resume Headline updated successfully.")
        except Exception as e:
            print(f"⚠️ Text toggle failed: {str(e)}")

        browser.close()

if __name__ == "__main__":
    update_naukri_profile()
