# Copyright (c) 2026, Tribest Technologies
# For license information, please see license.txt

import unittest
import frappe


class TestWhatsAppMessageLog(unittest.TestCase):
	"""
	Unit tests for WhatsApp Message Log doctype
	"""
	
	def setUp(self):
		"""Setup test data"""
		pass
	
	def tearDown(self):
		"""Cleanup test data"""
		pass
	
	def test_create_message_log(self):
		"""Test creating a message log entry"""
		# Example test
		msg_log = frappe.get_doc({
			"doctype": "WhatsApp Message Log",
			"message_id": "test_msg_123",
			"phone_number": "+1234567890",
			"message": "Test message",
			"direction": "Inbound",
			"status": "Sent"
		})
		msg_log.insert(ignore_permissions=True)
		
		# Verify creation
		self.assertEqual(msg_log.message_id, "test_msg_123")
		self.assertEqual(msg_log.direction, "Inbound")
