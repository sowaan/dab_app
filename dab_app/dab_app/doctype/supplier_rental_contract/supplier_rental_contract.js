/* ---------------- Supplier Rental Contract ---------------- */
frappe.ui.form.on('Supplier Rental Contract', {
onload: function(frm) {
// Filter allowed companies
frm.set_query("company", () => ({
query: "frappe.core.doctype.user_permission.user_permission.get_allowed_companies"
}));

    // Filter cost center based on current company or custom_company
    frm.set_query("cost_center", () => {
        const company = frm.doc.custom_company || frm.doc.company;
        if (company) {
            return {
                filters: {
                    company: company,
                    is_group: 0
                }
            };
        }
    });
},

company: function(frm) {
    // Clear previous selection
    frm.set_value('cost_center', null);
    // Re-filter cost centers based on newly selected company
    frm.set_query("cost_center", () => {
        if (frm.doc.company) {
            return {
                filters: {
                    company: frm.doc.company,
                    is_group: 0
                }
            };
        }
    });
},

refresh: function(frm) {
    // --- Auto-set custom_company and custom_cost_center ---
    if (frm.doc.supplier_rental_contract) {
        frappe.db.get_value(
            'Supplier Rental Contract',
            frm.doc.supplier_rental_contract,
            ['company', 'cost_center']
        ).then(r => {
            if (r.message) {
                if (!frm.doc.custom_company && r.message.company) {
                    frm.set_value('custom_company', r.message.company);
                }
                if (!frm.doc.custom_cost_center && r.message.cost_center) {
                    frm.set_value('cost_center', r.message.cost_center);
                }
            }
        });
    }

    // --- Remove buttons to avoid duplicates ---
    frm.remove_custom_button('Check In');
    frm.remove_custom_button('Check Out');

    // --- Control date fields based on status ---
    controlCheckDates(frm);

    // --- Vehicle filter for rental-only vehicles ---
    setupVehicleFilter(frm);

    // --- Toggle visibility of check-out fields ---
    toggleCheckOutFields(frm);

    // --- Add Check Out button if applicable ---
    addCheckOutButton(frm);

    // --- Setup purchase order filter ---
    setupPurchaseOrderFilter(frm);

    // --- Make all fields read-only if contract is closed ---
    if (frm.doc.docstatus === 1 && frm.doc.contract_status === 'Closed') {
        makeAllFieldsReadOnly(frm);
    }

    // --- Update field states based on status ---
    updateFieldStates(frm);
}

});

// ---------------- Helper functions ----------------
function calculateDaysDifference(frm) {
if (frm.doc.check_in_date && frm.doc.check_out_date) {
    const checkIn = frappe.datetime.str_to_obj(frm.doc.check_in_date);
    const checkOut = frappe.datetime.str_to_obj(frm.doc.check_out_date);
    const dayDiff = frappe.datetime.get_day_diff(checkOut, checkIn);
    const days = Math.max(1, dayDiff + 1);
    frm.set_value('days', days);
}
}

function setupPurchaseOrderFilter(frm) {
    frm.set_query('purchase_order', () => ({
    filters: { supplier: frm.doc.supplier }
    }));
}

function controlCheckDates(frm) {
    const dateFields = [
    'check_in_date', 'check_out_date', 'days',
    'reason', 'check_out_kilometers', 'check_out_fuel'
    ];
dateFields.forEach(field => frm.set_df_property(field, 'read_only', 1));

if (frm.doc.status === 'Check In') {
    frm.set_df_property('check_in_date', 'read_only', 0);
} else if (frm.doc.status === 'Check Out') {
    const editableFields = [
        'check_out_date', 'days', 'reason',
        'check_out_kilometers', 'check_out_fuel'
    ];
    editableFields.forEach(field => frm.set_df_property(field, 'read_only', 0));
} else {
    frm.set_df_property('check_in_date', 'read_only', 0);
}

}

function setupVehicleFilter(frm) {
    frm.set_query('vehicle', () => ({
    filters: { custom_rental: 1 }
    }));
}

function toggleCheckOutFields(frm) {
    const isCheckOut = frm.doc.status === 'Check Out';
    frm.set_df_property('check_out_kilometers', 'hidden', !isCheckOut);
    frm.set_df_property('check_out_fuel', 'hidden', !isCheckOut);
}

function addCheckOutButton(frm) {
if (frm.doc.docstatus === 1 && frm.doc.status === 'Check In') {
    frm.add_custom_button('Check Out', () => {
    setCheckInFieldsReadOnly(frm, true);
    setCheckOutFieldsEditable(frm);

        const checkOutDateStr = frappe.datetime.now_date();
        const dayOfMonth = frappe.datetime.str_to_obj(checkOutDateStr).getDate();
        const updatedInvoicedDays = (frm.doc.invoiced_days || 0) + dayOfMonth;

        frappe.call({
            method: 'frappe.client.set_value',
            args: {
                doctype: frm.doc.doctype,
                name: frm.doc.name,
                fieldname: {
                    'status': 'Check Out',
                    'check_out_date': checkOutDateStr,
                    'days': dayOfMonth,
                    'invoiced_days': updatedInvoicedDays
                }
            },
            callback: function() {
                frm.reload_doc();
            }
        });
    });
}

}

function makeAllFieldsReadOnly(frm) {
    frm.fields.forEach(field => {
    frm.set_df_property(field.df.fieldname, 'read_only', 1);
});
}

function updateFieldStates(frm) {
if (frm.doc.status === 'Check Out') {
    setCheckInFieldsReadOnly(frm, true);
    setCheckOutFieldsEditable(frm);
}
}

function setCheckInFieldsReadOnly(frm, readonly) {
    const checkInFields = [
    'air_conditioner', 'antenna', 'ash_tray', 'fe', 'floor_mats',
    'jack', 'lighter', 'lights', 'mulkia', 'reg_card',
    'spare_tyre', 'toolkit', 'triangle', 'washer',
    'wheel_caps', 'wipers', 'ws', 'wt', 'vehicle_marking'
    ];
checkInFields.forEach(field => frm.set_df_property(field, 'read_only', readonly));
}

function setCheckOutFieldsEditable(frm) {
    const checkOutFields = [
    'air_conditioner_co', 'antenna_co', 'ash_tray_co', 'fe_co', 'floor_mats_co',
    'jack_co', 'lighter_co', 'lights_co', 'mulkia_co', 'reg_card_co',
    'spare_tyre_co', 'toolkit_co', 'triangle_co', 'washer_co',
    'wheel_caps_co', 'wipers_co', 'ws_co', 'wt_co'
    ];
checkOutFields.forEach(field => frm.set_df_property(field, 'read_only', 0));

frm.set_df_property('vehicle_marking_check_out', 'hidden', 0);
frm.set_df_property('section_break_jmrr', 'hidden', 0);
frm.set_df_property('check_out_kilometers', 'read_only', 0);
frm.set_df_property('check_out_kilometers', 'hidden', 0);
frm.set_df_property('check_out_fuel', 'read_only', 0);
frm.set_df_property('check_out_fuel', 'hidden', 0);

}

function removeCustomButtons(frm) {
frm.remove_custom_button('Check In');
frm.remove_custom_button('Check Out');
}