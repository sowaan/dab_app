frappe.ui.form.on('Payment Entry', {
    refresh(frm) {
        enforce_cheque_ui(frm);
    },

    payment_type(frm) {
        enforce_cheque_ui(frm);
    },

    mode_of_payment(frm) {
        enforce_cheque_ui(frm);
    },

    custom_cheque_book(frm) {
        generate_cheque_no(frm);
    }
});

frappe.ui.form.on('Payment Entry', {
    custom_cheque_book(frm) {
        // ❌ Cheque book cleared → remove cheque no
        if (!frm.doc.custom_cheque_book) {
            frm.set_value("custom_cheque_no", null);
            return;
        }

        // ✅ Cheque book selected → generate cheque no
        generate_cheque_no(frm);
    }
});

/* ============================================================
   Enforce Cheque UI (Payment Type + MoP Type)
   ============================================================ */

function enforce_cheque_ui(frm) {
    if (!frm.doc.mode_of_payment) {
        hide_cheque_fields(frm);
        return;
    }

    frappe.db.get_value(
        "Mode of Payment",
        frm.doc.mode_of_payment,
        "type"
    ).then(r => {
        const mop_type = r.message?.type;

        const show_cheque =
            (frm.doc.payment_type === "Pay" ||
             frm.doc.payment_type === "Internal Transfer") &&
            mop_type === "Bank";

        // 🔥 Hard override (ERPNext-safe)
        frm.fields_dict["custom_cheque_book"].df.hidden = !show_cheque;
        frm.fields_dict["custom_cheque_no"].df.hidden = !show_cheque;

        frm.fields_dict["custom_cheque_book"].df.reqd = show_cheque;
        frm.fields_dict["custom_cheque_no"].df.reqd = show_cheque;

        frm.refresh_field("custom_cheque_book");
        frm.refresh_field("custom_cheque_no");

        if (!show_cheque) {
            hide_cheque_fields(frm);
        }
    });
}

function hide_cheque_fields(frm) {
    frm.set_value("custom_cheque_book", null);
    frm.set_value("custom_cheque_no", null);

    frm.fields_dict["custom_cheque_book"].df.hidden = 1;
    frm.fields_dict["custom_cheque_no"].df.hidden = 1;

    frm.fields_dict["custom_cheque_book"].df.reqd = 0;
    frm.fields_dict["custom_cheque_no"].df.reqd = 0;

    frm.refresh_field("custom_cheque_book");
    frm.refresh_field("custom_cheque_no");
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
            cheque_book: frm.doc.custom_cheque_book,
            payment_entry: frm.doc.name   // 👈 important (see below)
        },
        callback(res) {
            if (res.message) {
                // Force show before setting value
                frm.fields_dict["custom_cheque_no"].df.hidden = 0;
                frm.refresh_field("custom_cheque_no");

                frm.set_value("custom_cheque_no", res.message);
            }
        }
    });
}

/* ============================================================
   Filtering Cheque Books by Selected Company
   ============================================================ */
   
frappe.ui.form.on('Payment Entry', {
    setup(frm) {
        frm.set_query("custom_cheque_book", () => {
            return {
                filters: {
                    company: frm.doc.company,
                    is_active: 1
                }
            };
        });
    },

    company(frm) {
        // Clear cheque book if company changes
        frm.set_value("custom_cheque_book", null);
        frm.set_value("custom_cheque_no", null);
    }
});
