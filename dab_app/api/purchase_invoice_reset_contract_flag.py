# import frappe

# def on_purchase_invoice_cancel_or_delete(doc, method=None):
#     if not doc.items:
#         return

#     contracts = {
#         item.get("supplier_rental_contract") or item.get("custom_supplier_rental_contract")
#         for item in doc.items
#         if item.get("supplier_rental_contract") or item.get("custom_supplier_rental_contract")
#     }

#     for contract in contracts:
#         frappe.db.set_value(
#             "Supplier Rental Contract",
#             contract,
#             "purchase_invoiced",
#             0
#         )

