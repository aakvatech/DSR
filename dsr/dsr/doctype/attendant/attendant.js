// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendant', {
	// refresh: function(frm) {

	// }
	setup: function(frm) {
		frm.set_query('employee', function() {
			return {
				filters: {
					'company': frm.doc.company,
				}
			}
		});
	},
});
