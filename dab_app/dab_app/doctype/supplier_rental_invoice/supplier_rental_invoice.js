frappe.ui.form.on('Supplier Rental Invoice', {

    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button('Generate Invoice', function() {
                if (!frm.doc.supplier_rental_invoice_table.length) {
                    frappe.msgprint('No data in the table to generate invoice.');
                    return;
                }

                const ids = frm.doc.supplier_rental_invoice_table.map(row => row.id);

                // After creating Purchase Invoice
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
            const ids = frm.doc.supplier_rental_invoice_table.map(row => row.id);

            // Loop to mark each contract as invoiced
            ids.forEach(id => {
                frappe.call({
                    method: 'frappe.client.set_value',
                    args: {
                        doctype: 'Supplier Rental Contract',
                        name: id,
                        fieldname: 'purchase_invoiced',
                        value: 1
                    },
                    freeze: true,
                    freeze_message: "Marking contracts as invoiced..."
                });
            });

            frappe.set_route('Form', 'Purchase Invoice', r.message.name);
        }
    }
});
            });
        }

        setupVehicleFilter(frm);
    }

});

function setupVehicleFilter(frm) {
    frm.set_query('vehicle', () => ({
        filters: { custom_rental: 1 }
    }));
}
