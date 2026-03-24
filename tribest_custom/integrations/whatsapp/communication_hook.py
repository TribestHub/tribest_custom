import frappe
from frappe.utils import now
from tribest_custom.integrations.whatsapp.outbound import send_whatsapp_message
from tribest_custom.integrations.whatsapp.settings import get_whatsapp_webhook_user


def communication_after_insert(doc, method):
    """
    Triggered after Communication record is created on HD Ticket.
    If it's a new message from agent, send it via WhatsApp to the customer.
    """

    try:
        # Only process Communications linked to HD Ticket
        if doc.reference_doctype != "HD Ticket":
            frappe.log_error(
                f"Skipping Communication {doc.name}: not linked to HD Ticket (linked to {doc.reference_doctype})",
                "WhatsApp Communication Hook Debug"
            )
            return

        ticket_name = doc.reference_name
        
        frappe.log_error(
            f"Processing Communication {doc.name} for ticket {ticket_name}: "
            f"sent_or_received={doc.sent_or_received}, medium={doc.communication_medium}, owner={doc.owner}",
            "WhatsApp Communication Hook Debug"
        )

        # Skip inbound messages (already received from WhatsApp)
        if doc.sent_or_received == "Received":
            frappe.log_error(
                f"Skipping Communication {doc.name}: inbound message",
                "WhatsApp Communication Hook Debug"
            )
            return

        # For Chat medium (internal system messages), only process if not from bot
        webhook_user = get_whatsapp_webhook_user()
        if doc.communication_medium == "Chat" and doc.owner != webhook_user:
            # This is an agent reply via Chat, send it
            pass
        elif doc.communication_medium != "Chat":
            # Email or other medium from agent
            pass
        else:
            # Skip if it's from the bot (internal)
            frappe.log_error(
                f"Skipping Communication {doc.name}: from WhatsApp bot",
                "WhatsApp Communication Hook Debug"
            )
            return

        ticket = frappe.get_doc("HD Ticket", ticket_name)

        # Get customer phone number from ticket
        phone_number = getattr(ticket, "custom_medium_identifier", None)

        if not phone_number:
            frappe.log_error(
                f"Ticket {ticket_name} has no phone number (custom_medium_identifier) associated",
                "WhatsApp Outbound Hook Error"
            )
            return

        message_text = doc.content
        
        frappe.log_error(
            f"Agent reply - phone: {phone_number}, msg_len: {len(message_text) if message_text else 0}",
            "WhatsApp Agent Reply Debug"
        )

        # Use dedicated webhook user
        original_user = frappe.session.user
        frappe.set_user(webhook_user)

        try:
            frappe.log_error(
                f"Sending agent reply via WhatsApp to {phone_number}",
                "WhatsApp Agent Reply Debug"
            )
            
            # Send message to customer via WhatsApp
            response = send_whatsapp_message(phone_number, message_text)

            if not response:
                frappe.log_error(
                    f"No response from Infobip for Communication {doc.name}",
                    "WhatsApp Agent Reply Error"
                )
                return

            # Extract message ID from response
            message_id = response.get("messages", [{}])[0].get("messageId", "")

            # Log outbound message to WhatsApp Message Log
            msg_log = frappe.get_doc({
                "doctype": "WhatsApp Message Log",
                "message_id": message_id,
                "phone_number": phone_number,
                "message": message_text,
                "direction": "Outbound",
                "ticket": ticket_name
            }).insert(ignore_permissions=True)

            frappe.log_error(
                f"Agent reply sent via WhatsApp: {msg_log.name} to {phone_number}",
                "WhatsApp Agent Reply Success"
            )

            frappe.db.commit()

        except Exception as e:
            frappe.log_error(
                f"Failed to send agent reply via WhatsApp: {str(e)}\n{frappe.get_traceback()}",
                "WhatsApp Agent Reply Error"
            )

        finally:
            frappe.set_user(original_user)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Communication Hook Error")
