# # Copyright (c) 2025, Alfarsi
# # License information

# import json
# import frappe
# import asyncio
# from playwright.async_api import async_playwright
# from frappe.model.document import Document


# class MOHAutomation(Document):
#     pass

# @frappe.whitelist()
# def get_po_data(purchase_order):
#     po = frappe.get_doc("Purchase Order", purchase_order)
#     items = []
#     for row in po.items:
#         item_doc = frappe.get_doc("Item", row.item_code)
#         items.append({
#             "medical_device_item_code": row.item_code,
#             "item_name": row.item_name,
#             "medical_device_category": item_doc.custom_medical_device_category or "",
#             "medical_device_classification": item_doc.custom_medical_device_classification or "",
#             "medical_device_model": item_doc.custom_medical_device_model or "",
#             "moh_application_no": item_doc.custom_moh_application_no or "",
#             "moh_approval_no": item_doc.custom_moh_approval_no or "",
#         })


#     return {
#         "supplier": po.supplier,
#         "items": items
#     }

# @frappe.whitelist()
# def automate_moh_registration(selected_items):
#     selected_items = json.loads(selected_items)

#     for item in selected_items:
#         asyncio.run(run_moh_automation(item))
#     return "MOH Registration automation started. Chromium will open on server."

# async def run_moh_automation(item):

#     LOGIN_URL = (
#         "https://moh.gov.om/en/account/pki-login/"
#         "?returnUrl=https%3A%2F%2Feportal.moh.gov.om%2FINRMD%2F"
#     )

#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)
#         context = await browser.new_context(ignore_https_errors=True)
#         page = await context.new_page()

#         try:
#             frappe.log_error("MOH Automation Started", "MOH DEBUG")
#             # ---------------- LOGIN ----------------
#             await page.goto(LOGIN_URL, timeout=150000)
#             await page.wait_for_load_state("domcontentloaded")

#             await page.locator("text=National ID Login").click(no_wait_after=True)

#             # Wait for PKI redirect
#             for _ in range(300):
#                 if "idp.pki.ita.gov.om" in page.url:
#                     break
#                 await asyncio.sleep(1)

#             # Unlock audio
#             await page.mouse.click(10, 10)

#             # Alarm
#             await page.evaluate("""
#                 try {
#                     window.alarmAudio = new Audio(
#                         'https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg'
#                     );
#                     window.alarmAudio.loop = true;
#                     window.alarmAudio.play();
#                 } catch (e) {}
#             """)

#             # Wait until login completes
#             for _ in range(450):
#                 if "INRMD" in page.url:
#                     break
#                 await asyncio.sleep(1)
#             else:
#                 raise Exception("PKI login timeout")

#             # Stop alarm
#             await page.evaluate("""
#                 if (window.alarmAudio) {
#                     window.alarmAudio.pause();
#                     window.alarmAudio.currentTime = 0;
#                 }
#             """)

#             # ---------------- ESTABLISHMENT ----------------
#             await page.wait_for_selector("#b20-EstDropdown", timeout=180000)
#             await page.select_option("#b20-EstDropdown", value="0")
#             await page.click("#b20-VerifyBtn")

#             await page.wait_for_selector("#NextBtn:not([disabled])", timeout=240000)
#             await page.click("#NextBtn")

#             # ---------------- MEDICAL DEVICE INFO ----------------
#             await page.wait_for_load_state("domcontentloaded")

#             await page.fill("#b22-Input_manu_name", item.get("manufacturer_name", ""))
#             await page.click("#b22-b2-DropdownSearch .vscomp-toggle-button")
#             await page.fill("div.vscomp-search-input input", item.get("manufacturer_country", ""))
#             await page.keyboard.press("Enter")

#             await page.fill("#b23-Input_MedDevName", item.get("item_name", ""))
#             await page.fill("#b23-Input_MedDevModel", item.get("medical_device_model", ""))

