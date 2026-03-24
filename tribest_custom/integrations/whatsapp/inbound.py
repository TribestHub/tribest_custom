import frappe
from frappe.utils import now, get_datetime
from datetime import datetime, timedelta
from tribest_custom.integrations.whatsapp.ai_classifier import classify_ticket_type
from tribest_custom.integrations.whatsapp.settings import get_whatsapp_webhook_user


def process_inbound(data: dict):

    try:
        results = data.get("results", [])
        if not results:
            return

        for item in results:

            phone_number = item.get("sender")
            message_id = item.get("messageId")

            content_list = item.get("content", [])
            if not content_list:
                continue

            content = content_list[0]

            if content.get("type") != "TEXT":
                continue

            text_body = content.get("text")

            if isinstance(text_body, dict):
                text_body = text_body.get("body")

            if not text_body:
                continue

            # Prevent duplicate processing
            if frappe.db.exists("WhatsApp Message Log", {"message_id": message_id}):
                continue

            original_user = frappe.session.user
            webhook_user = get_whatsapp_webhook_user()
            frappe.set_user(webhook_user)

            try:

                # Find existing ticket for this phone number (most recent)
                ticket_name = frappe.db.get_value(
                    "HD Ticket",
                    {"custom_medium_identifier": phone_number},
                    "name",
                    order_by="creation desc"
                )

                if ticket_name:
                    ticket = frappe.get_doc("HD Ticket", ticket_name)
                    
                    # Reopen ticket if it was closed within 24 hours
                    if ticket.status == "Closed":
                        ticket_modified = get_datetime(ticket.modified)
                        current_time = get_datetime(now())
                        time_diff = current_time - ticket_modified
                        if time_diff <= timedelta(hours=24):
                            # Use db_set to directly update status in DB, bypassing all validation
                            frappe.db.set_value("HD Ticket", ticket_name,  "status", "ReOpen")
                            frappe.db.commit()
                            # Reload ticket with fresh state
                            ticket = frappe.get_doc("HD Ticket", ticket_name)
                else:
                    # Classify ticket type for new tickets
                    ticket_type = classify_ticket_type(text_body)

                    ticket = frappe.get_doc({
                        "doctype": "HD Ticket",
                        "subject": f"WhatsApp from {phone_number}",
                        "description": text_body,
                        "custom_medium_identifier": phone_number,
                        "medium": "WhatsApp",
                        "ticket_type": ticket_type,
                        "status": "Open"
                    }).insert(ignore_permissions=True)

                # Save WhatsApp Message Log
                msg_log = frappe.get_doc({
                    "doctype": "WhatsApp Message Log",
                    "message_id": message_id,
                    "phone_number": phone_number,
                    "message": text_body,
                    "direction": "Inbound",
                    "ticket": ticket.name
                }).insert(ignore_permissions=True)
                
                frappe.log_error(f"Created WhatsApp Message Log: {msg_log.name} for ticket {ticket.name}", "WhatsApp Debug")

                # Commit message log first
                frappe.db.commit()

                # Create Communication record (this appears in timeline)
                try:
                    comm = frappe.get_doc({
                        "doctype": "Communication",
                        "communication_type": "Communication",
                        "communication_medium": "Chat",
                        "sent_or_received": "Received",
                        "subject": f"WhatsApp from {phone_number}",
                        "content": text_body,
                        "sender_full_name": f"WhatsApp: {phone_number}",
                        "reference_doctype": "HD Ticket",
                        "reference_name": ticket.name,
                        "communication_date": now(),
                        "has_attachment": 0
                    })
                    comm.insert(ignore_permissions=True)
                    
                    frappe.log_error(f"Created Communication: {comm.name} for ticket {ticket.name}", "WhatsApp Debug")
                    
                    # Commit communication
                    frappe.db.commit()
                except Exception as e:
                    frappe.log_error(f"Error creating Communication: {str(e)}\n{frappe.get_traceback()}", "WhatsApp Communication Error")
                
                # Reload ticket to refresh timeline
                ticket = frappe.get_doc("HD Ticket", ticket.name)
                
                # Notify to refresh UI
                ticket.notify_update()

            finally:
                frappe.set_user(original_user)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Infobip Inbound Processing Error")