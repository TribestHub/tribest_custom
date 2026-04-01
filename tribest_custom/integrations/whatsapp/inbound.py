import frappe
from frappe.utils import now, get_datetime
from datetime import datetime, timedelta
from tribest_custom.integrations.whatsapp.ai_classifier import classify_ticket_type
from tribest_custom.integrations.whatsapp.settings import get_whatsapp_webhook_user
from html.parser import HTMLParser


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_html_tags(html_text):
    if not html_text:
        return html_text
    stripper = MLStripper()
    stripper.feed(html_text)
    return stripper.get_data().strip()


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

            # Strip HTML tags
            text_body = strip_html_tags(text_body)

            # Prevent duplicate processing
            if frappe.db.exists("WhatsApp Message Log", {"message_id": message_id}):
                continue

            original_user = frappe.session.user or "Administrator"
            webhook_user = get_whatsapp_webhook_user()

            if not webhook_user:
                frappe.log_error(
                    "whatsapp_webhook_user not configured in Tribest Custom Setting",
                    "WhatsApp Inbound Config Error"
                )
                return

            frappe.set_user(webhook_user)

            try:
                is_new_ticket = False

                # Find existing active ticket for this phone number
                ticket_name = frappe.db.get_value(
                    "HD Ticket",
                    {"custom_medium_identifier": phone_number, "status": ["!=", "Closed"]},
                    "name",
                    order_by="creation desc"
                )

                # If no active ticket, check for recently closed one
                if not ticket_name:
                    ticket_name = frappe.db.get_value(
                        "HD Ticket",
                        {"custom_medium_identifier": phone_number, "status": "Closed"},
                        "name",
                        order_by="modified desc"
                    )

                if ticket_name:
                    ticket = frappe.get_doc("HD Ticket", ticket_name)

                    if ticket.status == "Closed":
                        ticket_modified = get_datetime(ticket.modified)
                        current_time = get_datetime(now())
                        time_diff = current_time - ticket_modified

                        if time_diff <= timedelta(hours=24):
                            frappe.db.set_value("HD Ticket", ticket_name, "status", "Open")
                            frappe.db.commit()
                            ticket = frappe.get_doc("HD Ticket", ticket_name)
                        else:
                            # Closed more than 24 hours ago — create new ticket
                            ticket_name = None

                if not ticket_name:
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
                    is_new_ticket = True
                else:
                    is_new_ticket = False

                # Save WhatsApp Message Log
                frappe.get_doc({
                    "doctype": "WhatsApp Message Log",
                    "message_id": message_id,
                    "phone_number": phone_number,
                    "message": text_body,
                    "direction": "Inbound",
                    "ticket": ticket.name
                }).insert(ignore_permissions=True)

                frappe.db.commit()

                # Only manually create Communication for existing tickets
                # For new tickets, Helpdesk auto-creates it via after_insert
                if not is_new_ticket:
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
                        frappe.db.commit()

                    except Exception as e:
                        frappe.log_error(
                            f"Error creating Communication: {str(e)}\n{frappe.get_traceback()}",
                            "WhatsApp Communication Error"
                        )

                # Reload ticket to refresh timeline
                ticket = frappe.get_doc("HD Ticket", ticket.name)

                # Notify to refresh UI
                ticket.notify_update()

            finally:
                frappe.set_user(original_user)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Infobip Inbound Processing Error")