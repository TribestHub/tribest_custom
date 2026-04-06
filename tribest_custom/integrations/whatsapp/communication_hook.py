import frappe


def communication_after_insert(doc, method):
    """
    Triggered after Communication record is created on HD Ticket.
    Enqueues WhatsApp send to avoid session corruption.
    """
    try:
        if doc.reference_doctype != "HD Ticket":
            return

        if doc.sent_or_received == "Received":
            return

        webhook_user = _get_webhook_user()
        if not webhook_user:
            return

        # Skip if sent by the bot user (automated messages)
        if doc.owner == webhook_user:
            return

        ticket = frappe.get_doc("HD Ticket", doc.reference_name)

        if getattr(ticket, "custom_medium", None) != "WhatsApp":
            return

        phone_number = getattr(ticket, "custom_medium_identifier", None)
        if not phone_number:
            frappe.log_error(
                f"Ticket {doc.reference_name} has no phone number (custom_medium_identifier)",
                "WhatsApp Outbound Hook Error"
            )
            return

        if not doc.content:
            return

        frappe.enqueue(
            "tribest_custom.integrations.whatsapp.communication_hook.send_whatsapp_reply",
            queue="short",
            timeout=300,
            doc_name=doc.name,
            ticket_name=doc.reference_name,
            phone_number=phone_number,
            message_text=doc.content
        )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "WhatsApp Communication Hook Error"
        )


def send_whatsapp_reply(doc_name, ticket_name, phone_number, message_text):
    """Runs in background worker — safe to call send here"""
    try:
        from tribest_custom.integrations.whatsapp.outbound import send_whatsapp_message

        response = send_whatsapp_message(phone_number, message_text)

        if not response:
            frappe.log_error(
                f"No response from Infobip for Communication {doc_name}",
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
        frappe.log_error(
            frappe.get_traceback(),
            "WhatsApp Agent Reply Error"
        )


def _get_webhook_user():
    """Helper to get webhook user with error handling"""
    from tribest_custom.integrations.whatsapp.settings import get_whatsapp_webhook_user
    webhook_user = get_whatsapp_webhook_user()
    if not webhook_user:
        frappe.log_error(
            "whatsapp_webhook_user not configured in Tribest Custom Setting",
            "WhatsApp Outbound Config Error"
        )
    return webhook_user