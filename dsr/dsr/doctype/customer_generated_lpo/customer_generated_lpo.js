// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Generated LPO', {
	setup: function(frm) {
		frm.set_query('fuel_item', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station
				}
			}
		});
	},
	fuel_station: function(frm) {
		frm.set_value("fuel_item", "")
		frm.set_value("station_full_name", "")
	},
	// refresh: function(frm) {

	// }
});
