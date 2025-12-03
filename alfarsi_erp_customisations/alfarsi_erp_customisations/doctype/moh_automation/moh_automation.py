# Copyright (c)
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
import asyncio
from playwright.async_api import async_playwright


class MOHAutomation(Document):
    pass


# -------------------------------
# MAIN API – Called from Button
# -------------------------------
@frappe.whitelist()
def automate_moh_registration(selected_items):
    selected_items = json.loads(selected_items)

    for item in selected_items:
        frappe.enqueue(
            "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.moh_automation.moh_automation.run_submit_form",
            queue="long",
            timeout=60000,
            item=item
        )

    return f"MOH Automation started for {len(selected_items)} items."


# -------------------------------
# Worker wrapper
# -------------------------------
def run_submit_form(item):
    try:
        asyncio.run(submit_google_form(item))
    except Exception as e:
        frappe.log_error(f"MOH Automation Error: {str(e)}", "MOH Automation")
        raise


# -------------------------------
# MAIN AUTOMATION SCRIPT
# -------------------------------
async def submit_google_form(item):

    LOGIN_URL = (
        "https://moh.gov.om/en/account/pki-login/"
        "?returnUrl=https%3A%2F%2Feportal.moh.gov.om%2FMedicalDevice%2FRegistration"
    )

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            # -------------------------
            # Step 1: Open login page
            # -------------------------
            print("Opening PKI login page...")
            await page.goto(LOGIN_URL, timeout=90000)
            await page.wait_for_load_state("domcontentloaded")

            # -------------------------
            # Step 2: Click National ID Login
            # -------------------------
            print("Clicking National ID Login...")
            await page.locator("text=National ID Login").click(no_wait_after=True)

            # -------------------------
            # Step 3: Detect redirect to SSO page
            # -------------------------
            print("Waiting for redirect to SSO (idp.pki.ita.gov.om)...")

            sso_reached = False

            for _ in range(200):
                url = page.url
                if "idp.pki.ita.gov.om" in url:
                    print("SSO page reached:", url)
                    sso_reached = True
                    break
                await asyncio.sleep(1)

            if not sso_reached:
                print("SSO page not reached.")
                return

            # -------------------------
            # Step 4: Unlock autoplay on SSO domain
            # -------------------------
            print("Simulating user click to unlock sound...")
            await page.mouse.click(10, 10)  # REAL user gesture → unlock audio

            # -------------------------
            # Step 5: Start Alarm Sound
            # -------------------------
            print("Starting alarm sound on SSO page...")

            await page.evaluate("""
                try {
                    window.alarmAudio = new Audio(
                        'https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg'
                    );
                    window.alarmAudio.loop = true;
                    window.alarmAudio.play().catch(e => console.log("Audio blocked:", e));
                } catch (e) { console.log(e); }
            """)

            # -------------------------
            # Step 6: Wait for user login to complete
            # -------------------------
            print("Waiting for user to finish login...")

            for _ in range(300):
                current_url = page.url
                if "MedicalDevice/Registration" in current_url:
                    print("User login completed:", current_url)
                    break
                await asyncio.sleep(1)
            else:
                print("User did not login in time.")
                return

            # -------------------------
            # Step 7: Stop Alarm
            # -------------------------
            print("Stopping alarm sound...")

            await page.evaluate("""
                if (window.alarmAudio) {
                    window.alarmAudio.pause();
                    window.alarmAudio.currentTime = 0;
                }
            """)

            # -------------------------
            # Step 8: Wait for Establishment dropdown
            # -------------------------
            print("Waiting for establishment dropdown...")
            await page.wait_for_selector("#b20-EstDropdown", timeout=120000)

            # -------------------------
            # Step 9: Select establishment
            # -------------------------
            print("Selecting AL FARSI NATIONAL ENTERPRISES...")
            await page.select_option("#b20-EstDropdown", value="0")

            # -------------------------
            # Step 10: Click Verify
            # -------------------------
            print("Clicking Verify...")
            await page.click("#b20-VerifyBtn")

            # -------------------------
            # Step 11: Wait for CR Number (establishment details)
            # -------------------------
            print("Waiting for establishment details...")
            await page.wait_for_selector("#b20-CR_Number", timeout=120000)

            print("Establishment details loaded successfully!")

        except Exception as e:
            print("ERROR:", e)
            frappe.log_error(f"MOH Error → {str(e)}", "MOH Automation")
            await asyncio.sleep(99999)  # KEEP BROWSER OPEN FOR DEBUG
        finally:
            await context.close()
            await browser.close()