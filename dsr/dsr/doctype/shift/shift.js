// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shift', {
	refresh: function (frm) {
		if (!frm.doc.__islocal && frm.doc.shift_status == "Open") {
			frm.add_custom_button(__('Close Shift'), function () {
				frm.events.close_shift(frm);
			}).addClass("btn-primary");
		}
		if (frm.doc.shift_status == "Closed") {
			frm.set_df_property("fuel_station", "read_only", true);
			frm.set_df_property("shift_name", "read_only", true);
			frm.set_df_property("shift_from", "read_only", true);
			frm.set_df_property("shift_to", "read_only", true);
			frm.set_df_property("date", "read_only", true);
			frm.set_df_property("pump_meter_reading", "read_only", true);
			frm.set_df_property("attendant_pump", "read_only", true);
			frm.set_df_property("dip_reading", "read_only", true);
			frm.set_df_property("generator_reading", "read_only", true);
			frappe.meta.get_docfield("Pump Meter Reading", "pump", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Pump Meter Reading", "closing_mechanical", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Pump Meter Reading", "closing_electrical", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Attendant Pump", "attendant", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Attendant Pump", "pump", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Attendant Pump", "cash_deposited", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Dip Reading", "fuel_tank", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Dip Reading", "closing_mm", frm.doc.name).read_only = 1;
		}
	},
	get_last_shift_details:function(frm){
		if(!frm.doc.fuel_station){
			frappe.throw(__("Fuel Station Require For Load Last Shift Details"))
		}
		get_last_shift_data(frm)
	},
	close_shift: (frm) => {
		validate_meter_leading(frm)
		validate_attendant_pump(frm)
		validate_deep_reading(frm)
		frappe.call({
			method: "dsr.dsr.doctype.shift.shift.close_shift",
			args: { 'name': frm.doc.name, 'status': 'Closed' },
			callback: function (r) {
				cur_frm.reload_doc()
			}
		});
	},
	fuel_station: function (frm, cdt, cdn) {
		var doc = locals[cdt][cdn];
		console.log(doc.fuel_station)
		if (doc.fuel_station) {
			if(frm.doc.__islocal){
				validate_close_shift(frm)
			}
			get_dip_reading(frm)
			get_pump_meter_reading(frm)
			get_attendant_pump(frm)
		}
	},
	recalculate_sales_total:function(frm,cdt,cdn){
		var doc = locals[cdt][cdn];
		doc.pump_meter_reading.forEach((d, index) => {
			frappe.model.set_value(d.doctype, d.name, "calculated_sales", d.closing_electrical - d.opening_electrical)
		});
		refresh_field("attendance_pump");
	}
});

function get_last_shift_data(frm){
	frappe.call({
		method:"dsr.dsr.doctype.shift.shift.get_last_shift_data",
		args:{
			fuel_station:frm.doc.fuel_station
		},
		callback:function(r)
		{
			if(r.message){
				frm.clear_table("pump_meter_reading");
				r.message.pump_meter_reading.forEach(d => {
					var child = frm.add_child("pump_meter_reading");
					frappe.model.set_value(child.doctype, child.name, "pump", d.pump)
					frappe.model.set_value(child.doctype, child.name, "opening_electrical", d.closing_electrical)
					frappe.model.set_value(child.doctype, child.name, "opening_mechanical", d.closing_mechanical)
				});
				refresh_field("pump_meter_reading");
				frm.clear_table("dip_reading");
				r.message.dip_reading.forEach(d => {
					var child = frm.add_child("dip_reading");
					frappe.model.set_value(child.doctype, child.name, "fuel_tank", d.fuel_tank)
					frappe.model.set_value(child.doctype, child.name, "opening_mm", d.closing_mm)
				});
				refresh_field("dip_reading");
			}
		}
	});
}

function validate_close_shift(frm){
	frappe.call({
		method:"frappe.client.get_list",
		args:{
			doctype: 'Shift',
			filters: {'shift_status': 'Open','fuel_station':frm.doc.fuel_station},
			fields:["name"]
		},
		callback:function(r)
		{
			if(r.message.length >= 1){
				frappe.throw(__("{0} Is Not Close Yet",[r.message[0].name]))
			}
		}
	});
}

