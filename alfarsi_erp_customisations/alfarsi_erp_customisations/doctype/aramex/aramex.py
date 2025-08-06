# Copyright (c) 2025, Alfarsi and contributors
# For license information, please see license.txt

from xml.etree import ElementTree as ET

import requests
from frappe.model.document import Document

from alfarsi_erp_customisations.utils import build_soap_request_client_info


class Aramex(Document):
    def validate(self):
        if self.enabled:
            self.validate_credentials()


def check_credentials(client_info: dict):
    url = "https://ws.aramex.net/ShippingAPI/Location/Service_1_0.svc"
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://ws.aramex.net/ShippingAPI/v1/Service_1_0/FetchCountries",
    }
    body = build_soap_request_client_info(client_info)
    # return  requests.post(url, data=body, headers=headers, timeout=10)
    try:
        response = requests.post(url, data=body, headers=headers, timeout=10)
        print(response.__dict__)
        print("HTTP Status:", response.status_code)
        if response.status_code != 200:
            print("❌ HTTP error occurred.")
            print(response.text)
            return False

        # Parse <HasErrors> value from the SOAP response
        root = ET.fromstring(response.content)
        print(root)
        ns = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "v1": "http://ws.aramex.net/ShippingAPI/v1/",
        }
        has_errors = root.find(".//v1:HasErrors", ns)
        print("has_errors", has_errors)
        if has_errors is not None and has_errors.text == "true":
            print("❌ Invalid credentials.")
            return False
        else:
            print("✅ Credentials are valid.")
            return True

    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)
        return False
