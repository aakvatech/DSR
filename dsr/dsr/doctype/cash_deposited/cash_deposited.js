// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cash Deposited', {
	onload: function(frm,cdt,cdn) {
		auto_shift_selection(frm, cdt, cdn)
	},
	setup:function(frm,cdt,cdn){
		frm.set_query('shift', function() {
			return {
				filters: {
					'shift_status': 'Open'
				}
			}
		});
		frm.set_query('name_of_bank', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station
				}
			}
		});
		frm.set_query('credit_sales_reference', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station,
					'full_paid': 0
				}
			}
		});
	},
	amount: function(frm) {
		if (frm.doc.credit_sales_reference) {
			frm.set_value("amount_to_be_deposited", frm.doc.amount)
		}
	},
	credit_sales_reference: function(frm) {
		if (frm.doc.credit_sales_reference) {
			cur_frm.add_fetch("credit_sales_reference", "amount", "amount_to_be_deposited")
			console.log(frm.doc.credit_sales_reference, frm.doc.amount, frm.doc.amount_to_be_deposited)
		}
		// else {
		// 	// For some reason this doesn't fire
		// 	cur_frm.add_fetch("shift", "cash_in_hand", "amount_to_be_deposited")
		// }
	},
	shift: function(frm) {
		frm.set_value("name_of_bank", "")
	},
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
					frappe.model.set_value(cdt, cdn, "date", r.message[0].date)
					frappe.model.set_value(cdt, cdn, "fuel_station", r.message[0].fuel_station)

				}
			}
		});
	}

}
