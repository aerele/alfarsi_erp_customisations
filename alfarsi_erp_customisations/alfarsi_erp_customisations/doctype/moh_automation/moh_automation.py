# Copyright (c)
# License information

import json
import frappe
from frappe.model.document import Document
import asyncio
from playwright.async_api import async_playwright


class MOHAutomation(Document):
    pass


# ----------------------------------------------------------
# MAIN API – Called from ListView Button
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# MAIN AUTOMATION SCRIPT
# ----------------------------------------------------------
async def submit_google_form(item):

    LOGIN_URL = (
        "https://moh.gov.om/en/account/pki-login/"
        "?returnUrl=https%3A%2F%2Feportal.moh.gov.om%2FINRMD%2F"
    )

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            # STEP 1 — Open Login Page
            await page.goto(LOGIN_URL, timeout=150000)
            await page.wait_for_load_state("domcontentloaded")

            # STEP 2 — Click National ID Login
            await page.locator("text=National ID Login").click(no_wait_after=True)

            # STEP 3 — Wait for SSO Page
            for _ in range(300):
                if "idp.pki.ita.gov.om" in page.url:
                    break
                await asyncio.sleep(1)

            # STEP 4 — Unlock audio
            await page.mouse.click(10, 10)

            # STEP 5 — Play alarm
            await page.evaluate("""
                try {
                    window.alarmAudio = new Audio(
                        'https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg'
                    );
                    window.alarmAudio.loop = true;
                    window.alarmAudio.play().catch(err => {});
                } catch (e) {}
            """)

            # STEP 6 — Wait for SSO login completion
            for _ in range(450):
                if "INRMD" in page.url:
                    break
                await asyncio.sleep(1)

            # STOP alarm
            await page.evaluate("""
                if (window.alarmAudio) {
                    window.alarmAudio.pause();
                    window.alarmAudio.currentTime = 0;
                }
            """)

            # STEP 7 — Establishment Info
            await page.wait_for_selector("#b20-EstDropdown", timeout=180000)
            await page.select_option("#b20-EstDropdown", value="0")
            await page.click("#b20-VerifyBtn")

            await page.wait_for_selector("#b20-CR_Number:not([value=''])", timeout=240000)

            # Click Next
            print("Waiting for Next button to be enabled...")
            for _ in range(600):
                disabled = await page.evaluate("""document.querySelector('#NextBtn')?.disabled""")
                if disabled is False:
                    break
                await asyncio.sleep(1)

            await page.click("#NextBtn")
            print("Next button clicked successfully!")

            # --------------------------------------------------------
            # MEDICAL DEVICE INFO PAGE — UPDATED WITH CORRECT SELECTORS
            # --------------------------------------------------------
            print("Filling Medical Device Info Page...")

            await page.wait_for_load_state("domcontentloaded")

            # -------- Manufacturer Details --------

            # Manufacturer Name
            await page.fill("#b22-Input_manu_name", item.get("manufacturer_name"))

            # Manufacturer Country (search dropdown)
            await page.click("#b22-b2-DropdownSearch .vscomp-toggle-button")
            await page.fill("div.vscomp-search-input input", item.get("manufacturer_country", ""))
            await page.keyboard.press("Enter")

            # -------- Medical Device Details --------

            await page.fill("#b23-Input_MedDevName", item.get("medical_device_name"))
            await page.fill("#b23-Input_MedDevModel", item.get("medical_device_model"))

            await page.select_option("#b23-Dropdown1",
                                     label=item.get("medical_device_category", ""))

            await page.select_option("#b23-MedicalDeviceClassificationDropdown",
                                     label=item.get("medical_device_classification", ""))

            # --------------------------------------------------------
            # CLICK NEXT BUTTON ON MEDICAL DEVICE PAGE (CORRECT: NextBtn2)
            # --------------------------------------------------------
            print("Waiting for Next button on Device Info page...")

            for _ in range(300):
                disabled = await page.evaluate("""document.querySelector('#NextBtn2')?.disabled""")
                if disabled is False:
                    break
                await asyncio.sleep(1)

            await page.click("#NextBtn2")
            print("Medical Device Info Page Completed!")

        except Exception as e:
            frappe.log_error(f"Automation crashed: {str(e)}", "MOH Automation")
            raise

        finally:
            try:
                await context.close()
                await browser.close()
            except:
                pass
