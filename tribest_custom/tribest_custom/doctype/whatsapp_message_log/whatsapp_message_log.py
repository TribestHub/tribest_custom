# Copyright (c) 2026, Tribest Technologies
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WhatsAppMessageLog(Document):
	"""
	Log for all WhatsApp messages sent and received via Infobip integration.
	Used for audit trail and debugging.
	"""
	pass
