// Copyright (c) 2025, Sowaan Pvt. Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier Rental Invoice', {
    refresh: function(frm) {
        frm.add_custom_button('Generate Invoice', function() {
            if (!frm.doc.supplier_rental_invoice_table.length) {
                frappe.msgprint('No data in the table to generate invoice.');
                return;
            }

            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Purchase Invoice',
                        supplier: frm.doc.supplier,
                        items: frm.doc.supplier_rental_invoice_table.map(row => {
                            return {
                                item_code: row.item,
                                qty: row.number_of_days,
                                rate: row.rate,
                                custom_vehicle: row.vehicle,
                                custom_id: row.id
                            };
                        })
                    }
                },
                callback: function(r) {
                    if (!r.exc) {
                        
                        frappe.set_route('Form', 'Purchase Invoice', r.message.name);
                    }
                }
            });
        });
    }
});
