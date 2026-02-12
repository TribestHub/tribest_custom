import frappe

def process_inbound_message(payload):
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return

        message = messages[0]
        from_number = message.get("from")
        message_text = message.get("text", {}).get("body")

        frappe.log_error(
            title="WhatsApp Inbound Message",
            message=f"From: {from_number}\nMessage: {message_text}"
        )

        # NEXT STEP:
        # create HD Ticket or route to Helpdesk

    except Exception:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Inbound Error")
