# Copyright (c) 2025, Sowaan Pvt. Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class SupplierRentalInvoice(Document):
	def before_save(self):
		doc = self
		existing_ids = {d.id for d in doc.supplier_rental_invoice_table}

		# First add any new contracts that aren't already in the table
		filters = {
			"supplier": doc.supplier,
			"contract_status": "Closed"
		}

		if doc.vehicle:
			filters["vehicle"] = doc.vehicle

		contracts = frappe.get_all("Supplier Rental Contract",
			filters=filters,
			fields=["name", "vehicle", "days", "rate", "check_out_date"]
		)

		for c in contracts:
			check_out = getdate(c.check_out_date)
			if getdate(doc.from_date) <= check_out <= getdate(doc.to_date):
				if c.name in existing_ids:
					continue  # Skip if already exists

				amount = c.rate * c.days

				doc.append("supplier_rental_invoice_table", {
					"id": c.name,
					"item": doc.item,
					"vehicle": c.vehicle,
					"number_of_days": c.days,
					"rate": c.rate,
					"amount": amount
				})

		# Now calculate totals from all rows (both existing and newly added)
		total_days = 0
		total_amount = 0
		
		for d in doc.supplier_rental_invoice_table:
			# Ensure amount is calculated based on current values
			d.amount = d.rate * d.number_of_days
			total_days += d.number_of_days
			total_amount += d.amount

		doc.total_days = total_days
		doc.total_amount = total_amount