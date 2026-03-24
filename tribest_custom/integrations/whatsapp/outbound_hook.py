import frappe
from frappe.utils import now, get_datetime
from tribest_custom.integrations.whatsapp.outbound import send_whatsapp_message
from tribest_custom.integrations.whatsapp.settings import get_whatsapp_webhook_user


def ticket_created(doc, method):
    """
    Triggered after HD Ticket is created.
    Sends WhatsApp confirmation message via Infobip.
    """

    try:
        # Ensure this ticket came from WhatsApp
        phone_number = getattr(doc, "custom_medium_identifier", None)

        if not phone_number:
            return

        # Prevent duplicate confirmation messages
        if frappe.db.exists(
            "WhatsApp Message Log",
            {
                "phone_number": phone_number,
                "message": ["like", f"%{doc.name}%"],
                "direction": "Outbound"
            }
        ):
            return

        message = build_confirmation_message(doc)

        response = send_whatsapp_message(phone_number, message)
        
        # Extract message ID from response
        message_id = response.get("messages", [{}])[0].get("messageId", "")

        # Use dedicated webhook user
        original_user = frappe.session.user
        webhook_user = get_whatsapp_webhook_user()
        frappe.set_user(webhook_user)

        try:
            # Log outbound message to WhatsApp Message Log
            msg_log = frappe.get_doc({
                "doctype": "WhatsApp Message Log",
                "message_id": message_id,
                "phone_number": phone_number,
                "message": message,
                "direction": "Outbound",
                "ticket": doc.name
            }).insert(ignore_permissions=True)
            
            frappe.log_error(f"Created Outbound WhatsApp Message Log: {msg_log.name} for ticket {doc.name}", "WhatsApp Debug")
            
            # Commit message log
            frappe.db.commit()

            # Create Communication record for ticket timeline/portal
            comm = frappe.get_doc({
                "doctype": "Communication",
                "communication_type": "Communication",
                "communication_medium": "Chat",
                "sent_or_received": "Sent",
                "subject": f"WhatsApp to {phone_number}",
                "content": message,
                "sender_full_name": "WhatsApp Bot",
                "reference_doctype": "HD Ticket",
                "reference_name": doc.name,
                "communication_date": now(),
                "has_attachment": 0
            }).insert(ignore_permissions=True)
            
            frappe.log_error(f"Created Outbound Communication: {comm.name} for ticket {doc.name}", "WhatsApp Debug")
            
            # Commit communication
            frappe.db.commit()
            
            # Reload ticket and notify
            ticket = frappe.get_doc("HD Ticket", doc.name)
            ticket.notify_update()

        finally:
            frappe.set_user(original_user)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Outbound Hook Error")


def build_confirmation_message(doc):
    """
    Construct confirmation message.
    Keep it short (WhatsApp best practice).
    """

    return (
        f"Your ticket has been created.\n\n"
        f"Ticket ID: {doc.name}\n"
        f"Category: {doc.ticket_type}\n\n"
        f"Our team will contact you shortly."
    )