import frappe
from tribest_custom.integrations.whatsapp.inbound import process_inbound
from tribest_custom.integrations.whatsapp.settings import get_infobip_webhook_secret
import hashlib
import hmac


@frappe.whitelist(allow_guest=True)
def infobip_webhook():
    """
    Public inbound webhook for Infobip WhatsApp.
    Accepts POST only.
    """

    # Allow POST only
    if frappe.request.method != "POST":
        frappe.response["http_status_code"] = 405
        return "Method Not Allowed"

    try:
        # Validate signature if configured
        # validate_infobip_signature()

        # Parse JSON body
        data = frappe.request.get_json()

        if not data:
            frappe.response["http_status_code"] = 400
            return "Invalid payload"

        # Enqueue background processing
        frappe.enqueue(
            process_inbound,
            data=data,
            queue="short",
            timeout=300
        )

        return "OK"

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Infobip Webhook Error")
        frappe.response["http_status_code"] = 500
        return "Error"


def validate_infobip_signature():
    """
    Optional security validation using X-IB-Signature.
    Retrieves secret from Tribest Custom Setting doctype singlet.
    """

    secret = get_infobip_webhook_secret()
    if not secret:
        return  # Skip validation if not set

    signature = frappe.request.headers.get("X-IB-Signature")
    if not signature:
        frappe.throw("Missing Infobip signature")

    raw_body = frappe.request.get_data()

    expected_signature = hmac.new(
        secret.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        frappe.throw("Invalid Infobip signature")
