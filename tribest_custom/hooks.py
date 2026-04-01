app_name = "tribest_custom"
app_title = "Tribest Custom"
app_publisher = "Tribest"
app_description = "Custom integrations and extensions for Tribest Contact Centre"
app_email = "erptest@mg.tribestsuport.com"
app_license = "mit"

required_apps = ["frappe", "helpdesk"]

doc_events = {
    "Call Log": {
        "after_insert": "tribest_custom.integrations.call_log.create_ticket"
    },
    "HD Ticket": {
        "after_insert": "tribest_custom.integrations.whatsapp.outbound_hook.ticket_created"
    },
    "Communication": {
        "after_insert": "tribest_custom.integrations.whatsapp.communication_hook.communication_after_insert"
    },
    "Tribest Custom Setting": {
        "on_update": "tribest_custom.setup.create_whatsapp_bot_user"
    }
}

after_migrate = [
    "tribest_custom.setup.after_migrate"
]