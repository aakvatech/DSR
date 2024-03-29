// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Credit Sales', {
	setup: function(frm) {
		frm.set_query('credit_customer', function() {
			return {
				filters: {
					'disabled': 0,
					'is_frozen': 0
				}
			}
		});
		frm.set_query('fuel_item', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station
				}
			}
		});
		frm.set_query('pump', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station,
					'fuel_item': frm.doc.fuel_item
				}
			}
		});
		frm.set_query('lpo', function() {
			return {
				filters: {
					'fuel_station': frm.doc.fuel_station,
					'docstatus': 1,
					"fulfilled": ["!=", "Completely Fulfilled"]
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
	onload: function (frm, cdt, cdn) {
		auto_shift_selection(frm, cdt, cdn)
	},
	quantity: function (frm) {
		if ((frm.doc.quantity > frm.doc.original_quantity) && frm.doc.lpo ) {
			frm.set_value("quantity", frm.doc.quantity)
			frappe.throw("Entered quantity cannot be greater than LPO quantity. Resetting the quantity to original quantity.")
		}
		if (frm.doc.quantity && frm.doc.fuel_item) {
			calculate_total(frm)
		}
	},
	credit_customer_type: function (frm) {
		// if (frm.doc.quantity && frm.doc.fuel_item) {
		// 	calculate_total(frm)
		// }
		if (frm.doc.credit_customer_type == "Discounted Cash") {
			frm.set_value("discounted_cash_customer", true)
		} else {
			frm.set_value("discounted_cash_customer", false)
		}
	},
	lpo: function (frm) {
		if (frm.doc.lpo) {
			frm.set_df_property("vehicle_number", "read_only", true);
			frm.set_df_property("credit_customer", "read_only", true);
			frm.set_df_property("is_cash_received_at_other_station", "read_only", true);
			frm.set_df_property("discounted_cash_customer", "read_only", true);
			frm.set_df_property("fuel_item", "read_only", true);
			frm.set_value("is_cash_received_at_other_station", false)
			frm.set_value("discounted_cash_customer", false)
			frm.set_value("manual_lpo_no", "")
			frm.set_value("pump", "")
			// console.log("setting fuel item from lpo", frm.doc.lpo)
			// frm.add_fetch("lpo","fuel_item","fuel_item")
			// console.log("fuel item set to", frm.doc.fuel_item)
		} else {
			frm.set_df_property("vehicle_number", "read_only", false);
			frm.set_df_property("credit_customer", "read_only", false);
			frm.set_df_property("is_cash_received_at_other_station", "read_only", false);
			frm.set_df_property("discounted_cash_customer", "read_only", false);
			frm.set_df_property("fuel_item", "read_only", false);
			frm.set_value("cg_lpo_owner", "")
			frm.set_value("credit_customer", "")
			frm.set_value("credit_customer_type", "")
			frm.set_value("vehicle_number", "")
			frm.set_value("quantity", "")
			frm.set_value("original_quantity", "")
			frm.set_value("amount", "")
			frm.set_value("fuel_item", "")
			frm.set_value("pump", "")
		}
	},
	fuel_item: function (frm) {
		if (frm.doc.quantity && frm.doc.fuel_item) {
			calculate_total(frm)
			frm.set_value("pump", "")
		};
	},
	is_cash_received_at_other_station: function (frm, cdt, cdn) {
		if (frm.doc.is_cash_received_at_other_station) {
			validate_mandatory_field(frm, cdt, cdn)
			frappe.call({
				method: "dsr.dsr.doctype.credit_sales.credit_sales.get_cash_receiver_other_station_details",
				args: { 'station': frm.doc.fuel_station, 'customer': frm.doc.credit_customer, 'vehicle': frm.doc.vehicle_number },
				callback: function (r) {
					if (r.message) {
						if (r.message.balance_qty == 0 || r.message.balance_qty == '') {
							frappe.model.set_value(cdt, cdn, "is_cash_received_at_other_station", 0)
							frappe.throw(__("No Balance Qty Available For Vehicle {0} At Fuel Station {1}", [frm.doc.vehicle_number, frm.doc.fuel_station]))
						}
						frappe.model.set_value(cdt, cdn, "other_station_cash_record", r.message.name)
						frappe.model.set_value(cdt, cdn, "pump", r.message.pump)
						frappe.model.set_value(cdt, cdn, "fuel_item", r.message.item)
						frappe.model.set_value(cdt, cdn, "quantity", r.message.balance_qty)
					}
				}
			})
		}
	}
});

frappe.ui.form.on("Credit Sales", "before_submit", function(frm, cdt, cdn) {
	// your code
	if (!frm.doc.lpo && !frm.doc.manual_lpo_no)
		frappe.throw(__("Please enter Manual LPO number as this credit sales is not from a Customer Generated LPO"))
 })
 
function calculate_total(frm) {
	frappe.call({
		method: "dsr.dsr.doctype.credit_sales.credit_sales.calculate_total",
		args: { "qty": frm.doc.quantity, "item": frm.doc.fuel_item },
		callback: function (r) {
			if (r.message) {
				frm.set_value("amount", r.message)
			}
		}
	})
}

function validate_mandatory_field(frm, cdt, cdn) {
	if (!frm.doc.fuel_station) {
		frappe.model.set_value(cdt, cdn, "is_cash_received_at_other_station", 0)
		frappe.throw(__("Fuel Station Is Mandatory For Fetch Cash Receive From Other Station"))
	}
	if (!frm.doc.credit_customer) {
		frappe.model.set_value(cdt, cdn, "is_cash_received_at_other_station", 0)
		frappe.throw(__("Credit Customer Is Mandatory For Fetch Cash Receive From Other Station"))
	}
	if (!frm.doc.vehicle_number) {
		frappe.model.set_value(cdt, cdn, "is_cash_received_at_other_station", 0)
		frappe.throw(__("Vehicle Is Mandatory For Fetch Cash Receive From Other Station"))
	}
}

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
