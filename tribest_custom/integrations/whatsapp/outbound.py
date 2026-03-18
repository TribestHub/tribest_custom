import frappe
import requests
import base64
import urllib3
import re
from html.parser import HTMLParser

# Suppress SSL warnings (Infobip has certificate issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MLStripper(HTMLParser):
    """Strip HTML tags from text"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_html_tags(html_text):
    """Remove HTML tags from text"""
    if not html_text:
        return html_text
    stripper = MLStripper()
    stripper.feed(html_text)
    return stripper.get_data()


def send_whatsapp_message(phone_number: str, message: str) -> dict:
    """
    Send WhatsApp text message via Infobip.
    Returns Infobip JSON response.
    
    message: Can be HTML or plain text - will be converted to plain text
    """

    # Strip HTML tags from message (Frappe stores as HTML, WhatsApp needs plain text)
    if message:
        message = strip_html_tags(message).strip()

    api_key = frappe.conf.get("infobip_api_key")
    base_url = frappe.conf.get("infobip_base_url")
    sender = frappe.conf.get("infobip_sender")

    if not api_key or not base_url or not sender:
        frappe.log_error(
            f"Config missing - api_key: {bool(api_key)}, base_url: {bool(base_url)}, sender: {bool(sender)}",
            "WhatsApp Outbound Config Error"
        )
        return {}

    # Ensure base_url has scheme
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"

    url = f"{base_url}/whatsapp/1/message/text"

    # Try API key format (check Infobip docs for your account type)
    # Format: "Authorization: App <api_key>"
    headers = {
        "Authorization": f"App {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "from": sender,
        "to": phone_number,
        "content": {
            "text": message
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15,
            verify=False  # Skip SSL verification (Infobip certificate issue)
        )

        # Log non-success responses
        if response.status_code not in (200, 201):
            frappe.log_error(
                f"Infobip Status: {response.status_code}\nURL: {url}\nHeaders: {headers}\nResponse: {response.text}",
                "Infobip Outbound Error"
            )
            return {}

        return response.json()

    except requests.Timeout:
        frappe.log_error("Infobip request timeout", "WhatsApp Outbound Timeout")
        return {}

    except Exception:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Outbound Exception")
        return {}