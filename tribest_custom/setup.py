import frappe

def create_whatsapp_bot_user(doc=None, method=None):
    email = frappe.db.get_value(
        "Tribest Custom Setting",
        "Tribest Custom Setting",
        "whatsapp_webhook_user"
    )

    if not email:
        frappe.log_error(
            "whatsapp_webhook_user not set in Tribest Custom Setting",
            "WhatsApp Setup Error"
        )
        return

    if not frappe.db.exists("User", email):
        frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "WhatsApp Bot",
            "user_type": "Website User",
            "enabled": 1,
            "send_welcome_email": 0
        }).insert(ignore_permissions=True)
        frappe.db.commit()