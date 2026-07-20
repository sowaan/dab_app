frappe.ui.form.on("Payment Reconciliation", {
	refresh(frm) {
		render_reconciliation_totals(frm);
		bind_selection_listeners(frm);
	},
	invoices_add(frm) {
		render_reconciliation_totals(frm);
	},
	invoices_remove(frm) {
		render_reconciliation_totals(frm);
	},
	payments_add(frm) {
		render_reconciliation_totals(frm);
	},
	payments_remove(frm) {
		render_reconciliation_totals(frm);
	},
});

function bind_selection_listeners(frm) {
	["invoices", "payments"].forEach((fieldname) => {
		let grid = frm.fields_dict[fieldname]?.grid;
		if (!grid || !grid.wrapper) return;

		$(grid.wrapper)
			.off("click.recon_totals", ".grid-row-check")
			.on("click.recon_totals", ".grid-row-check", () => {
				render_reconciliation_totals(frm);
			});
	});
}

function render_reconciliation_totals(frm) {
	let currency = frm.doc.currency || frappe.defaults.get_default("currency");

	let invoice_total = get_grid_total(frm, "invoices", "outstanding_amount");
	let payment_total = get_grid_total(frm, "payments", "amount");
	let difference = invoice_total - payment_total;
	let diff_color = difference === 0 ? "#2e7d32" : "#c62828";

	let diff_row = `<div style="margin-top:4px; padding-top:4px; border-top:1px dashed #d1d8dd; color:${diff_color}">${__(
		"Difference"
	)}: ${format_currency(difference, currency)}</div>`;

	render_grid_total(frm, "invoices", `
		<div>${__("Total Invoice Amount")}: ${format_currency(invoice_total, currency)}</div>
		${diff_row}
	`);

	render_grid_total(frm, "payments", `
		<div>${__("Total Payment Amount")}: ${format_currency(payment_total, currency)}</div>
		${diff_row}
	`);
}

function render_grid_total(frm, fieldname, inner_html) {
	let grid = frm.fields_dict[fieldname]?.grid;
	if (!grid || !grid.wrapper) return;

	let html = `
		<div class="reconciliation-total-summary" style="
				padding:10px 12px;
				margin-bottom:10px;
				border:1px solid #d1d8dd;
				border-radius:5px;
				background:#fafafa;
				font-weight:600;
			">
			${inner_html}
		</div>
	`;

	$(grid.wrapper).find(".reconciliation-total-summary").remove();
	$(grid.wrapper).prepend(html);
}

function get_grid_total(frm, fieldname, amount_field) {
	let grid = frm.fields_dict[fieldname]?.grid;
	if (!grid) return 0;

	let selected = grid.get_selected_children();
	let rows = selected.length ? selected : frm.doc[fieldname] || [];

	return rows.reduce((sum, row) => sum + flt(row[amount_field]), 0);
}
