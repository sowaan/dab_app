import frappe
from frappe.model.document import Document
from frappe.utils import getdate, flt, get_last_day, get_first_day, date_diff
from datetime import datetime
import calendar

class SupplierRentalInvoice(Document):
    def before_save(self):
        doc = self
        existing_ids = {d.id for d in doc.supplier_rental_invoice_table}
        skipped_contracts = []
        
        # Get the first and last day of the selected month/year
        invoice_month_start = get_first_day(doc.from_date)
        invoice_month_end = get_last_day(doc.from_date)
        
        # Filters for check out contracts
        filters = {
            "supplier": doc.supplier,
            "status": "Check Out",
            "docstatus": 1
        }
        
        if doc.vehicle:
            filters["vehicle"] = doc.vehicle
            
        contracts = frappe.get_all("Supplier Rental Contract",
            filters=filters,
            fields=["name", "vehicle", "check_out_date", "rate", "purchase_order", "status","days"]
        )
        
        for c in contracts:
            check_out_date = getdate(c.check_out_date)
            
            # Check if contract's check_out_date falls within the selected month
            if invoice_month_start <= check_out_date <= invoice_month_end:
                # Check if this contract is already invoiced for this month
                existing = frappe.db.sql("""
                    SELECT sri.parent 
                    FROM `tabSupplier Rental Invoice Table` sri
                    JOIN `tabSupplier Rental Invoice` si ON sri.parent = si.name
                    WHERE sri.id = %s 
                    AND si.name != %s
                    AND MONTH(si.from_date) = MONTH(%s)
                    AND YEAR(si.from_date) = YEAR(%s)
                """, (c.name, doc.name, doc.from_date, doc.from_date), as_dict=1)
                
                if existing:
                    skipped_contracts.append(f"{c.name} (used in {existing[0].parent})")
                    continue
                
                if c.name in existing_ids:
                    continue  # Already in current doc
                
                # Calculate days based on check_out_date day of the month
                # For example, if check_out_date is 15th, then days would be 15
                # days_in_month = check_out_date.day
                
                # Calculate daily rate (monthly rate / 30)
                year = c.check_out_date.year
                month = c.check_out_date.month

                # Get the number of days in the month
                days_in_month = calendar.monthrange(year, month)[1]

                # Calculate daily rate based on actual number of days in the month
                rate_per_day = flt(c.rate) / days_in_month

                # Calculate total amount based on days and daily rate
                amount = rate_per_day * c.days

                doc.append("supplier_rental_invoice_table", {
                    "id": c.name,
                    "item": doc.item,
                    "vehicle": c.vehicle,
                    "purchase_order": c.purchase_order,
                    "number_of_days": c.days,
                    "rate": rate_per_day,
                    "status": c.status,
                    "check_out_date": c.check_out_date,
                    "amount": amount
                })
                
        
        # Recalculate totals
        total_days = 0
        total_amount = 0
        for d in doc.supplier_rental_invoice_table:
            # Amount is the contract rate
   
            # Rate per day is calculated by dividing amount by number of days
            total_days += d.number_of_days
            total_amount += d.amount  
        
        doc.total_days = total_days
        doc.total_amount = total_amount
        
        # Show message if any contracts were skipped due to duplication
        if skipped_contracts:
            frappe.msgprint("These contracts were already invoiced for this month and skipped: " + ", ".join(skipped_contracts))

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
