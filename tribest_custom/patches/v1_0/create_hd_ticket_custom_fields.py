# import frappe

# def execute():
#    fields = [
#        {
#            "dt": "HD Ticket",
#            "fieldname": "custom_medium",
#            "fieldtype": "Select",
#            "label": "Medium",
#            "options": "Email\nWhatsApp\nChat\nPhone\nOther",
#            "insert_after": "status",
#            "in_list_view": 1,
#            "in_standard_filter": 1,
#            "search_index": 1,
#            "description": "Medium through which ticket was created"
#        },
#        {
#            "dt": "HD Ticket",
#            "fieldname": "custom_medium_identifier",
#            "fieldtype": "Data",
#            "label": "Medium Identifier",
#            "insert_after": "custom_medium",
#            "in_list_view": 1,
#            "in_standard_filter": 1,
#            "search_index": 1,
#            "description": "WhatsApp phone number or custom medium identifier"
#        }
#    ]
#
#    for field in fields:
#        if frappe.db.exists("Custom Field", f"HD Ticket-{field['fieldname']}"):
#            frappe.log_error(
#                f"Field already exists: HD Ticket-{field['fieldname']}",
#                "HD Ticket Patch"
#            )
#            continue
#
#        try:
#            frappe.get_doc({
#                "doctype": "Custom Field",
#                **field
#            }).insert(ignore_permissions=True)
#            frappe.log_error(
#                f"Successfully created: HD Ticket-{field['fieldname']}",
#                "HD Ticket Patch"
#            )
#        except Exception as e:
#            frappe.log_error(
#                f"Failed to create {field['fieldname']}: {str(e)}\n{frappe.get_traceback()}",
#                "HD Ticket Patch Error"
#            )
#
#    frappe.db.commit()
#
