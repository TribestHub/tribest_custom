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
        # Ensure existing user has correct roles
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


def create_hd_ticket_custom_fields():
    """Create custom fields on HD Ticket if they don't exist"""

    fields = [
        {
            "dt": "HD Ticket",
            "fieldname": "medium",
            "fieldtype": "Select",
            "label": "Medium",
            "options": "Email\nWhatsApp\nChat\nPhone\nOther",
            "insert_after": "status",
            "in_list_view": 1,
            "in_standard_filter": 1,
            "search_index": 1,
            "description": "Medium through which ticket was created"
        },
        {
            "dt": "HD Ticket",
            "fieldname": "custom_medium_identifier",
            "fieldtype": "Data",
            "label": "Custom Medium Identifier",
            "insert_after": "medium",
            "in_list_view": 1,
            "in_standard_filter": 1,
            "search_index": 1,
            "description": "WhatsApp phone number or custom medium identifier"
        }
    ]

    for field in fields:
        # Check if field already exists in meta (helpdesk source code)
        meta = frappe.get_meta("HD Ticket")
        existing = [df for df in meta.get("fields") if df.fieldname == field["fieldname"]]
        if existing:
            continue

        # Check if Custom Field record already exists
        if frappe.db.exists("Custom Field", f"HD Ticket-{field['fieldname']}"):
            continue

        # Create Custom Field
        frappe.get_doc({
            "doctype": "Custom Field",
            **field
        }).insert(ignore_permissions=True)
        frappe.log_error(
            f"Created Custom Field: {field['fieldname']} on HD Ticket",
            "WhatsApp Setup"
        )

    frappe.db.commit()


def after_migrate():
    create_whatsapp_bot_user()
    create_hd_ticket_custom_fields()