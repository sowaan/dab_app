frappe.ui.form.on('Payment Entry', {
    setup(frm) {
        // --------------------------------------------------
        // Filter cheque books by Company + Active
        // --------------------------------------------------
        frm.set_query("custom_cheque_book", () => {
            return {
                filters: {
                    company: frm.doc.company,
                    is_active: 1
                }
            };
        });
    },

    refresh(frm) {
        // UI only — NO set_value here
        enforce_cheque_ui(frm);
    },

    payment_type(frm) {
        enforce_cheque_ui(frm);
    },

    mode_of_payment(frm) {
        enforce_cheque_ui(frm);
    },

    company(frm) {
        // User action → safe to clear
        frm.set_value("custom_cheque_book", null);
        frm.set_value("custom_cheque_no", null);
    },

    custom_cheque_book(frm) {
        // ---------------------------------------------
        // User cleared cheque book → clear cheque no
        // ---------------------------------------------
        if (!frm.doc.custom_cheque_book) {
            frm.set_value("custom_cheque_no", null);
            return;
        }

        // ---------------------------------------------
        // Do NOT mutate values during save / workflow
        // ---------------------------------------------
        if (frm.is_saving || frm.doc.__unsaved === 0 || frm.doc.docstatus !== 0) {
            return;
        }

        // ---------------------------------------------
        // Generate cheque number (user-triggered only)
        // ---------------------------------------------
        generate_cheque_no(frm);
    }
});

/* ============================================================
   Enforce Cheque UI (Payment Type + MoP Type)
   UI ONLY — no set_value here
   ============================================================ */

function enforce_cheque_ui(frm) {
    if (!frm.doc.mode_of_payment) {
        hide_cheque_ui(frm);
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
        frm.fields_dict.custom_cheque_book.df.hidden = !show_cheque;
        frm.fields_dict.custom_cheque_no.df.hidden = !show_cheque;

        frm.fields_dict.custom_cheque_book.df.reqd = show_cheque;
        frm.fields_dict.custom_cheque_no.df.reqd = show_cheque;

        frm.refresh_field("custom_cheque_book");
        frm.refresh_field("custom_cheque_no");

        if (!show_cheque) {
            hide_cheque_ui(frm);
        }
    });
}

function hide_cheque_ui(frm) {
    frm.fields_dict.custom_cheque_book.df.hidden = 1;
    frm.fields_dict.custom_cheque_no.df.hidden = 1;

    frm.fields_dict.custom_cheque_book.df.reqd = 0;
    frm.fields_dict.custom_cheque_no.df.reqd = 0;

    frm.refresh_field("custom_cheque_book");
    frm.refresh_field("custom_cheque_no");
}

/* ============================================================
   Generate cheque number (USER ACTION ONLY)
   ============================================================ */

function generate_cheque_no(frm) {
    if (!frm.doc.custom_cheque_book) {
        return;
    }

    frappe.call({
        method: "dab_app.api.cheque.get_next_cheque_number",
        args: {
            cheque_book: frm.doc.custom_cheque_book,
            payment_entry: frm.doc.name
        },
        callback(res) {
            if (res.message && frm.doc.custom_cheque_no !== res.message) {
                // Force visible before setting
                frm.fields_dict.custom_cheque_no.df.hidden = 0;
                frm.refresh_field("custom_cheque_no");

                frm.set_value("custom_cheque_no", res.message);
            }
        }
    });
}