#             await page.select_option(
#                 "#b23-Dropdown1",
#                 label=item.get("medical_device_category", "")
#             )

#             await page.select_option(
#                 "#b23-MedicalDeviceClassificationDropdown",
#                 label=item.get("medical_device_classification", "")
#             )

#             await page.wait_for_selector("#NextBtn2:not([disabled])", timeout=300000)
#             await page.click("#NextBtn2")
#             await page.click("#NextBtn4")

#             await page.wait_for_selector("#b39-Checkbox", timeout=30000)
#             await page.check("#b39-Checkbox")

#             await page.evaluate("document.querySelector('#Submit').scrollIntoView()")
#             await page.wait_for_selector("#Submit:not([disabled])", timeout=300000)
#             await page.click("#Submit")

#             await page.wait_for_selector("button:has-text('Confirm')", timeout=30000)
#             await page.click("button:has-text('Confirm')")
#             await page.wait_for_selector("#b7-ApplicationNumber", timeout=30000)
#             application_number = (await page.inner_text("#b7-ApplicationNumber")).strip()

#             item_code = item.get("medical_device_item_code")

#             frappe.db.set_value(
#                 "Item",
#                 item_code,
#                 "custom_moh_application_no",
#                 application_number
#             )

#             await page.click("#b7-MyApplications")
#             await page.wait_for_load_state("networkidle")
#             await page.select_option("#DrpdownSearchBy", value="0")
#             await page.fill("#Input_GlobalSearch2", application_number)
#             await page.click("button:has(i.fa-search)")

#             await asyncio.sleep(3)

#             await page.click(f"a:has-text('{application_number}')")

#             await page.wait_for_selector(
#                 "span.font-bold:has-text('Non-Registered Medical Device Number')",
#                 timeout=30000
#             )

#             approval_text = await page.inner_text(
#                 "span.font-bold:has-text('Non-Registered Medical Device Number')"
#             )

#             moh_approval_no = approval_text.split(":")[-1].strip()

#             frappe.db.set_value(
#                 "Item",
#                 item_code,
#                 "custom_moh_approval_no",
#                 moh_approval_no
#             )

#             frappe.db.commit()

#         except Exception as e:
#             frappe.log_error(str(e), "MOH Automation Error")
#             raise

#         finally:
#             await context.close()
#             await browser.close()
# import json
# import os
# import asyncio
# import importlib.util
# import frappe
# from frappe.model.document import Document


# DESKTOP_SCRIPT_PATH = os.path.expanduser("~/Desktop/moh_runner.py")


# class MOHAutomation(Document):
#     pass


# # ✅ THIS WAS MISSING — NOW FIXED
# @frappe.whitelist()
# def get_po_data(purchase_order):
#     po = frappe.get_doc("Purchase Order", purchase_order)
#     items = []

#     for row in po.items:
#         item_doc = frappe.get_doc("Item", row.item_code)
#         items.append({
#             "medical_device_item_code": row.item_code,
#             "item_name": row.item_name,
#             "medical_device_category": item_doc.custom_medical_device_category or "",
#             "medical_device_classification": item_doc.custom_medical_device_classification or "",
#             "medical_device_model": item_doc.custom_medical_device_model or "",
#             "moh_application_no": item_doc.custom_moh_application_no or "",
#             "moh_approval_no": item_doc.custom_moh_approval_no or "",
#         })

#     return {
#         "supplier": po.supplier,
#         "items": items
#     }


# def load_moh_runner():
#     if not os.path.exists(DESKTOP_SCRIPT_PATH):
#         frappe.throw("moh_runner.py not found on Desktop")

#     spec = importlib.util.spec_from_file_location(
#         "moh_runner_desktop",
#         DESKTOP_SCRIPT_PATH
#     )
#     module = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(module)
#     return module


# def run_moh_automation_job(item):
#     runner = load_moh_runner()
#     asyncio.run(runner.run_moh_automation(item))


