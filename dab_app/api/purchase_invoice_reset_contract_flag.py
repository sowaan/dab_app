import frappe

@frappe.whitelist()
def purchase_invoice_reset_contract_flag(doc, method=None):
    """
    Reset `purchase_invoiced` flag and remove invoicing history
    for Supplier Rental Contracts linked in a Purchase Invoice
    when it is cancelled or deleted.
    """
    if not doc.items:
        return

    # Collect all linked contracts from invoice items
    contracts = list({item.get("supplier_rental_contract") for item in doc.items if item.get("supplier_rental_contract")})

    frappe.msgprint(f"contracts {contracts}")

    for contract_name in contracts:
        try:
            # Load the contract document
            contract_doc = frappe.get_doc("Supplier Rental Contract", contract_name)

            frappe.msgprint(f"contract_doc {contract_doc}")

            # Reset purchase_invoiced flag
            contract_doc.purchase_invoiced = 0

            # Remove invoicing history rows related to this invoice
            contract_doc.invoicing_history = [
                row for row in contract_doc.invoicing_history
                if row.purchase_invoice != doc.name
            ]

            # Save changes
            contract_doc.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(
                title=f"Error resetting purchase_invoiced for {contract_name}",
                message=str(e)
            )

