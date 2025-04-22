# Copyright (c) 2025, Sowaan Pvt. Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SupplierRentalContract(Document):
	def validate(self):
		# Server Script for Supplier Rental Contract - Validate
		doc = self
		if doc.vehicle:
			existing = frappe.db.exists(
				"Supplier Rental Contract",
				{
					"vehicle": doc.vehicle,
					"status": "Check In",
					"name": ["!=", doc.name]
				}
			)
			if existing:
				frappe.throw(f"Vehicle {doc.vehicle} is already in use (Checked In) in another contract.")

