import frappe
from frappe.utils import now


def ticket_created(doc, method):
    """
    Triggered after HD Ticket is created.
    Enqueues WhatsApp confirmation to avoid session corruption.
    """
    try:
        phone_number = getattr(doc, "custom_medium_identifier", None)
        if not phone_number:
            return

        frappe.enqueue(
            "tribest_custom.integrations.whatsapp.outbound_hook.send_ticket_confirmation",
            queue="short",
            timeout=300,
            ticket_name=doc.name,
            phone_number=phone_number
        )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "WhatsApp Outbound Hook Error"
        )


def send_ticket_confirmation(ticket_name, phone_number):
    """Runs in background worker — safe to use set_user here"""
    try:
        from tribest_custom.integrations.whatsapp.outbound import send_whatsapp_message
        from tribest_custom.integrations.whatsapp.settings import get_whatsapp_webhook_user

        webhook_user = get_whatsapp_webhook_user()
        if not webhook_user:
            frappe.log_error(
                "whatsapp_webhook_user not configured in Tribest Custom Setting",
                "WhatsApp Outbound Config Error"
            )
            return

        # Prevent duplicate confirmation messages
        if frappe.db.exists(
            "WhatsApp Message Log",
            {
                "phone_number": phone_number,
                "message": ["like", f"%{ticket_name}%"],
                "direction": "Outbound"
            }
        ):
            return

        original_user = frappe.session.user or "Administrator"
        frappe.set_user(webhook_user)

        try:
            ticket = frappe.get_doc("HD Ticket", ticket_name)
            message = build_confirmation_message(ticket)
            response = send_whatsapp_message(phone_number, message)

            if not response:
                frappe.log_error(
                    f"No response from Infobip for ticket {ticket_name}",
                    "WhatsApp Outbound Error"
                )
                return

            message_id = response.get("messages", [{}])[0].get("messageId", "")

            frappe.get_doc({
                "doctype": "WhatsApp Message Log",
                "message_id": message_id,
                "phone_number": phone_number,
                "message": message,
                "direction": "Outbound",
                "ticket": ticket_name
            }).insert(ignore_permissions=True)

            frappe.db.commit()

            comm = frappe.get_doc({
                "doctype": "Communication",
                "communication_type": "Communication",
                "communication_medium": "Chat",
                "sent_or_received": "Sent",
                "subject": f"WhatsApp to {phone_number}",
                "content": message,
                "sender_full_name": "WhatsApp Bot",
                "reference_doctype": "HD Ticket",
                "reference_name": ticket_name,
                "communication_date": now(),
                "has_attachment": 0
            })
            comm.flags.ignore_validate = True
            comm.flags.ignore_mandatory = True
            comm.insert(ignore_permissions=True)

            frappe.db.commit()

            ticket = frappe.get_doc("HD Ticket", ticket_name)
            ticket.notify_update()

        finally:
            frappe.set_user(original_user)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "WhatsApp Outbound Hook Error"
        )


def build_confirmation_message(doc):
    return (
        f"Your ticket has been created.\n\n"
        f"Ticket ID: {doc.name}\n"
        f"Category: {doc.ticket_type}\n\n"
        f"Our team will contact you shortly."
    )