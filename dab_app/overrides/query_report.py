import json

import frappe
from frappe import _
from frappe.desk.query_report import (
	build_xlsx_data,
	clean_params,
	format_fields,
	parse_json,
	run,
	valid_report_name,
)
from frappe.utils import get_datetime, getdate

# Exporting a query report to Excel writes Date/Datetime columns as text cells:
# format_fields() turns every date into a display string, and prepared reports
# already hand back dates as ISO strings (their result is stored as JSON).
# make_xlsx() only writes a real Excel date when it receives a date object, so
# we save the raw values before format_fields() and put date objects back for
# Excel exports. CSV output is left exactly as core produces it.
#
# export_query, run_export_query_job and _export_query are copied from
# frappe/desk/query_report.py (Frappe 15.115.4). Changes are marked "dab_app:".
# Re-diff against core when upgrading Frappe.

DATE_FIELDTYPES = {"Date": getdate, "Datetime": get_datetime}


@frappe.whitelist()
def export_query():
	"""export from query reports"""
	from frappe.desk.utils import pop_csv_params

	form_params = frappe._dict(frappe.local.form_dict)
	csv_params = pop_csv_params(form_params)
	clean_params(form_params)
	parse_json(form_params)
	report_name = form_params.report_name
	frappe.permissions.can_export(
		frappe.get_cached_value("Report", report_name, "ref_doctype"),
		raise_exception=True,
	)

	export_in_background = int(form_params.export_in_background or 0)
	if export_in_background:
		user = frappe.session.user
		user_email = frappe.get_cached_value("User", user, "email")
		frappe.enqueue(
			# dab_app: our job, so background exports also get real dates
			"dab_app.overrides.query_report.run_export_query_job",
			user_email=user_email,
			form_params=form_params,
			csv_params=csv_params,
			queue="long",
			now=frappe.flags.in_test,
		)
		frappe.msgprint(
			_(
				"Your report is being generated in the background. You will receive an email on {0} with a download link once it is ready."
			).format(user_email)
		)
		return

	return _export_query(form_params, csv_params)


def run_export_query_job(user_email: str, form_params, csv_params):
	from frappe.desk.utils import send_report_email

	report_name, file_extension, content = _export_query(form_params, csv_params, populate_response=False)
	send_report_email(
		user_email, report_name, file_extension, content, attached_to_name=form_params.report_name
	)


def _export_query(form_params, csv_params, populate_response=True):
	from frappe.desk.utils import get_csv_bytes, provide_binary_file
	from frappe.utils.xlsxutils import handle_html, make_xlsx

	report_name = form_params.report_name
	file_format_type = form_params.file_format_type
	custom_columns = frappe.parse_json(form_params.custom_columns or "[]")
	include_indentation = form_params.include_indentation
	include_filters = form_params.include_filters
	visible_idx = form_params.visible_idx
	include_hidden_columns = form_params.include_hidden_columns

	if isinstance(visible_idx, str):
		visible_idx = json.loads(visible_idx)

	data = run(report_name, form_params.filters, custom_columns=custom_columns, are_default_filters=False)
	data = frappe._dict(data)
	data.filters = form_params.applied_filters

	if not data.columns:
		frappe.respond_as_web_page(
			_("No data to export"),
			_("You can try changing the filters of your report."),
		)
		return

	# dab_app: format_fields() overwrites dates with display strings, save the raw values first
	raw_dates = save_date_values(data) if file_format_type == "Excel" else {}

	format_fields(data)

	# dab_app: give make_xlsx() date objects so it writes real Excel date cells
	restore_date_values(data, raw_dates)
	
	xlsx_data, column_widths = build_xlsx_data(
		data,
		visible_idx,
		include_indentation,
		include_filters=include_filters,
		include_hidden_columns=include_hidden_columns,
	)

	if file_format_type == "CSV":
		content = get_csv_bytes(
			[[handle_html(frappe.as_unicode(v)) if isinstance(v, str) else v for v in r] for r in xlsx_data],
			csv_params,
		)
		file_extension = "csv"
	elif file_format_type == "Excel":
		file_extension = "xlsx"
		content = make_xlsx(xlsx_data, "Query Report", column_widths=column_widths).getvalue()

	if include_filters:
		for value in (data.filters or {}).values():
			suffix = ""
			if isinstance(value, list):
				suffix = "_" + ",".join(value)
			elif isinstance(value, str) and value not in {"Yes", "No"}:
				suffix = f"_{value}"

			if valid_report_name(report_name, suffix):
				report_name += suffix

	if not populate_response:
		return report_name, file_extension, content

	provide_binary_file(_(report_name), file_extension, content)


def save_date_values(data):
	"""Return {(row_idx, key): (fieldtype, raw value)} for every non-empty Date/Datetime cell."""
	saved = {}
	for i, col in enumerate(data.columns):
		# old-style reports use "Label:Fieldtype:Width" strings; format_fields() skips those too
		if not isinstance(col, dict) or col.get("fieldtype") not in DATE_FIELDTYPES:
			continue

		for row_idx, row in enumerate(data.result or []):
			if isinstance(row, dict):
				key = col.get("fieldname")
				val = row.get(key)
			elif isinstance(row, list | tuple) and i < len(row):
				key = i
				val = row[key]
			else:
				continue

			# getdate("") / get_datetime(None) return *today*, so empty cells must stay empty
			if val:
				saved[(row_idx, key)] = (col["fieldtype"], val)

	return saved


def restore_date_values(data, saved):
	for (row_idx, key), (fieldtype, val) in saved.items():
		try:
			value = DATE_FIELDTYPES[fieldtype](val)
		except Exception:
			# getdate() throws on text like "Opening", keep the formatted value instead of failing the export
			continue

		row = data.result[row_idx]
		if value and not isinstance(row, tuple):
			row[key] = value
