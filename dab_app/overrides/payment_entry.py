import frappe
from frappe import _

def validate(doc, method):
    """
    Cheque validation:
    - ONLY ensures cheque fields exist when shown
    - No bank account dependency
    """

    if not doc.mode_of_payment:
        return

    mop_type = frappe.db.get_value(
        "Mode of Payment",
        doc.mode_of_payment,
        "type"
    )

    if mop_type != "Bank":
        return

    if doc.payment_type not in ("Pay", "Internal Transfer"):
        return

    missing = []

    if not doc.cheque_book:
        missing.append(_("Cheque Book"))

    if not doc.custom_cheque_no:
        missing.append(_("Cheque Number"))

    if missing:
        frappe.throw(
            _("The following fields are required for Bank Payments: {0}")
            .format(", ".join(missing))
        )
