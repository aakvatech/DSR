// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dispensed for Office Use', {
	setup: function(frm) {
		frm.set_query('pump', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station
				}
			}
		});
		frm.set_query('shift', function() {
			return {
				filters: {
					'shift_status': 'Open'
				}
			}
		});
	},
	onload: function(frm,cdt,cdn) {
		auto_shift_selection(frm, cdt, cdn)
	},
	quantity:function(frm,cdt,cdn){
		calculate_amount(frm,cdt,cdn)
	}
});

var calculate_amount =  function (frm,cdt,cdn){
	var doc = locals[cdt][cdn]
	if(doc.quantity && doc.fuel_item){
		frappe.call({
			method: "frappe.client.get_value",
			args:{
				fieldname: "mera_wholesale_price",
				doctype: "Fuel Item",
				filters:{name:doc.fuel_item},
			},
			async: false,
			callback: function(data) {
				if(data.message){
					frappe.model.set_value(cdt,cdn,"amount",parseFloat(doc.quantity)*parseFloat(data.message.mera_wholesale_price))
				}
			}
		});
		
	}
}
