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
            asyncio.run(run_moh_automation(item))
            results.append(f"{item} → SUCCESS")
        except Exception as e:
            frappe.log_error(f"Error processing {item}: {str(e)}", "MOH Automation")
            results.append(f"{item} → FAILED ({str(e)})")
    return "\n".join(results)



async def run_moh_automation(item):

    LOGIN_URL = (
        "https://moh.gov.om/en/account/pki-login/"
        "?returnUrl=https%3A%2F%2Feportal.moh.gov.om%2FINRMD%2F"
    )

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            # STEP 1 — Login Page
            await page.goto(LOGIN_URL, timeout=150000)
            await page.wait_for_load_state("domcontentloaded")

            # STEP 2 — Click National ID Login
            await page.locator("text=National ID Login").click(no_wait_after=True)

            # STEP 3 — Wait for SSO redirect
            for _ in range(300):
                if "idp.pki.ita.gov.om" in page.url:
                    break
                await asyncio.sleep(1)

            # STEP 4 — Click page to unlock audio
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

            # STEP 6 — Wait for login completion
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
            for _ in range(600):
                disabled = await page.evaluate("document.querySelector('#NextBtn')?.disabled")
                if disabled is False:
                    break
                await asyncio.sleep(1)
            await page.click("#NextBtn")


            # --------------------------------------------------------
            # MEDICAL DEVICE INFO PAGE
            # --------------------------------------------------------
            await page.wait_for_load_state("domcontentloaded")

            await page.fill("#b22-Input_manu_name", item.get("manufacturer_name"))
            await page.click("#b22-b2-DropdownSearch .vscomp-toggle-button")
            await page.fill("div.vscomp-search-input input", item.get("manufacturer_country", ""))
            await page.keyboard.press("Enter")

            await page.fill("#b23-Input_MedDevName", item.get("medical_device_name"))
            await page.fill("#b23-Input_MedDevModel", item.get("medical_device_model"))

            await page.select_option("#b23-Dropdown1", label=item.get("medical_device_category", ""))
            await page.select_option("#b23-MedicalDeviceClassificationDropdown",
                                     label=item.get("medical_device_classification", ""))

            for _ in range(300):
                disabled = await page.evaluate("document.querySelector('#NextBtn2')?.disabled")
                if disabled is False:
                    break
                await asyncio.sleep(1)
            await page.click("#NextBtn2")

            await page.click("#NextBtn4")
            await page.wait_for_load_state("domcontentloaded")


            # --------------------------------------------------------
            # DECLARATION + SUBMIT
            # --------------------------------------------------------
            await page.wait_for_selector("#b39-Checkbox", timeout=20000)
            await page.check("#b39-Checkbox")

            for _ in range(300):
                disabled = await page.evaluate("document.querySelector('#Submit')?.disabled")
                if disabled is False:
                    break
                await asyncio.sleep(1)

            await page.evaluate("document.querySelector('#Submit').scrollIntoView()")
            try:
                await page.click("#Submit")
            except:
                await page.evaluate("document.getElementById('Submit').click()")

            # Confirm popup
            await page.wait_for_selector("button:has-text('Confirm')", timeout=20000)
            try:
                await page.click("button:has-text('Confirm')")
            except:
                await page.evaluate("""
                    [...document.querySelectorAll('button')]
                    .find(btn => btn.innerText.includes('Confirm'))
                    ?.click()
                """)


            # --------------------------------------------------------
            # EXTRACT APPLICATION NUMBER
            # --------------------------------------------------------
            await page.wait_for_selector("#b7-ApplicationNumber", timeout=20000)
            application_number = (await page.inner_text("#b7-ApplicationNumber")).strip()

            # Save into ERPNext Doc
            doc = frappe.get_doc("MOH Automation", item.get("medical_device_item_code"))
            doc.moh_application_no = application_number
            doc.save()


            # --------------------------------------------------------
            # OPEN "MY APPLICATIONS"
            # --------------------------------------------------------
            await page.wait_for_selector("#b7-MyApplications", timeout=20000)
            try:
                await page.click("#b7-MyApplications")
            except:
                await page.evaluate("document.getElementById('b7-MyApplications').click()")

            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)


            # --------------------------------------------------------
            # SEARCH BY APPLICATION NUMBER
            # --------------------------------------------------------
            await page.wait_for_selector("#DrpdownSearchBy", timeout=20000)
            await page.select_option("#DrpdownSearchBy", value="0")

            await page.wait_for_selector("#Input_GlobalSearch2", timeout=20000)
            await page.fill("#Input_GlobalSearch2", application_number)

            # CLICK SEARCH BUTTON (correct selector)
            await page.wait_for_selector("button:has(i.fa-search)", timeout=20000)
            await page.click("button:has(i.fa-search)")

            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)


            # --------------------------------------------------------
            # OPEN THE APPLICATION FROM THE TABLE
            # --------------------------------------------------------
            row_selector = f"a:has-text('{application_number}')"
            await page.wait_for_selector(row_selector, timeout=20000)
            await page.click(row_selector)

            await page.wait_for_selector(
                "span.font-bold:has-text('Non-Registered Medical Device Number')",
                timeout=30000
            )

            approval_text = await page.inner_text(
                "span.font-bold:has-text('Non-Registered Medical Device Number')"
            )

            moh_approval_no = approval_text.split(":")[-1].strip()
            doc.moh_approval_no=moh_approval_no
            doc.save()


        except Exception as e:
            frappe.log_error(f"Automation crashed: {str(e)}", "MOH Automation")
            raise

        finally:
            try:
                await context.close()
                await browser.close()
            except:
                pass

