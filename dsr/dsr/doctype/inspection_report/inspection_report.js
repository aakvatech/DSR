// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inspection Report', {
	onload: function(frm) {
		console.log("yes")
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Inspection Report",
				fields: ["owner"],
				order_by: "inspection_date"
				},
			callback: function (r) {
				console.log("Yes")
			}
		});
	}
});
