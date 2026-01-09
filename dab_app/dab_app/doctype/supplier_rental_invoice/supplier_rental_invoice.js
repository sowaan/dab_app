/* ---------------- Supplier Rental Invoice ---------------- */
frappe.ui.form.on('Supplier Rental Invoice', {
    onload: function(frm) {
        // Filter cost_center based on selected custom_company
        frm.set_query("cost_center", () => {
            const company = frm.doc.custom_company;
            if (company) {
                return { filters: { company: company, is_group: 0 } };
            }
        });

        // Auto-select cost_center from linked Supplier Rental Contract if available
        if (frm.doc.supplier_rental_contract) {
            frappe.db.get_value(
                'Supplier Rental Contract',
                frm.doc.supplier_rental_contract,
                'cost_center'
            ).then(r => {
                if (r.message && r.message.cost_center && !frm.doc.cost_center) {
                    frm.set_value('cost_center', r.message.cost_center);
                }
            });
        }
    },

    refresh: function(frm) {
    console.log(frm.doc.docstatus)
    if (frm.doc.docstatus !== 1) return;

    frm.clear_custom_buttons(); // 🔥 VERY IMPORTANT

    frappe.call({
        method: "dab_app.dab_app.doctype.supplier_rental_invoice.supplier_rental_invoice.is_already_invoiced",
        args: {
            supplier_rental_invoice: frm.doc.name
        },
        callback: function(r) {
            if (!r.message) {
                // ✅ Not invoiced → show button
                add_generate_invoice_button(frm);
            }
        }
    });

    setupVehicleFilter(frm);
}

});

frappe.ui.form.on("Supplier Rental Invoice", {
    supplier_rental_invoice_table_add(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (!row.supplier_rental_contract || !frm.doc.custom_company) return;

        frappe.db.get_value(
            "Supplier Rental Contract",
            row.supplier_rental_contract,
            "custom_company"
        ).then(r => {
            if (r.message.custom_company !== frm.doc.custom_company) {
                frappe.msgprint({
                    title: "Company Mismatch",
                    indicator: "red",
                    message: `
                        Contract belongs to <b>${r.message.custom_company}</b><br>
                        Invoice company is <b>${frm.doc.custom_company}</b>
                    `
                });

                // optional: auto-clear invalid selection
                frappe.model.set_value(cdt, cdn, "supplier_rental_contract", null);
            }
        });
    }
});

function add_generate_invoice_button(frm) {
    frm.add_custom_button('Generate Invoice', function() {

        if (!frm.doc.supplier_rental_invoice_table.length) {
            frappe.msgprint('No data in the table to generate invoice.');
            return;
        }

        const contract_names = frm.doc.supplier_rental_invoice_table.map(row => row.id);
        const invoice_month = frappe.datetime.str_to_user(
            frappe.datetime.month_start(frm.doc.to_date)
        );

        frappe.call({
            method: "dab_app.dab_app.doctype.supplier_rental_invoice.supplier_rental_invoice.check_invoice_exists",
            args: {
                contract_names: contract_names,
                invoice_month: invoice_month
            },
            callback: function(r) {
                if (r.message && r.message.exists) {
                    frappe.msgprint({
                        message: `🚫 Purchase Invoice already exists for <b>${invoice_month}</b>.`,
                        title: "Duplicate Invoice Detected",
                        indicator: "red"
                    });
                    return;
                }

                create_purchase_invoice(frm, frm.doc.custom_company);
            }
        });
    });
}

// Function to create the Purchase Invoice
function create_purchase_invoice(frm, company) {
    const supplier = frm.doc.supplier;
    const selected_cost_center = frm.doc.cost_center;

    frappe.db.get_list("Department", {
        filters: { company: company },
        fields: ["name"],
        limit_page_length: 1
    }).then(dept_res => {
        if (!dept_res || dept_res.length === 0) {
            frappe.msgprint("No Department found for this company. Please create one first.");
            return;
        }

        const department = dept_res[0].name;

        if (selected_cost_center) {
            insert_purchase_invoice(frm, supplier, company, department, selected_cost_center);
        } else {
            frappe.db.get_list("Cost Center", {
                filters: { company: company, is_group: 0 },
                fields: ["name"],
                limit_page_length: 1
            }).then(cc_res => {
                if (!cc_res || cc_res.length === 0) {
                    frappe.msgprint(`No Cost Center found for company ${company}. Please create one.`);
                    return;
                }
                insert_purchase_invoice(frm, supplier, company, department, cc_res[0].name);
            });
        }
    });
}

// Function to insert Purchase Invoice
function insert_purchase_invoice(frm, supplier, company, department, cost_center) {
    frappe.call({
        method: 'frappe.client.insert',
        args: {
            doc: {
                doctype: 'Purchase Invoice',
                supplier: supplier,
                company: company,
                department: department,
                cost_center: cost_center,
                bill_no: "AUTO-" + Date.now(),
                bill_date: frm.doc.to_date,
                set_posting_time: 1,
                posting_date: frm.doc.to_date,
                supplier_rental_invoice: frm.doc.name,
                remarks: "Auto-generated invoice",
                custom_invoice_remarks: "Auto-generated",
                items: frm.doc.supplier_rental_invoice_table.map(row => ({
                    item_code: row.item,
                    qty: row.number_of_days,
                    rate: parseFloat(row.rate).toFixed(2),
                    amount: parseFloat(row.amount).toFixed(2),
                    custom_vehicle: row.vehicle,
                    custom_id: row.id,
                    supplier_rental_contract: row.supplier_rental_contract
                }))
            }
        },
        callback: function(r) {
            if (!r.exc) {
                const pi_name = r.message.name;
                const contract_names = frm.doc.supplier_rental_invoice_table.map(row => row.id);
               
                
                frm.clear_custom_buttons(); // immediate UX feedback

                // OPTIONAL: delay reload slightly to avoid async race
                setTimeout(() => {
                    frm.reload_doc();
                }, 500);
            
           // 🔥 syncs server state

                // Mark contracts as invoiced
                contract_names.forEach(id => {
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

                // Add invoicing history
                frappe.call({
                    method: "dab_app.dab_app.doctype.supplier_rental_invoice.supplier_rental_invoice.add_invoicing_history",
                    args: {
                        invoice_name: pi_name,
                        contract_names: contract_names,
                        invoice_month: frm.doc.to_date                                                
                    },
                    callback: function() {
                        frm.clear_custom_buttons();
                        frappe.msgprint("Invoicing History Inserted Successfully!");
                    }
                });

                //frappe.set_route('Form', 'Purchase Invoice', pi_name);
            }
        }
    });
}

// Optional: filter vehicles in child table
function setupVehicleFilter(frm) {
    frm.set_query('vehicle', () => ({
        filters: { custom_rental: 1 }
    }));
}
