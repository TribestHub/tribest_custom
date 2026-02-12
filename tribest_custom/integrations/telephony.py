import frappe

@frappe.whitelist(allow_guest=True)
def call_event():
    frappe.set_user("Administrator")

    payload = frappe.request.get_json()
    if not payload:
        frappe.throw("JSON payload is required")

    call_id = payload.get("call_id")
    if not call_id:
        frappe.throw("call_id is required")

    # 🔍 Check existing Call Log by ID field
    existing = frappe.db.get_value(
        "Call Log",
        {"id": call_id},
        "name"
    )

    if existing:
        call_log = frappe.get_doc("Call Log", existing)
    else:
        call_log = frappe.new_doc("Call Log")

        # ✅ REQUIRED FIELD
        call_log.id = call_id

    call_log.from_number = payload.get("from")
    call_log.to_number = payload.get("to")
    call_log.call_status = payload.get("event")
    call_log.summary = payload.get("summary")
    call_log.direction = "Inbound"
    call_log.medium = "Phone"

    call_log.save(ignore_permissions=True)

    return {
        "status": "success",
        "call_log": call_log.name,
        "call_id": call_log.id,
        "ticket": getattr(call_log, "ticket_type", None)
    }
