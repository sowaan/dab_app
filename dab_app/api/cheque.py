import frappe

@frappe.whitelist()
def get_next_cheque_number(cheque_book):
    """
    Generate next cheque number purely from Cheque Book
    Respects:
    - serial_from
    - serial_to
    - first_cheque_number
    - no_of_page
    - invalid cheque list
    """

    if not cheque_book:
        frappe.throw("Cheque Book is required")

    cb = frappe.get_doc("Cheque Book", cheque_book)

    # --------------------------------------------------
    # Series Info
    # --------------------------------------------------
    serial_from_raw = cb.serial_from          # e.g. "04560"
    serial_to_raw = cb.serial_to              # e.g. "04660"
    first_cheque_raw = cb.first_cheque_number # e.g. "04563"

    serial_from = int(serial_from_raw)
    serial_to = int(serial_to_raw)
    first_cheque = int(first_cheque_raw) if first_cheque_raw else serial_from
    no_of_page = int(cb.no_of_page or 0)

    series_length = len(serial_from_raw)

    # --------------------------------------------------
    # Calculate MAX allowed cheque using no_of_page
    # --------------------------------------------------
    if no_of_page:
        max_allowed = min(
            serial_to,
            serial_from + no_of_page - 1
        )
    else:
        max_allowed = serial_to

    # --------------------------------------------------
    # Invalid / Rejected Cheques
    # --------------------------------------------------
    invalid_numbers = {
        int(row.cheque_no)
        for row in cb.invalid_cheque_list
        if row.cheque_no
    }

    # --------------------------------------------------
    # Last Used Cheque
    # --------------------------------------------------
    last_used = frappe.db.sql("""
        SELECT IFNULL(MAX(CAST(custom_cheque_no AS UNSIGNED)), 0)
        FROM `tabPayment Entry`
        WHERE custom_cheque_book = %s
          AND custom_cheque_no IS NOT NULL
          AND custom_cheque_no != ''
          AND docstatus < 2
    """, cheque_book)[0][0]

    # --------------------------------------------------
    # Determine Starting Point (FIX)
    # --------------------------------------------------
    if last_used:
        next_no = int(last_used) + 1
    else:
        # 🔥 THIS IS THE FIX
        next_no = max(serial_from, first_cheque)

    # --------------------------------------------------
    # Skip Invalid Cheques
    # --------------------------------------------------
    while next_no in invalid_numbers:
        next_no += 1

    # --------------------------------------------------
    # Overflow Protection
    # --------------------------------------------------
    if next_no > max_allowed:
        frappe.throw(
            f"Cheque Book exhausted. Max allowed cheque is "
            f"{str(max_allowed).zfill(series_length)}"
        )

    # --------------------------------------------------
    # Zero-pad before returning
    # --------------------------------------------------
    return str(next_no).zfill(series_length)
