import frappe
import requests

def send_whatsapp_message(to, message):
    url = (
        f"https://graph.facebook.com/v19.0/"
        f"{frappe.conf.whatsapp_phone_number_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {frappe.conf.whatsapp_access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
