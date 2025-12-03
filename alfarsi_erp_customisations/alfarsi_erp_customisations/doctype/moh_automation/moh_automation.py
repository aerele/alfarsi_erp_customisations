# Copyright (c)
# License information

import json
import frappe
from frappe.model.document import Document
import asyncio
from playwright.async_api import async_playwright


class MOHAutomation(Document):
    pass

@frappe.whitelist()
def automate_moh_registration(selected_items):
    selected_items = json.loads(selected_items)
    results = []
    for item in selected_items:
        try:
            asyncio.run(submit_google_form(item))
            results.append(f"{item} → SUCCESS")
        except Exception as e:
            frappe.log_error(f"Error processing {item}: {str(e)}", "MOH Automation")
            results.append(f"{item} → FAILED ({str(e)})")

    return "\n".join(results)

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
            # STEP 1
            await page.goto(LOGIN_URL, timeout=90000)
            await page.wait_for_load_state("domcontentloaded")

            # STEP 2
            await page.locator("text=National ID Login").click(no_wait_after=True)

            # STEP 3
            for _ in range(200):
                if "idp.pki.ita.gov.om" in page.url:
                    break
                await asyncio.sleep(1)

            # STEP 4 – unlock audio
            await page.mouse.click(10, 10)

            # STEP 5 – alarm
            await page.evaluate("""
                try {
                    window.alarmAudio = new Audio(
                        'https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg'
                    );
                    window.alarmAudio.loop = true;
                    window.alarmAudio.play().catch(err => {});
                } catch (e) {}
            """)

            # STEP 6 – wait login
            for _ in range(300):
                if "MedicalDevice/Registration" in page.url:
                    break
                await asyncio.sleep(1)

            # STOP ALARM
            await page.evaluate("""
                if (window.alarmAudio) {
                    window.alarmAudio.pause();
                    window.alarmAudio.currentTime = 0;
                }
            """)

            # STEP 7 – wait dropdown
            await page.wait_for_selector("#b20-EstDropdown", timeout=120000)

            # STEP 8 – select establishment
            await page.select_option("#b20-EstDropdown", value="0")

            # STEP 9 – Verify
            await page.click("#b20-VerifyBtn")

            # STEP 10 – wait for CR number
            await page.wait_for_selector("#b20-CR_Number", timeout=120000)

        except Exception as e:
            frappe.log_error(f"Automation crashed: {str(e)}", "MOH Automation")
            raise

        finally:
            try:
                await context.close()
                await browser.close()
            except:
                pass
