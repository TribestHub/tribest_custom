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



@frappe.whitelist()
def check_fixtures():
    import json
    import os

    result = {}

    # Check 1: Does fixture file exist on server?
    app_path = frappe.get_app_path("tribest_custom")
    fixture_path = os.path.join(app_path, "fixtures", "custom_field.json")
    result["fixture_file_exists"] = os.path.exists(fixture_path)
    result["fixture_path"] = fixture_path

    # Check 2: Read fixture file content
    if result["fixture_file_exists"]:
        with open(fixture_path, "r") as f:
            result["fixture_content"] = json.load(f)
    else:
        result["fixture_content"] = None

    # Check 3: What fixtures hook does Frappe see?
    result["fixtures_hook"] = frappe.get_hooks(
        "fixtures", app_name="tribest_custom"
    )

    # Check 4: Are fields in DB?
    result["fields_in_db"] = frappe.db.get_all(
        "Custom Field",
        filters={"dt": "HD Ticket"},
        fields=["name", "fieldname", "label"]
    )

    # Check 5: Try creating the field right now
    try:
        if not frappe.db.exists("Custom Field", "HD Ticket-custom_medium"):
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "HD Ticket",
                "fieldname": "custom_medium",
                "fieldtype": "Select",
                "label": "Medium",
                "options": "Email\nWhatsApp\nChat\nPhone\nOther",
                "insert_after": "status",
            }).insert(ignore_permissions=True)
            frappe.db.commit()
            result["manual_insert"] = "Created successfully"
        else:
            result["manual_insert"] = "Already exists"
    except Exception as e:
        result["manual_insert"] = f"FAILED: {str(e)}"

    return result