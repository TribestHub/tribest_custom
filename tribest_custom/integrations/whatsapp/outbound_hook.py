import frappe
from tribest_custom.integrations.whatsapp.outbound import send_whatsapp_message

def send_reply(doc, method):
    if doc.communication_medium != "WhatsApp":
        return
    if doc.sent_or_received != "Sent":
        return

    ticket = frappe.get_doc(doc.reference_doctype, doc.reference_name)
    if not ticket.custom_whatsapp_number:
        return

    send_whatsapp_message(ticket.custom_whatsapp_number, doc.content)
