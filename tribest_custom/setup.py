import frappe


def create_whatsapp_bot_user(doc=None, method=None):
    """Create WhatsApp bot user if it doesn't exist, with correct roles"""
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
            "user_type": "System User",
            "enabled": 1,
            "send_welcome_email": 0,
            "roles": [
                {"role": "Agent"},
                {"role": "Agent Manager"},
                {"role": "System Manager"}
            ]
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    else:
        user = frappe.get_doc("User", email)
        existing_roles = [r.role for r in user.roles]
        roles_to_add = ["Agent", "Agent Manager", "System Manager"]

        updated = False
        for role in roles_to_add:
            if role not in existing_roles:
                user.append("roles", {"role": role})
                updated = True

        if updated:
            user.save(ignore_permissions=True)
            frappe.db.commit()

def debug_after_migrate():
    try:
        medium = frappe.db.exists("Custom Field", "HD Ticket-custom_medium")
        identifier = frappe.db.exists("Custom Field", "HD Ticket-custom_medium_identifier")
        
        frappe.log_error(
            f"Fixture Debug:\n"
            f"HD Ticket-custom_medium exists: {medium}\n"
            f"HD Ticket-custom_medium_identifier exists: {identifier}",
            "Fixture Debug"
        )
    except Exception as e:
        frappe.log_error(str(e), "Fixture Debug Error")