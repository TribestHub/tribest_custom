import frappe
from tribest_custom.integrations.whatsapp.outbound import send_whatsapp_message
from tribest_custom.integrations.whatsapp.settings import get_whatsapp_webhook_user


def communication_after_insert(doc, method):
    """
    Triggered after Communication record is created on HD Ticket.
    If it's an outbound message from agent, send it via WhatsApp to the customer.
    """

    try:
        # Only process Communications linked to HD Ticket
        if doc.reference_doctype != "HD Ticket":
            return

        ticket_name = doc.reference_name

        # Skip inbound messages
        if doc.sent_or_received == "Received":
            return

        # Skip if sent by the bot user (automated messages)
        webhook_user = get_whatsapp_webhook_user()
        if doc.owner == webhook_user:
            return

        # At this point it's an outbound message from a real agent — process it
        ticket = frappe.get_doc("HD Ticket", ticket_name)

        # Only process WhatsApp tickets
        if getattr(ticket, "medium", None) != "WhatsApp":
            return

        # Get customer phone number from ticket
        phone_number = getattr(ticket, "custom_medium_identifier", None)

        if not phone_number:
            frappe.log_error(
                f"Ticket {ticket_name} has no phone number (custom_medium_identifier) associated",
                "WhatsApp Outbound Hook Error"
            )
            return

        # Strip HTML from message
        message_text = doc.content
        if not message_text:
            return

        original_user = frappe.session.user or "Administrator"

        if not webhook_user:
            frappe.log_error(
                "whatsapp_webhook_user not configured in Tribest Custom Setting",
                "WhatsApp Outbound Config Error"
            )
            return

        frappe.set_user(webhook_user)

        try:
            response = send_whatsapp_message(phone_number, message_text)

            if not response:
                frappe.log_error(
                    f"No response from Infobip for Communication {doc.name}",
                    "WhatsApp Agent Reply Error"
                )
                return

            message_id = response.get("messages", [{}])[0].get("messageId", "")

            frappe.get_doc({
                "doctype": "WhatsApp Message Log",
                "message_id": message_id,
                "phone_number": phone_number,
                "message": message_text,
                "direction": "Outbound",
                "ticket": ticket_name
            }).insert(ignore_permissions=True)

            frappe.db.commit()

        except Exception:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Agent Reply Error")

        finally:
            frappe.set_user(original_user)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Communication Hook Error")