# @frappe.whitelist()
# def automate_moh_registration(selected_items):
#     selected_items = json.loads(selected_items)

#     for item in selected_items:
#         frappe.enqueue(
#             "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.moh_automation.moh_automation.run_moh_automation_job",
#             item=item,
#             queue="long",
#             timeout=3600
#         )

#     return "MOH Automation started in background"

# import json
# import requests
# import frappe
# from frappe.model.document import Document

# MOH_AGENT_URL = "https://intercessional-dryly-roselle.ngrok-free.dev/run"


# class MOHAutomation(Document):
#     pass

# @frappe.whitelist()
# def get_po_data(purchase_order):
#     po = frappe.get_doc("Purchase Order", purchase_order)
#     items = []

#     for row in po.items:
#         item_doc = frappe.get_doc("Item", row.item_code)
#         items.append({
#         "medical_device_item_code": row.item_code,
#         "item_name": row.item_name,
#         "medical_device_model": item_doc.custom_medical_device_model or "",
#         "manufacturer_name": po.supplier
#     })


#     return {
#         "supplier": po.supplier,
#         "items": items
#     }

# def run_moh_automation_job(item):
#     resp = requests.post(MOH_AGENT_URL, json=item, timeout=1800)
#     resp.raise_for_status()

#     data = resp.json()
#     application_number = data["application_number"]

#     frappe.db.set_value(
#         "Item",
#         item["medical_device_item_code"],
#         "custom_moh_application_no",
#         application_number
#     )
#     frappe.db.commit()

# @frappe.whitelist()
# def automate_moh_registration(selected_items):
#     selected_items = json.loads(selected_items)

#     for item in selected_items:
#         frappe.enqueue(
#             "alfarsi_erp_customisations.alfarsi_erp_customisations.doctype.moh_automation.moh_automation.run_moh_automation_job",
#             item=item,
#             queue="long",
#             timeout=3600
#         )

#     return "MOH automation sent to PKI agent"

import frappe
import requests
from frappe.model.document import Document

NGROK_URL = "https://mechelle-skirtless-tinley.ngrok-free.dev/run"


class MOHAutomation(Document):
    pass

@frappe.whitelist()
def get_po_data(purchase_order):
    po = frappe.get_doc("Purchase Order", purchase_order)
    items = []

    for row in po.items:
        item_doc = frappe.get_doc("Item", row.item_code)
        items.append({
        "medical_device_item_code": row.item_code,
        "item_name": row.item_name,
        "medical_device_model": item_doc.custom_medical_device_model or "",
        "manufacturer_name": po.supplier
    })


    return {
        "supplier": po.supplier,
        "items": items
    }


# User clicks button in ERP
@frappe.whitelist()
def trigger_moh(moh_doc):
    requests.post(
        NGROK_URL,
        json={"moh_doc": moh_doc},
        timeout=240
    )
    return "MOH automation started"


# PC fetches MOH Automation doc
@frappe.whitelist()
def get_moh_doc(moh_doc):
    doc = frappe.get_doc("MOH Automation", moh_doc)
    return doc.as_dict()


# PC sends back MOH result
@frappe.whitelist()
def update_moh_result(
    moh_doc,
    item_code,
    application_no,
    approval_no=None,
    medical_device_name=None,
):

    doc = frappe.get_doc("MOH Automation", moh_doc)
    for row in doc.medical_devices:
        if row.medical_device_item_code == item_code:
            row.moh_application_no = application_no
            row.moh_approval_no = approval_no
    doc.save(ignore_permissions=True)

    frappe.db.set_value(
        "Item",
        item_code,
        {
            "custom_moh_application_no": application_no,
            "custom_moh_approval_no": approval_no,
            "custom_medical_device_name": medical_device_name,
        }
    )
    return {
        "status": "success",
        "application_no": application_no,
        "approval_no": approval_no,
        "medical_device_name": medical_device_name,
    }