function get_dip_reading(frm){
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: 'Fuel Tank',
			filters: { 'fuel_station': frm.doc.fuel_station },
			fields: ["name", "tank_capacity"],
			order_by: 'fuel_item desc, tank_number asc'
		},
		async: false,
		callback: function (r) {
			frm.clear_table("dip_reading");
			r.message.forEach(d => {
				var child = frm.add_child("dip_reading")
				frappe.model.set_value(child.doctype, child.name, "fuel_tank", d.name);
			});
			refresh_field("dip_reading");
		}
	});
}

function get_pump_meter_reading(frm){
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: 'Pump',
			filters: { 'fuel_station': frm.doc.fuel_station },
			fields: ["name"],
			order_by: 'fuel_item desc, pump_number asc'
		},
		async: false,
		callback: function (r) {
			frm.clear_table("pump_meter_reading");
			r.message.forEach(d => {
				var child = frm.add_child("pump_meter_reading");
				frappe.model.set_value(child.doctype, child.name, "pump", d.name);
			});
			refresh_field("pump_meter_reading");
		}
	});
}

function get_attendant_pump(frm){
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: 'Pump',
			filters: { 'fuel_station': frm.doc.fuel_station },
			fields: ["name"],
			order_by: 'fuel_item desc, pump_number asc'
		},
		async: false,
		callback: function (r) {
			if (r.message) {
				frm.clear_table("attendant_pump");
				r.message.forEach(d => {
					var child = frm.add_child("attendant_pump");
					frappe.model.set_value(child.doctype, child.name, "pump", d.name);
				})
				refresh_field("attendant_pump");
			}
		}
	});
}

function validate_meter_leading(frm) {
	frm.doc.pump_meter_reading.forEach((d, index) => {
		if (!d.closing_mechanical || d.closing_mechanical == 0) {
			frappe.throw(__("Row {0}:Closing Mechanical Mandatory In Pump Meter Leading Table", [d.idx]))
		}
		if (!d.closing_electrical || d.closing_electrical == 0) {
			frappe.throw(__("Row {0}:Closing Electrical Mandatory In Pump Meter Leading Table", [d.idx]))
		}
	});
}

function validate_attendant_pump(frm) {
	var total_deposited = 0
	frm.doc.attendant_pump.forEach((d, index) => {
		if (!d.cash_deposited || d.cash_deposited == 0) {
			frappe.throw(__("Row {0}:Cash Deposited Mandatory In Attendant Pump Table", [d.idx]))
		}
		if (d.cash_deposited < d.cash_to_be_deposited) {
			frappe.throw(__("Row {0}:Cash Deposited is lower than expected In Attendant Pump Table", [d.idx]))
		}
		total_deposited = total_deposited + d.cash_deposited
	});
	frappe.model.set_value(frm.doctype, frm.name, "total_deposited", total_deposited)
}

function validate_deep_reading(frm) {
	frm.doc.dip_reading.forEach((d, index) => {
		if (!d.closing_mm || d.closing_mm == 0) {
			frappe.throw(__("Row {0}:Closing MM Mandatory In Deep Reading Table", [d.idx]))
		}
	});
}

frappe.ui.form.on('Dip Reading', {
	closing_mm: function (frm, cdt, cdn) {
		var tank_doc = locals[cdt][cdn];
		if (!cur_frm.doc.fuel_station) {
			frappe.model.set_value(cdt, cdn, "closing_mm", '');
			frappe.throw(__("Select Fuel Station"))
		}
		if (!tank_doc.fuel_tank) {
			frappe.model.set_value(cdt, cdn, "closing_mm", '');
			frappe.throw(__("Select Fuel Tank"))
		}
		if (tank_doc.closing_mm) {
			frappe.call({
				method: "dsr.dsr.doctype.inspection_report.inspection_report.get_litres_from_dip_reading",
				args: { 'fuel_tank': tank_doc.fuel_tank, 'station': cur_frm.doc.fuel_station, 'dip_reading': tank_doc.closing_mm },
				callback: function (r) {
					if (r.message > 0) {
						frappe.model.set_value(cdt, cdn, "closing_liters", r.message);
					}
					else {
						frappe.model.set_value(cdt, cdn, "closing_mm", '');
						frappe.throw(__("Reading Not In Calibration Chart"))
					}
					console.log(r.message)
				}
			});
		}
	}
});

