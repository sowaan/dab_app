frappe.listview_settings['Supplier Rental Contract'] = {
    onload: function(listview) {
        listview.page.add_inner_button('Generate Monthly Invoice', () => {
            let selected = listview.get_checked_items().map(row => row.name);
            if (!selected.length) {
                frappe.msgprint('Please select at least one contract.');
                return;
            }

            frappe.call({
                method: 'dab_app.api.supplier_rental.generate_monthly_invoice',
                args: {
                    contract_ids: selected
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(r.message);
                    }
                }
            });
        });
    }
};
