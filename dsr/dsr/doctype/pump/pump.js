// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pump', {
	setup: function(frm){
		frm.set_query('fuel_item', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station,
				}
			}
		});
		frm.set_query('warehouse', function() {
			return {
				filters: {
					'company': frm.doc.company,
				}
			}
		});
	},
});
