import frappe   # 🔴 REQUIRED

def create_ticket(doc, method=None):
    summary = (doc.summary or "").lower()

    if "job" in summary or "application" in summary:
        ticket_type = "Applicant Inquiry"
    elif "complaint" in summary:
        ticket_type = "Complaint"
    elif "interview" in summary or "candidate" in summary:
        ticket_type = "Candidate Inquiry"
    else:
        ticket_type = "Client Management"

    ticket = frappe.new_doc("HD Ticket")
    ticket.subject = f"Incoming Call from {doc.from_number}"
    ticket.description = doc.summary
    ticket.ticket_type = ticket_type
    ticket.medium = "Phone"
    ticket.status = "Open"

    ticket.flags.ignore_permissions = True
    ticket.insert()

    ticket.db_set("ticket_type", ticket_type, update_modified=False)
