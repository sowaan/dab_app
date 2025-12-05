from datetime import date, timedelta
import calendar
import frappe

@frappe.whitelist()
def generate_monthly_invoice(contract_ids=None):
    """
    Generate monthly invoices for supplier rental contracts.
    Consolidates invoices by supplier - one invoice per supplier with multiple items.
    
    Args:
        contract_ids: List or JSON string of contract IDs to process. If None, all eligible contracts are processed.
    """
    if contract_ids:
        if isinstance(contract_ids, str):
            contract_ids = frappe.parse_json(contract_ids)
    else:
        contract_ids = []  # or fetch all if needed

    # Filter contracts by selected IDs
    filters = {
        "status": "Check In",
        "docstatus": 1
    }
    if contract_ids:
        filters["name"] = ["in", contract_ids]

    # Get all eligible contracts
    contracts = frappe.get_list(
        "Supplier Rental Contract",
        filters=filters,
        fields=["name", "check_in_date", "supplier"]
    )
    
    # Calculate date ranges
    today = date.today()
    first_day_current_month = today.replace(day=1)
    first_day_prev_month = (first_day_current_month - timedelta(days=1)).replace(day=1)
    last_day_prev_month = first_day_current_month - timedelta(days=1)
    last_month_name = calendar.month_name[first_day_prev_month.month]
    _, days_in_prev_month = calendar.monthrange(first_day_prev_month.year, first_day_prev_month.month)

    # Track results
    previous_month = []
    before_previous_month = []
    skipped_contracts = []
    skipped_missing_fields = []
    errors = []
    
    # Dictionary to group contract items by supplier
    supplier_items = {}
    
    frappe.msgprint(f"Processing {len(contracts)} contracts for {last_month_name}")

    # Process each contract
    for contract in contracts:
        try:
            check_in = contract.check_in_date
            doc = frappe.get_doc("Supplier Rental Contract", contract.name)
            
            # Check if an invoice for this contract in the previous month already exists
            already_invoiced = False
            if doc.invoicing_history:
                for history in doc.invoicing_history:
                    if history.invoice_month == last_month_name and history.status == "Invoiced":
                        already_invoiced = True
                        skipped_contracts.append(contract.name)
                        break
            
            if already_invoiced:
                continue  # Skip this contract as it's already invoiced for previous month

            # Check if check-in date is before the first day of current month
            if check_in >= first_day_current_month:
                # Contract checked in during current month - skip
                continue
            
            # Ensure required fields exist
            if not doc.supplier or not doc.rate or not doc.item or not doc.vehicle:
                skipped_missing_fields.append({
                    "contract": contract.name, 
                    "missing": [f for f in ["supplier", "rate", "item", "vehicle"] 
                                if not doc.get(f)]
                })
                continue

            # Calculate invoice details based on check-in date
            if first_day_prev_month <= check_in <= last_day_prev_month:
                # Contract started within previous month
                previous_month.append(contract.name)
                
                # Calculate days from check-in to end of previous month
                current_invoice_days = (last_day_prev_month - check_in).days + 1  # +1 to include the last day
            else:
                # Contract started before previous month
                before_previous_month.append(contract.name)
                current_invoice_days = days_in_prev_month
            
            # Update contract fields
            frappe.db.set_value("Supplier Rental Contract", contract.name, "days", current_invoice_days)
            current_invoiced_days = doc.get("invoiced_days") or 0
            new_invoiced_days = current_invoiced_days + current_invoice_days
            frappe.db.set_value("Supplier Rental Contract", contract.name, "invoiced_days", new_invoiced_days)
            
            # Reload doc to get updated values
            doc.reload()

            # Calculate per-day rate
            rate_per_day = doc.rate / days_in_prev_month
            
            # Create an item dict for this contract
            item_dict = {
                "item_code": doc.item,
                "qty": current_invoice_days,
                "rate": rate_per_day,
                "custom_vehicle": doc.vehicle,
                "custom_id": doc.name,
                "contract": contract.name,  # Store contract name for later updating
            }
            
            # Add to supplier_items dictionary
            if doc.supplier not in supplier_items:
                supplier_items[doc.supplier] = []
            supplier_items[doc.supplier].append(item_dict)

        except Exception as e:
            error_msg = f"Error processing contract {contract.name}: {str(e)}"
            frappe.log_error(error_msg, "Invoice Generation Error")
            errors.append({"contract": contract.name, "error": str(e)})

    # Create one invoice per supplier with all their items
    created_invoices = []
    
    for supplier, items in supplier_items.items():
        try:
            # Create a new Purchase Invoice
            pi = frappe.new_doc("Purchase Invoice")
            pi.supplier = supplier
            
            # Keep track of contracts for this invoice
            invoice_contracts = []
            
            # Add all items to this invoice
            for item in items:
                contract_name = item.pop("contract")  # Remove contract field before adding to invoice
                pi.append("items", item)
                invoice_contracts.append(contract_name)
            
            # Save the invoice
            pi.insert(ignore_permissions=True)
            created_invoices.append(pi.name)

            frappe.msgprint(f"Purchase Invoice Created {pi.name}")
            
            # Now that we have the invoice name, update all associated contracts
            for contract_name in invoice_contracts:
                frappe.msgprint(f"contract_name {contract_name}")
                try:
                    doc = frappe.get_doc("Supplier Rental Contract", contract_name)
                    doc.append("invoicing_history", {
                        "invoice_month": last_month_name,
                        "status": "Invoiced",
                        "purchase_invoice": pi.name
                    })
                    doc.save(ignore_permissions=True)
                except Exception as e:
                    error_msg = f"Error updating contract {contract_name} with invoice {pi.name}: {str(e)}"
                    frappe.log_error(error_msg, "Contract Update Error")
                    errors.append({"contract": contract_name, "error": str(e)})
                
        except Exception as e:
            error_msg = f"Error creating invoice for supplier {supplier}: {str(e)}"
            frappe.log_error(error_msg, "Supplier Invoice Creation Error")
            errors.append({"supplier": supplier, "error": str(e)})

    # Final message with detailed statistics
    total_contracts_processed = len(previous_month) + len(before_previous_month)
    
    msg = f"Monthly Invoice Generation Summary for {last_month_name}:\n"
    msg += f"Total Eligible Contracts: {len(contracts)}\n"
    msg += f"Contracts Processed: {total_contracts_processed}\n"
    msg += f"Contracts from Previous Month: {len(previous_month)}\n"
    msg += f"Contracts from Earlier Months: {len(before_previous_month)}\n"
    msg += f"Skipped (Already Invoiced): {len(skipped_contracts)}\n"
    msg += f"Skipped (Missing Required Fields): {len(skipped_missing_fields)}\n"
    msg += f"Failed with Errors: {len(errors)}\n"
    msg += f"Purchase Invoices Successfully Created: {len(created_invoices)}\n"
    
    if skipped_missing_fields:
        msg += "\nContracts skipped due to missing fields:\n"
        for item in skipped_missing_fields:
            msg += f"- {item['contract']}: Missing {', '.join(item['missing'])}\n"
    
    if errors:
        msg += "\nErrors encountered:\n"
        for item in errors:
            if "contract" in item:
                msg += f"- Contract {item['contract']}: {item['error']}\n"
            else:
                msg += f"- Supplier {item['supplier']}: {item['error']}\n"
    
    if created_invoices:
        msg += "\nInvoices Created:\n"
        for inv in created_invoices:
            msg += f"- {inv}\n"

    frappe.msgprint(msg)
    return created_invoices


def remove_invoicing_history_on_invoice_delete(doc, method):
    for item in doc.items:
        contract_id = item.get("custom_id")
        if not contract_id:
            continue
        
        try:
            contract_doc = frappe.get_doc("Supplier Rental Contract", contract_id)
            new_history = []

            for history in contract_doc.invoicing_history:
                if history.purchase_invoice != doc.name:
                    new_history.append(history)

            # Clear and repopulate invoicing_history
            contract_doc.set("invoicing_history", new_history)
            contract_doc.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to update invoicing history for contract {contract_id}: {e}")