frappe.ui.form.on('Pump Meter Reading', {
	closing_electrical: function (frm, cdt, cdn) {
		calculate_sales_qty(frm, cdt, cdn)
	},
	opening_electrical: function (frm, cdt, cdn) {
		calculate_sales_qty(frm, cdt, cdn)
	},
	closing_mechanical: function (frm, cdt, cdn) {
		calculate_mechanical_difference(frm, cdt, cdn)
	},
	opening_mechanical: function (frm, cdt, cdn) {
		calculate_mechanical_difference(frm, cdt, cdn)
	},
	calculated_sales: function (frm, cdt, cdn) {
		calculate_total_sales(frm, cdt, cdn)
	}
});

function calculate_sales_qty(frm, cdt, cdn) {
	var child = locals[cdt][cdn]
	frappe.model.set_value(cdt, cdn, "calculated_sales", child.closing_electrical - child.opening_electrical)
}

function calculate_mechanical_difference(frm, cdt, cdn) {
	var child = locals[cdt][cdn]
	frappe.model.set_value(cdt, cdn, "mechanical_difference", child.closing_mechanical - child.opening_mechanical)
}

function calculate_total_sales(frm, cdt, cdn) {
	var child = locals[cdt][cdn]
	var total_sales = 0
	var total_cash_shortage = 0;
	if (child.calculated_sales && child.pump) {
		frappe.call({
			method: "dsr.dsr.doctype.shift.shift.calculate_total_sales",
			args: { 'shift': cur_frm.doc.name, 'pump': child.pump, 'total_qty': child.calculated_sales },
			callback: function (r) {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "calculated_sales_price", r.message[0])
					frm.doc.attendant_pump.forEach((d, index) => {
						if (d.pump == child.pump) {
							frappe.model.set_value(d.doctype, d.name, "cash_to_be_deposited", r.message[2])
							frappe.model.set_value(d.doctype, d.name, "cash_shortage", d.cash_to_be_deposited - d.cash_deposited)
							total_cash_shortage = total_cash_shortage + d.cash_to_be_deposited - d.cash_deposited;
							total_sales = total_sales + r.message[2];
						}
					});
				}
				frappe.model.set_value(frm.doctype, frm.name, "total_sales", total_sales)
			}
		});
	}
}

frappe.ui.form.on('Attendant Pump', {
	pump: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.pump) {
			cur_frm.doc.attendant_pump.forEach((d, index) => {
				if (d.pump == child.pump && d.name != child.name) {
					frappe.model.set_value(child.doctype, child.name, "pump", "")
					frappe.throw(__("Pump {0} Already Assign {1} In Row {2}", [d.pump, d.attendant, d.idx]))
				}
			});
		}
	},
	cash_deposited: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		console.log('call')
		var total_deposited = 0;
		var total_cash_shortage = 0;
		if (child.cash_deposited) {
			cur_frm.doc.attendant_pump.forEach((d, index) => {
					frappe.model.set_value(d.doctype, d.name, "cash_shortage", d.cash_to_be_deposited - d.cash_deposited)
					total_deposited = total_deposited + d.cash_deposited;
					total_cash_shortage = total_cash_shortage + d.cash_to_be_deposited - d.cash_deposited;
				
			});
		}
		frappe.model.set_value(cur_frm.doc.doctype,cur_frm.doc.name, "total_deposited", total_deposited)
		refresh_field("total_deposited")
		frappe.model.set_value(cur_frm.doc.doctype,cur_frm.doc.name, "total_cash_shortage", total_cash_shortage)
		refresh_field("total_cash_shortage")
	}
});
