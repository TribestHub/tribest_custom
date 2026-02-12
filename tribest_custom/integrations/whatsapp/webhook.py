import frappe
from werkzeug.wrappers import Response

@frappe.whitelist(allow_guest=True)
def whatsapp_webhook():

    # -------------------------
    # META VERIFICATION (GET)
    # -------------------------
    if frappe.request.method == "GET":
        mode = frappe.request.args.get("hub.mode")
        verify_token = frappe.request.args.get("hub.verify_token")
        challenge = frappe.request.args.get("hub.challenge")

        expected_token = frappe.conf.get("whatsapp_verify_token")

        if mode == "subscribe" and verify_token == expected_token:
            return Response(
                challenge,
                status=200,
                content_type="text/plain"
            )

        return Response(
            "Invalid verification token",
            status=403,
            content_type="text/plain"
        )

    
    # ==================================================
    # WHATSAPP MESSAGE RECEIVED (POST)
    # ==================================================
       # -------------------------
    # INCOMING MESSAGES (POST)
    # -------------------------
    if frappe.request.method == "POST":
        frappe.log_error("WEBHOOK HIT", "WhatsApp Debug")

        data = frappe.request.get_json()

        try:
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages")

            if not messages:
                return Response("EVENT_RECEIVED", status=200, content_type="text/plain")

            message = messages[0]
            message_id = message.get("id")
            sender = message.get("from")
            text_body = message.get("text", {}).get("body", "")

            # -------------------------
            # Idempotency Protection
            # -------------------------
            if frappe.db.exists("WhatsApp Message Log", {"message_id": message_id}):
                return Response("EVENT_RECEIVED", status=200, content_type="text/plain")

            # Save message log
            frappe.get_doc({
                "doctype": "WhatsApp Message Log",
                "message_id": message_id,
                "phone_number": sender,
                "message": text_body
            }).insert(ignore_permissions=True)

            # -------------------------
            # Check Existing Open Ticket
            # -------------------------
            # -------------------------
            # Create / Update Ticket as System User
            # -------------------------

            original_user = frappe.session.user
            frappe.set_user("Administrator")

            try:
                existing_ticket = frappe.db.get_value(
                    "HD Ticket",
                    {
                        "custom_medium_identifier": sender,
                        "status": ["not in", ["Closed", "Resolved"]]
                    },
                    "name"
                )

                if existing_ticket:
                    frappe.get_doc({
                        "doctype": "Comment",
                        "comment_type": "Comment",
                        "reference_doctype": "HD Ticket",
                        "reference_name": existing_ticket,
                        "content": f"WhatsApp message from {sender}:<br><br>{text_body}"
                    }).insert(ignore_permissions=True)

                else:
                    existing_ticket = frappe.get_doc({
                        "doctype": "HD Ticket",
                        "subject": f"WhatsApp Message from {sender}",
                        "custom_medium_identifier": sender,
                        "description": text_body,
                        "status": "Open",
                        "priority": "Medium",
                        "ticket_type": "Complaint"
                    }).insert(ignore_permissions=True).name

                frappe.db.commit()

            finally:
                frappe.set_user(original_user)


        except Exception:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Webhook Error")
            raise

        return Response("EVENT_RECEIVED", status=200, content_type="text/plain")
