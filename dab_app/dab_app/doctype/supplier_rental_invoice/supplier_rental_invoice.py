import frappe
from frappe.model.document import Document
from frappe.utils import getdate, flt, get_last_day, get_first_day, date_diff
from datetime import datetime
import calendar
import json

class SupplierRentalInvoice(Document):
    def before_save(self):

        doc = self

        # --- Basic Validation ---
        if not doc.from_date or not doc.to_date:
            frappe.throw("Please select both <b>From Date</b> and <b>To Date</b>.")

        if getdate(doc.from_date) > getdate(doc.to_date):
            frappe.throw("<b>From Date</b> cannot be later than <b>To Date</b>.")

        frappe.logger().info(f"[Supplier Rental Invoice] Calculating invoice for {doc.supplier} between {doc.from_date} → {doc.to_date}")

        existing_ids = {d.id for d in doc.supplier_rental_invoice_table}
        skipped_contracts = []

        invoice_month_start = getdate(doc.from_date)
        invoice_month_end = getdate(doc.to_date)

        # --- Fetch eligible contracts ---
        filters = {"supplier": doc.supplier, "docstatus": 1}

        if doc.vehicle: filters["vehicle"] = doc.vehicle
        if doc.status: filters["status"] = doc.status

        contracts = frappe.get_all(
            "Supplier Rental Contract",
            filters=filters,
            fields=["name", "vehicle", "check_in_date", "check_out_date", "rate",
                    "purchase_order", "status"]
        )

        frappe.logger().info(f"Found {len(contracts)} contract(s) for billing.")

        for c in contracts:

            check_in_date = getdate(c.check_in_date)
            check_out_date = getdate(c.check_out_date) if c.check_out_date else None
            actual_end = check_out_date or invoice_month_end

            #frappe.msgprint(f"check_in_date {check_in_date} check_out_date {check_out_date} actual_end {actual_end}")

            # Skip if contract does not overlap
            if not (check_in_date <= invoice_month_end and actual_end >= invoice_month_start):
                frappe.logger().info(f"Skipping contract {c.name} (outside period).")
                continue

            # --- Prevent duplicate entries across invoices ---
            existing_invoice = frappe.db.sql("""
                SELECT sri.parent
                FROM `tabSupplier Rental Invoice Table` sri
                JOIN `tabSupplier Rental Invoice` si ON sri.parent = si.name
                WHERE sri.id = %s
                AND si.name != %s
                AND MONTH(si.from_date) = MONTH(%s)
                AND YEAR(si.from_date) = YEAR(%s)
            """, (c.name, doc.name, doc.from_date, doc.from_date), as_dict=1)

            if existing_invoice:
                skipped_contracts.append(f"{c.name} (already invoiced: {existing_invoice[0].parent})")
                frappe.logger().warning(f"Contract {c.name} skipped (already billed).")
                continue

            # --- Prevent duplication inside same document ---
            if c.name in existing_ids:
                frappe.logger().warning(f"Contract {c.name} skipped (already on document).")
                continue

            # --- Billable period ---
            bill_start = max(check_in_date, invoice_month_start)
            bill_end = min(actual_end, invoice_month_end)
            
            number_of_days = (bill_end - bill_start).days + 1

            #frappe.msgprint(f"bill_start {bill_start} bill_end {bill_end} number_of_days {number_of_days}")

            if number_of_days < 0:
                frappe.logger().error(f"Contract {c.name}: Negative billing days detected ({number_of_days}). Fixing to 0.")
                number_of_days = 0

            # --- Pricing calculation ---
            days_in_month = calendar.monthrange(invoice_month_start.year, invoice_month_start.month)[1]
            daily_rate = flt(c.rate / days_in_month, 2)
            amount = flt(number_of_days * daily_rate, 2)

            # --- Append invoice row ---
            doc.append("supplier_rental_invoice_table", {
                "id": c.name,
                "item": doc.item,
                "vehicle": c.vehicle,
                "purchase_order": c.purchase_order,
                "number_of_days": number_of_days,
                "rate": daily_rate,
                "status": c.status,
                "check_in_date": check_in_date,
                "check_out_date": actual_end,
                "amount": amount
            })

            frappe.logger().info(f"Added: {c.name} → {number_of_days} days @ {daily_rate} = {amount}")

        # --- Totals ---
        doc.total_days = sum(d.number_of_days for d in doc.supplier_rental_invoice_table)
        doc.total_amount = sum(d.amount for d in doc.supplier_rental_invoice_table)

        frappe.logger().info(f"Final Totals: {doc.total_days} days | {doc.total_amount} amount")

        # Notify skipped items
        if skipped_contracts:
            frappe.msgprint(
                "Some contracts were skipped because already invoiced:<br><br>" +
                "<br>".join(f"• {s}" for s in skipped_contracts)
            )




@frappe.whitelist()
def check_duplicate_contract_ids(ids):
    if not isinstance(ids, list):
        ids = frappe.parse_json(ids)

    # Check if any Supplier Rental Contract is already invoiced
    contracts = frappe.get_all(
        "Supplier Rental Contract",
        filters={"name": ["in", ids], "purchase_invoiced": 1},
        fields=["name"],
        limit=1
    )

    if contracts:
        return {
            "duplicate": True,
            "contract_id": contracts[0]["name"]
        }

    return {"duplicate": False}

@frappe.whitelist()
def add_invoicing_history(invoice_name, contract_names, invoice_month):
    
    if isinstance(contract_names, str):
        contract_names = json.loads(contract_names)

    for contract_name in contract_names:
        if not contract_name:
            continue
        try:
            contract_doc = frappe.get_doc("Supplier Rental Contract", contract_name)
            # Append new row to child table
            contract_doc.append("invoicing_history", {
                "invoice_month": invoice_month,
                "status": "Invoiced",
                "purchase_invoice": invoice_name
            })
            contract_doc.db_set("purchase_invoiced", 1)  # parent field
            contract_doc.save(ignore_permissions=True)   # saves child table automatically
        except Exception as e:
            frappe.log_error(title=f"Error updating contract {contract_name}", message=str(e))

@frappe.whitelist()
def check_invoice_exists(contract_names, invoice_month):
    import json

    if isinstance(contract_names, str):
        contract_names = json.loads(contract_names)

    duplicate_contracts = []

    for contract_name in contract_names:
        contract_doc = frappe.get_doc("Supplier Rental Contract", contract_name)
        for row in contract_doc.invoicing_history:
            if row.invoice_month == invoice_month:
                duplicate_contracts.append(contract_name)
                break
    
    #frappe.msgprint(f"exists {len(duplicate_contracts)}")

    return {"exists": len(duplicate_contracts) > 0, "contracts": duplicate_contracts}

    
  



