frappe.ui.form.on('Payment Entry', {
    refresh(frm) {
        enforce_cheque_ui(frm);
    },

    payment_type(frm) {
        enforce_cheque_ui(frm);
    },

    custom_cheque_book(frm) {
        generate_cheque_no(frm);
    }
});

/* ============================================================
   Force Cheque Book visibility (NO ERPNext dependency)
   ============================================================ */

function enforce_cheque_ui(frm) {
    const show_cheque =
        frm.doc.payment_type === "Pay" ||
        frm.doc.payment_type === "Internal Transfer";

    // 🔥 Hard override: bypass ERPNext core JS
    frm.fields_dict["custom_cheque_book"].df.hidden = !show_cheque;
    frm.fields_dict["custom_cheque_no"].df.hidden = !show_cheque;

    frm.fields_dict["custom_cheque_book"].df.reqd = show_cheque;
    frm.fields_dict["custom_cheque_no"].df.reqd = show_cheque;

    frm.refresh_field("custom_cheque_book");
    frm.refresh_field("custom_cheque_no");

    if (!show_cheque) {
        frm.set_value("custom_cheque_book", null);
        frm.set_value("custom_cheque_no", null);
    }
}

/* ============================================================
   Generate cheque number on cheque book selection
   ============================================================ */

function generate_cheque_no(frm) {
    if (!frm.doc.custom_cheque_book) {
        return;
    }

    frappe.call({
        method: "dab_app.api.cheque.get_next_cheque_number",
        args: {
            cheque_book: frm.doc.custom_cheque_book
        },
        callback(res) {
            if (res.message) {
                frm.set_value("custom_cheque_no", res.message);
            }
        }
    });
}
