frappe.ui.form.on('Supplier Rental Contract', {
    refresh: function(frm) {
        // Make check-out fields read-only by default
        make_check_out_fields_readonly(frm);
        
        // Remove buttons to avoid duplicates
        frm.remove_custom_button('Check In');
        frm.remove_custom_button('Check Out');

        // Control date fields based on status and docstatus
        control_check_dates(frm);

        // Show Check In button only if neither checked in nor checked out
        if (frm.doc.docstatus === 0 && frm.doc.status !== 'Check In' && frm.doc.status !== 'Check Out') {
            frm.add_custom_button('Check In', () => {
                frappe.call({
                    method: 'frappe.client.set_value',
                    args: {
                        doctype: frm.doc.doctype,
                        name: frm.doc.name,
                        fieldname: {
                            'status': 'Check In',
                            'check_in_date': frappe.datetime.now_datetime()  // Optional: auto-set Check In Date
                        }
                    },
                    callback: function() {
                        frm.reload_doc();
                    }
                });
            });
        }

        // Show Check Out button only after Check In (status = "Check In")
        if (frm.doc.docstatus === 0 && frm.doc.status === 'Check In') {
            frm.add_custom_button('Check Out', () => {
                // First make check-in fields read-only
                make_check_in_fields_readonly(frm, true);
                
                // Then make check-out fields editable
                make_check_out_fields_editable(frm);
                
                // Then set the status to Check Out
                frappe.call({
                    method: 'frappe.client.set_value',
                    args: {
                        doctype: frm.doc.doctype,
                        name: frm.doc.name,
                        fieldname: {
                            'status': 'Check Out',
                            'check_out_date': frappe.datetime.now_datetime()  // Optional: auto-set Check Out Date
                        }
                    },
                    callback: function() {
                        frm.reload_doc();
                    }
                });
            });
        }
        
        // If already in Check Out status, ensure fields are in correct state
        if (frm.doc.status === 'Check Out') {
            make_check_in_fields_readonly(frm, true);
            make_check_out_fields_editable(frm);
        }
    }
});

function control_check_dates(frm) {
    if (frm.doc.docstatus === 0) {
        // Draft - allow editing based on status
        if (frm.doc.status === 'Check In') {
            frm.set_df_property('check_in_date', 'read_only', 0);   // Editable during Check In phase
            frm.set_df_property('check_out_date', 'read_only', 1);  // Disable Check Out date until checked out
        } else if (frm.doc.status === 'Check Out') {
            frm.set_df_property('check_in_date', 'read_only', 1);   // Lock Check In Date after Check Out
            frm.set_df_property('check_out_date', 'read_only', 0);  // Allow Check Out date edit (optional if auto-set)
        } else {
            // Before Check In - Both fields editable if you want (or disable if required)
            frm.set_df_property('check_in_date', 'read_only', 0);
            frm.set_df_property('check_out_date', 'read_only', 1);
        }
    } else {
        // After Submit - Both fields are visible but read-only
        frm.set_df_property('check_in_date', 'read_only', 1);
        frm.set_df_property('check_out_date', 'read_only', 1);
    }
}

// Function to make check-in fields read-only
function make_check_in_fields_readonly(frm, readonly) {
    const check_in_fields = [
        'air_conditioner', 'antenna', 'ash_tray', 'fe', 'floor_mats', 
        'jack', 'lighter', 'lights', 'mulkia', 'reg_card', 
        'spare_tyre', 'toolkit', 'triangle', 'washer', 
        'wheel_caps', 'wipers', 'ws', 'wt'
    ];
    
    check_in_fields.forEach(field => {
        frm.set_df_property(field, 'read_only', readonly);
    });
}

// Function to make check-out fields read-only
function make_check_out_fields_readonly(frm) {
    const check_out_fields = [
        'air_conditioner_co', 'antenna_co', 'ash_tray_co', 'fe_co', 'floor_mats_co', 
        'jack_co', 'lighter_co', 'lights_co', 'mulkia_co', 'reg_card_co', 
        'spare_tyre_co', 'toolkit_co', 'triangle_co', 'washer_co', 
        'wheel_caps_co', 'wipers_co', 'ws_co', 'wt_co'
    ];
    
    check_out_fields.forEach(field => {
        frm.set_df_property(field, 'read_only', 1);  // Make read-only
    });
}

// Function to make check-out fields editable
function make_check_out_fields_editable(frm) {
    // Skip if document is submitted
    if (frm.doc.docstatus === 1) return;
    
    const check_out_fields = [
        'air_conditioner_co', 'antenna_co', 'ash_tray_co', 'fe_co', 'floor_mats_co', 
        'jack_co', 'lighter_co', 'lights_co', 'mulkia_co', 'reg_card_co', 
        'spare_tyre_co', 'toolkit_co', 'triangle_co', 'washer_co', 
        'wheel_caps_co', 'wipers_co', 'ws_co', 'wt_co'
    ];
    
    check_out_fields.forEach(field => {
        frm.set_df_property(field, 'read_only', 0);  // Make editable
    });
}