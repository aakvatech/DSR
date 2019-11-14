// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Credit Sales', {
	onload: function (frm, cdt, cdn) {
		auto_shift_selection(frm, cdt, cdn)
	},
	quantity: function (frm) {
		if (frm.doc.quantity && frm.doc.fuel_item) {
			calculate_total(frm)
		}

	},
	fuel_item: function (frm) {
		if (frm.doc.quantity && frm.doc.fuel_item) {
			calculate_total(frm)
		}
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

function calculate_total(frm) {
	frappe.call({
		method: "dsr.dsr.doctype.credit_sales.credit_sales.calculate_total",
		args: { "qty": frm.doc.quantity, "item": frm.doc.fuel_item },
		callback: function (r) {
			if (r.message) {
				frappe.model.set_value(frm.doc.doctype, frm.doc.name, "amount", r.message)
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
					frappe.model.set_value(cdt, cdn, "fuel_station", r.message[0].fuel_station)
				}
			}
		});
	}
}
