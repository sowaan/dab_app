import frappe
from frappe.utils import getdate, today, date_diff

def check_back_date_permission(doc, method=None):
    """
    Check if backdated entry is allowed for this DocType and current user/role.
    """

    # 1️⃣ Find the date field dynamically
    possible_date_fields = [
        "posting_date",
        "transaction_date",
        "bill_date",
        "invoice_date",
        "date",
    ]
    date_field = next((f for f in possible_date_fields if f in doc.as_dict()), None)
    if not date_field:
        return  # no relevant date field → skip

    doc_date = getdate(doc.get(date_field))
    today_date = getdate(today())

    # 2️⃣ Calculate how many days back the document is
    diff_days = date_diff(today_date, doc_date)
    if diff_days <= 0:
        return  # not backdated → skip

    # 3️⃣ Get active permissions
    permissions = frappe.get_all(
        "Back Date Entry Permission",        
        fields=["*"]
    )

    if not permissions:
        return
        # no permissions configured → block all backdated entries
        #frappe.throw("Backdated entries are not allowed. No permission configured.")

    # 4️⃣ For each permission, get child rows (users/roles, doctypes, days)
    allowed = False
    for perm in permissions:
        rows = frappe.get_all(
            "Back Date Entry Permission Detail",
            filters={"parent": perm.name, "doc_type": doc.doctype},
            fields=["permission_type", "user", "role", "allowed_days"]
        )

        for row in rows:
            if row.permission_type == "User" and row.user == frappe.session.user:
                if diff_days <= row.allowed_days:
                    allowed = True
                    break

            elif row.permission_type == "Role":
                roles = frappe.get_roles(frappe.session.user)
                if row.role in roles and diff_days <= row.allowed_days:
                    allowed = True
                    break

        if allowed:
            break

    # 5️⃣ If not allowed → block
    if not allowed:
        frappe.throw(
            f"You are not allowed to backdate {doc.doctype} by {diff_days} days."
        )

# def validate_back_date_permission(doc, method=None):
#     """
#     Restrict backdated document creation based on Back Date Entry Permission settings.
#     Automatically detects the main date field in the DocType.
#     """
#     frappe.msgprint("I've been called")

#     # 1️⃣ Identify the relevant date field dynamically
#     possible_date_fields = [
#         "posting_date",
#         "transaction_date",
#         "bill_date",
#         "invoice_date",
#         "date",
#     ]

#     date_field = next((f for f in possible_date_fields if f in doc.as_dict()), None)
#     if not date_field:
#         return  # Skip if this DocType has no date field

#     frappe.msgprint(f"Date Field {date_field}")

#     # 2️⃣ Compare document date with today's date
#     doc_date = getdate(doc.get(date_field))
#     today_date = getdate(today())
#     diff_days = (today_date - doc_date).days

#     # 3️⃣ Allow future or same-day documents
#     if diff_days <= 0:
#         return

#     # 4️⃣ Get active Back Date Entry Permission parents
#     parents = frappe.get_all(
#         "Back Date Entry Permission",
#         fields=["*"],
#         pluck="name"
#     )
#     if not parents: 
#         return  # No config → allow all

#     # 5️⃣ Fetch permission details for this DocType
#     details = frappe.get_all(
#         "Back Date Entry Permission Detail",
#         filters={"parent": ["in", parents], "doc_type": doc.doctype},
#         fields=["permission_type", "user", "role", "allowed_days"]
#     )

#     if not details:
#         # No specific permission for this doctype → restrict
#         frappe.throw(
#             f"You are not allowed to create or modify {doc.doctype} "
#             f"entries older than {diff_days} days (no permission defined)."
#         )

#     # 6️⃣ Check if user or their role is allowed
#     user_roles = frappe.get_roles(frappe.session.user)
#     for d in details:
#         if (
#             (d.permission_type == "User" and d.user == frappe.session.user)
#             or (d.permission_type == "Role" and d.role in user_roles)
#         ):
#             if diff_days <= d.allowed_days:
#                 return  # ✅ Allowed within limit

#     # 7️⃣ Otherwise, restrict
#     frappe.throw(
#         f"🚫 You are not allowed to create or modify {doc.doctype} "
#         f"older than {diff_days} days. Backdate permission not found."
#     )
