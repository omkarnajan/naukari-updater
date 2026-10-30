import os
import time
from playwright.sync_api import sync_playwright, TimeoutError

def update_naukri_profile():
    username = os.environ.get('NAUKRI_USERNAME')
    password = os.environ.get('NAUKRI_PASSWORD')
    resume_path = "resume.pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Navigating to Naukri login...")
        page.goto("https://login.naukri.com/nLogin/Login.php")

        print("Entering credentials...")
        page.fill("input[id='usernameField']", username)
        page.fill("input[id='passwordField']", password)
        page.click("button[type='submit']")

        # Wait for the dashboard to load to confirm login success
        page.wait_for_url("**/mnjuser/homepage**", timeout=15000)
        print("Login successful. Navigating to profile...")
        
        page.goto("https://www.naukri.com/mnjuser/profile")
        page.wait_for_load_state("networkidle")

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
            # Click the edit icon next to the 'Resume headline' section
            page.click("xpath=//span[contains(text(), 'Resume headline')]/following-sibling::span[contains(@class, 'edit')]")
            
            page.wait_for_selector("textarea[id='resumeHeadlineTxt']", timeout=5000)
            current_text = page.input_value("textarea[id='resumeHeadlineTxt']")
            
            # Toggle a trailing space
            if current_text.endswith(' '):
                new_text = current_text[:-1]
            else:
                new_text = current_text + ' '
                
            page.fill("textarea[id='resumeHeadlineTxt']", new_text)
            
            # Click Save
            page.click("form[name='resumeHeadlineForm'] button[type='submit']")
            page.wait_for_selector("text=Resume Headline has been successfully saved", timeout=10000)
            print("✅ Resume Headline updated successfully.")
        except Exception as e:
            print(f"⚠️ Text toggle failed: {str(e)}")

        browser.close()

if __name__ == "__main__":
    update_naukri_profile()
