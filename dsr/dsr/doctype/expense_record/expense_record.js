// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expense Record', {
	onload: function(frm,cdt,cdn) {
		auto_shift_selection(frm, cdt, cdn)
	},
	setup: function(frm) {
		frm.set_query('expense_type', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station
				}
			}
		});
	}
});
var auto_shift_selection = function (frm, cdt, cdn) {
if (frm.doc.__islocal) {
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Shift",
			fields: ["name", "fuel_station"],
			order_by: "creation desc",
			limit_page_length: 1
		},
		async: false,
		callback: function (r) {
			if (r.message) {
				frappe.model.set_value(cdt, cdn, "shift", r.message[0].name)
				frappe.model.set_value(cdt, cdn, "fuel_station", r.message[0].fuel_station)

			}
		}
	});
}

}
