"""
WhatsApp Integration Settings Helper
Retrieves configuration from Tribest Custom Setting doctype singlet
"""

import frappe
from frappe.utils.password import get_decrypted_password


def get_setting(field_name: str, default_value=None):
    """
    Retrieve a setting from Tribest Custom Setting doctype.
    
    Args:
        field_name: Field name in the doctype (e.g., 'infobip_api_key')
        default_value: Default value if setting is not found
    
    Returns:
        The setting value or default_value
    """
    try:
        doc = frappe.get_doc("Tribest Custom Setting", "Tribest Custom Setting")
        return getattr(doc, field_name, default_value)
    except frappe.DoesNotExistError:
        frappe.log_error(
            f"Tribest Custom Setting not found. Please create it in the UI.",
            "Settings Configuration Error"
        )
        return default_value
    except AttributeError:
        frappe.log_error(
            f"Field '{field_name}' not found in Tribest Custom Setting",
            "Settings Field Error"
        )
        return default_value


def get_password_setting(field_name: str):
    """
    Retrieve a Password fieldtype setting (decrypted) from Tribest Custom Setting.
    """
    try:
        return get_decrypted_password(
            "Tribest Custom Setting",
            "Tribest Custom Setting",
            field_name
        ) or ""
    except Exception:
        frappe.log_error(
            f"Failed to decrypt password field '{field_name}'",
            "Settings Decryption Error"
        )
        return ""


def get_infobip_api_key():
    """Get Infobip API Key"""
    return get_password_setting("infobip_api_key")


def get_infobip_base_url():
    """Get Infobip Base URL"""
    return (get_setting("infobip_base_url") or "").strip()


def get_infobip_sender():
    """Get Infobip Sender ID"""
    return (get_setting("infobip_sender") or "").strip()


def get_infobip_webhook_secret():
    """Get Infobip Webhook Secret"""
    return get_password_setting("infobip_webhook_secret")


def get_whatsapp_webhook_user():
    """Get WhatsApp Webhook User (defaults to whatsapp.bot@yourcompany.com if not configured)"""
    return get_setting("whatsapp_webhook_user", "whatsapp.bot@yourcompany.com")