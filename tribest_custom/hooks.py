app_name = "tribest_custom"
app_title = "Tribest Custom"
app_publisher = "Tribest"
app_description = "Custom integrations and extensions for Tribest Contact Centre"
app_email = "careers@tribestsupport.com"
app_license = "mit"

doc_events = {
    "Call Log": {
        "after_insert": "tribest_custom.integrations.call_log.create_ticket"
    },
    "HD Ticket": {
        "after_insert": "tribest_custom.integrations.whatsapp.outbound_hook.ticket_created"
    },
    "Communication": {
        "after_insert": "tribest_custom.integrations.whatsapp.communication_hook.communication_after_insert"
    }
}
