frappe.ui.form.on('Supplier Rental Contract', {
    check: function(frm) {
        // Toggle visibility of replacement vehicle fields based on check value
        Object.keys(frm.fields_dict)
            .filter(fieldname => fieldname.startsWith('replacement_vehicle'))
            .forEach(fieldname => {
                frm.set_df_property(fieldname, 'hidden', frm.doc.check !== 'Replacement');
            });
    },

    
    
    refresh: function(frm) {
        // Calculate days between check-in and check-out
        calculateDaysDifference(frm);
        
        // Remove buttons to avoid duplicates
        frm.remove_custom_button('Check In');
        frm.remove_custom_button('Check Out');
        
        // Control date fields based on status
        controlCheckDates(frm);
        
        // Set up vehicle filter for rental-only vehicles
        setupVehicleFilter(frm);
        
        // Toggle visibility of check-out fields
        toggleCheckOutFields(frm);
        
        // Add Check Out button if applicable
        addCheckOutButton(frm);
        

        setupPurchaseOrderFilter(frm);
        // Make all fields read-only if contract is closed
        if (frm.doc.docstatus === 1 && frm.doc.contract_status === 'Closed') {
            makeAllFieldsReadOnly(frm);
        }
        
        // Set field states based on current status
        updateFieldStates(frm);
    }
});

// Calculate days between check-in and check-out dates
function calculateDaysDifference(frm) {
    if (frm.doc.check_in_date && frm.doc.check_out_date) {
        const checkIn = frappe.datetime.str_to_obj(frm.doc.check_in_date);
        const checkOut = frappe.datetime.str_to_obj(frm.doc.check_out_date);
        const dayDiff = frappe.datetime.get_day_diff(checkOut, checkIn);
        // Ensure days is at least 1 or the calculated difference + 1
        const days = Math.max(1, dayDiff + 1);
        frm.set_value('days', days);
    }
}

function setupPurchaseOrderFilter(frm) {
    frm.set_query('purchase_order', () => ({
        filters: { supplier: frm.doc.supplier }
    }));
}


// Control read-only status of date fields based on current status
function controlCheckDates(frm) {
    // Default all fields to read-only
    const dateFields = [
        'check_in_date', 'check_out_date', 'days', 
        'reason', 'check_out_kilometers', 'check_out_fuel'
    ];
    
    // Set all fields to read-only by default
    dateFields.forEach(field => frm.set_df_property(field, 'read_only', 1));
    
    // Enable specific fields based on status
    if (frm.doc.status === 'Check In') {
        frm.set_df_property('check_in_date', 'read_only', 0);
    } else if (frm.doc.status === 'Check Out') {
        const editableFields = [
            'check_out_date', 'days', 'reason', 
            'check_out_kilometers', 'check_out_fuel'
        ];
        editableFields.forEach(field => frm.set_df_property(field, 'read_only', 0));
    } else {
        // Default state (before check-in)
        frm.set_df_property('check_in_date', 'read_only', 0);
    }
}

// Set up vehicle filter to only show rental vehicles
function setupVehicleFilter(frm) {
    frm.set_query('vehicle', () => ({
        filters: { custom_rental: 1 }
    }));
}

// Toggle visibility of check-out related fields
function toggleCheckOutFields(frm) {
    const isCheckOut = frm.doc.status === 'Check Out';
    frm.set_df_property('check_out_kilometers', 'hidden', !isCheckOut);
    frm.set_df_property('check_out_fuel', 'hidden', !isCheckOut);
}

// Add Check Out button for submitted documents in Check In status
function addCheckOutButton(frm) {
    if (frm.doc.docstatus === 1 && frm.doc.status === 'Check In') {
        frm.add_custom_button('Check Out', () => {
            // First make check-in fields read-only
            setCheckInFieldsReadOnly(frm, true);
            
            // Then make check-out fields editable
            setCheckOutFieldsEditable(frm);
            
            // Update status to Check Out
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: frm.doc.doctype,
                    name: frm.doc.name,
                    fieldname: {
                        'status': 'Check Out',
                        'check_out_date': frappe.datetime.now_datetime()
                    }
                },
                callback: function() {
                    frm.reload_doc();
                }
            });
        });
    }
}

// Make all form fields read-only
function makeAllFieldsReadOnly(frm) {
    frm.fields.forEach(field => {
        frm.set_df_property(field.df.fieldname, 'read_only', 1);
    });
}

// Update field states based on current document status
function updateFieldStates(frm) {
    if (frm.doc.status === 'Check Out') {
        setCheckInFieldsReadOnly(frm, true);
        setCheckOutFieldsEditable(frm);
    }
}

// Set check-in fields to read-only state
function setCheckInFieldsReadOnly(frm, readonly) {
    const checkInFields = [
        'air_conditioner', 'antenna', 'ash_tray', 'fe', 'floor_mats', 
        'jack', 'lighter', 'lights', 'mulkia', 'reg_card', 
        'spare_tyre', 'toolkit', 'triangle', 'washer', 
        'wheel_caps', 'wipers', 'ws', 'wt', 'vehicle_marking'
    ];
    
    checkInFields.forEach(field => {
        frm.set_df_property(field, 'read_only', readonly);
    });
}

// Make check-out fields editable 
function setCheckOutFieldsEditable(frm) {
    const checkOutFields = [
        'air_conditioner_co', 'antenna_co', 'ash_tray_co', 'fe_co', 'floor_mats_co', 
        'jack_co', 'lighter_co', 'lights_co', 'mulkia_co', 'reg_card_co', 
        'spare_tyre_co', 'toolkit_co', 'triangle_co', 'washer_co', 
        'wheel_caps_co', 'wipers_co', 'ws_co', 'wt_co'
    ];
    
    checkOutFields.forEach(field => {
        frm.set_df_property(field, 'read_only', 0);
    });

    // Show additional check-out related fields
    frm.set_df_property('vehicle_marking_check_out', 'hidden', 0);
    frm.set_df_property('section_break_jmrr', 'hidden', 0);
    frm.set_df_property('check_out_kilometers', 'read_only', 0);
    frm.set_df_property('check_out_kilometers', 'hidden', 0);
    frm.set_df_property('check_out_fuel', 'read_only', 0);
    frm.set_df_property('check_out_fuel', 'hidden', 0);
}