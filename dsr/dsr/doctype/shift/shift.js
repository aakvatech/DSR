// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shift', {
	before_submit: (frm) => {
		validate_unsubmitted_documents(frm)
		validate_cash_discounted_pending(frm)
		validate_meter_reading(frm)
		validate_attendant_pump(frm)
		validate_dip_reading(frm)
		validate_generator_reading(frm)
	},
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
		if (frappe.user_roles.includes("Cluster Manager")) {
			console.log("Special access granted to " + frappe.session.user)
			// Assume that the user is allowed to update pump detials 
			frm.set_df_property("pump_meter_reading", "read_only", false);
			frm.set_df_property("attendant_pump", "read_only", false);
			frm.set_df_property("dip_reading", "read_only", false);
			frappe.meta.get_docfield("Pump Meter Reading", "pump", frm.doc.name).read_only = 0;
		}
		if (frappe.user_roles.includes("System Manager")) {
			console.log("Super Special access granted to " + frappe.session.user)
			// Assume that the user is allowed to update pump detials 
			frm.set_df_property("opening_balance", "read_only", false);
			frm.set_df_property("cash_in_hand", "read_only", false);
			frm.set_df_property("pump_meter_reading", "read_only", false);
			frm.set_df_property("attendant_pump", "read_only", false);
			frm.set_df_property("dip_reading", "read_only", false);
			frappe.meta.get_docfield("Pump Meter Reading", "pump", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Pump Meter Reading", "pump", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Pump Meter Reading", "opening_mechanical", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Pump Meter Reading", "closing_mechanical", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Pump Meter Reading", "opening_electrical", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Pump Meter Reading", "closing_electrical", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Attendant Pump", "pump", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Dip Reading", "fuel_tank", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Dip Reading", "opening_mm", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Dip Reading", "opening_liters", frm.doc.name).read_only = 0;
		}
		refresh_field("shift_fuel_item_totals");
	},

	get_last_shift_details:function(frm){
		if(!frm.doc.fuel_station){
			frappe.throw(__("Fuel Station Required For Loading Last Shift Details"))
		}
		get_last_shift_data(frm)
	},
	close_shift: (frm) => {
		validate_unsubmitted_documents(frm)
		validate_cash_discounted_pending(frm)
		validate_meter_reading(frm)
		validate_attendant_pump(frm)
		validate_dip_reading(frm)
		validate_generator_reading(frm)
		frappe.call({
			method: "dsr.dsr.doctype.shift.shift.close_shift",
			args: { 'name': frm.doc.name, 'status': 'Closed' },
			callback: function (r) {
				cur_frm.reload_doc()
			}
		});
	},
	fuel_station: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.fuel_station) {
			if(frm.doc.__islocal){
				validate_close_shift(frm)
			}
			get_dip_reading(frm)
			get_pump_meter_reading(frm)
			get_last_shift_data(frm)
			get_attendant_pump(frm)
		}
	},
	validate: function(frm,cdt,cdn){
		// frappe.msgprint("Validate fired")
		var child = locals[cdt][cdn];
		var calculated_sales = 0;
		child.pump_meter_reading.forEach((d, index) => {
			calculated_sales = 0;
			frappe.model.set_value(d.doctype, d.name, "calculated_sales", calculated_sales)
			calculated_sales = d.closing_electrical - d.opening_electrical;
			frappe.model.set_value(d.doctype, d.name, "calculated_sales", calculated_sales)
			// console.log(d.pump, calculated_sales);
		});
		refresh_field("attendance_pump");
		calculate_other_sales_totals(frm);
	},
	closing_generator_hours: function(frm) {
		if (frm.doc.generator_hours || frm.doc.generator_hours == 0) {
			if (frm.doc.closing_generator_hours < frm.doc.generator_hours) {
				frm.set_value("generator_operation_hours", 0)
				frm.set_value("closing_generator_hours", 0)
				frm.set_value("estimated_generator_expense", 0)
				frappe.throw(__("Closing generator hours cannot be less than opening generator hours"))
			}
			else {
				frm.set_value("generator_operation_hours", frm.doc.closing_generator_hours - frm.doc.generator_hours)
				calculate_generator_expense(frm)
			}
		}
	},
	setup: function(frm) {
		// console.log(frm)
		frm.set_query('pump', 'pump_meter_reading', function(doc, cdt, cdn) {
			return {
				filters: {
					'fuel_station': doc.fuel_station
				}
			}
		});
		frm.set_query('pump', 'attendant_pump', function(doc, cdt, cdn) {
			return {
				filters: {
					'fuel_station': doc.fuel_station
				}
			}
		});
		frm.set_query('attendant', 'attendant_pump', function(doc, cdt, cdn) {
			return {
				filters: {
					'fuel_station': doc.fuel_station
				}
			}
		});
		frm.set_query('fuel_tank', 'dip_reading', function(doc, cdt, cdn) {
			return {
				filters: {
					'fuel_station': doc.fuel_station
				}
			}
		});
	}
});

function get_last_shift_data(frm){
	frappe.call({
		method:"dsr.dsr.doctype.shift.shift.get_last_shift_data",
		args:{
			fuel_station:frm.doc.fuel_station
		},
		async: false,
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
					frappe.model.set_value(child.doctype, child.name, "opening_liters", d.closing_liters)
				});
				refresh_field("dip_reading")
				frm.set_value("opening_balance", 0);
				if(r.message.cash_in_hand) {
					frm.set_value("opening_balance", r.message.cash_in_hand);
				}
				refresh_field("opening_balance")
				frm.set_value("generator_hours", r.message.generator_operation_hours)
				refresh_field("generator_hours")
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
		async: false,
		callback:function(r)
		{
			if(r.message.length >= 1){
				frm.set_value("fuel_station", "")
				refresh_field("fuel_station")
				frappe.throw(__("{0} is not yet closed",[r.message[0].name]))
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

function validate_meter_reading(frm) {
	frm.doc.pump_meter_reading.forEach((d, index) => {
		if (!d.closing_mechanical || d.closing_mechanical == 0) {
			frappe.throw(__("Row {0}: Missing Closing Mechanical Mandatory In Pump Meter Reading Table for {1}", [d.idx, d.pump]))
		}
		if (!d.closing_electrical || d.closing_electrical == 0) {
			frappe.throw(__("Row {0}: Missing Closing Electrical Mandatory In Pump Meter Reading Table for {1}", [d.idx, d.pump]))
		}
	});
}

function validate_attendant_pump(frm) {
	frm.doc.attendant_pump.forEach((d, index) => {
		// console.log(d.cash_deposited, d.cash_to_be_deposited, d.cash_shortage)
		if (!d.cash_deposited && d.cash_deposited != 0) {
			frappe.throw(__("Row {0}: Cash Deposited Mandatory In Attendant Pump Table for {2}. The amount is recorded is {1}.", [d.idx, d.cash_deposited, d.attendant]))
		}
		if (d.cash_shortage > 0) {
			frappe.throw(__("Row {0}: Cash Deposited is lower than expected In Attendant Pump Table for {2}. The shortage is {1}", [d.idx, d.cash_shortage, d.attendant]))
		}
	});
}

function validate_dip_reading(frm) {
	frm.doc.dip_reading.forEach((d, index) => {
		if (!d.closing_mm || d.closing_mm == 0) {
			frappe.throw(__("Row {0}: Closing MM Mandatory In Dip Reading Table for {1}", [d.idx, d.fuel_tank]))
		}
	});
}

function validate_generator_reading(frm) {
	if (!frm.doc.closing_generator_hours || frm.doc.closing_generator_hours == 0) {
		frappe.throw(__("Closing Generator Hours is Mandatory. Please enter Closing Generator Hours"))
	}
}

// Check if there are any credit sales pending to be posted or with cash_discounted not full paid
function validate_cash_discounted_pending(frm) {
	frappe.call({
		method:"frappe.client.get_list",
		args:{
			doctype: 'Credit Sales',
			filters: {'shift': frm.doc.shift,'discounted_cash_customer':1,'full_paid':0},
			fields:["name"],
			limit: 1
		},
		async: false,
		callback:function(r)
		{
			if(r.message.length >= 1){
				frappe.throw(__("<a href=#Form/Credit%20Sales/{0}>{0}</a> is not fully paid yet! Please confirm that the monies are fully paid by reviewing the document.",[r.message[0].name]))
			}
		}
	});
}

// Check if the Disbursed for Office use or Fuel Stock receipts are pending submission
function validate_unsubmitted_documents(frm) {
	frappe.call({
		method:"frappe.client.get_list",
		args:{
			doctype: 'Credit Sales',
			filters: {'shift': frm.doc.name, 'docstatus':0},
			fields:["name"]
		},
		async: false,
		callback:function(r)
		{
			if(r.message.length >= 1){
				frappe.throw(__("Credit Sales <a href=#Form/Credit%20Sales/{0}>{0}</a> is not submitted yet! Please submit the document",[r.message[0].name]))
			}
		}
	});
	frappe.call({
		method:"frappe.client.get_list",
		args:{
			doctype: 'Dispensed for Office Use',
			filters: {'shift': frm.doc.name, 'docstatus':0},
			fields:["name"]
		},
		async: false,
		callback:function(r)
		{
			if(r.message.length >= 1){
				frappe.throw(__("Dispensed for Office Use <a href=#Form/Dispensed%20for%20Office%20Use/{0}>{0}</a> is not submitted yet! Please submit the document",[r.message[0].name]))
			}
		}
	});
	frappe.call({
		method:"frappe.client.get_list",
		args:{
			doctype: 'Fuel Stock Receipts',
			filters: {'shift': frm.doc.name, 'docstatus':0},
			fields:["name"]
		},
		async: false,
		callback:function(r)
		{
			if(r.message.length >= 1){
				frappe.throw(__("Fuel Stock Receipts <a href=#Form/Fuel%20Stock%20Receipts/{0}>{0}</a> is not submitted yet! Please submit the document",[r.message[0].name]))
			}
		}
	});
	frappe.call({
		method:"frappe.client.get_list",
		args:{
			doctype: 'Cash Deposited',
			filters: {'shift': frm.doc.name, 'docstatus':0},
			fields:["name"]
		},
		async: false,
		callback:function(r)
		{
			if(r.message.length >= 1){
				frappe.throw(__("Cash Deposited <a href=#Form/Cash%20Deposited/{0}>{0}</a> is not submitted yet! Please submit the document",[r.message[0].name]))
			}
		}
	});
	frappe.call({
		method:"frappe.client.get_list",
		args:{
			doctype: 'Expense Record',
			filters: {'shift': frm.doc.name, 'docstatus':0},
			fields:["name"]
		},
		async: false,
		callback:function(r)
		{
			if(r.message.length >= 1){
				frappe.throw(__("Expense Record <a href=#Form/Expense%20Record/{0}>{0}</a> is not submitted yet! Please submit the document",[r.message[0].name]))
			}
		}
	});
	frappe.call({
		method:"frappe.client.get_list",
		args:{
			doctype: 'Inspection Report',
			filters: {'shift': frm.doc.name, 'docstatus':0},
			fields:["name"]
		},
		async: false,
		callback:function(r)
		{
			if(r.message.length >= 1){
				frappe.throw(__("Inspection Report <a href=#Form/Inspection%20Report/{0}>{0}</a> is not submitted yet! Please submit the document",[r.message[0].name]))
			}
		}
	});
}

// Calculate number of hours 
function calculate_generator_expense(frm) {
	var avg_consump = 0;
	frappe.call({
		method:"frappe.client.get_value",
		args:{
			'doctype':"Fuel Station",
			'filters':{'name': frm.doc.fuel_station},
			'fieldname':[
				'average_generator_fuel_consumption_per_hour'
			]
		},
		async: false,
		callback: function (data) {
			// console.log(data);
			if(data.message) {
				avg_consump = data.message.average_generator_fuel_consumption_per_hour;
			}
		}
	});
	var item_rate = 0;
	frappe.call({
		method:"frappe.client.get_value",
		args:{
			'doctype':"Fuel Item",
			'filters':{'name': frm.doc.fuel_station + "-Diesel"},
			'fieldname':[
				'mera_wholesale_price'
			]
		},
		async: false,
		callback: function (data) {
			if(data.message) {
				item_rate = data.message.mera_wholesale_price;
			}
		}
	});
	frm.set_value("estimated_generator_expense", avg_consump * item_rate * frm.doc.generator_operation_hours);
}

frappe.ui.form.on('Dip Reading', {
	closing_mm: function (frm, cdt, cdn) {
		var tank_doc = locals[cdt][cdn];
		if (!frm.doc.fuel_station) {
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
				args: { 'fuel_tank': tank_doc.fuel_tank, 'station': frm.doc.fuel_station, 'dip_reading': tank_doc.closing_mm },
				callback: function (r) {
					if (r.message > 0) {
						frappe.model.set_value(cdt, cdn, "closing_liters", r.message);
					}
					else {
						frappe.model.set_value(cdt, cdn, "closing_mm", '');
						frappe.throw(__("Reading Not In Calibration Chart"))
					}
				}
			});
		}
	},
	closing_liters:function(frm,cdt,cdn){
		var doc = locals[cdt][cdn]
		frappe.model.set_value(cdt,cdn,"difference_in_liters",parseFloat(doc.closing_liters)-parseFloat(doc.opening_liters))
	},

	
	
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
		var child = locals[cdt][cdn]
		// console.log(child.pump, child.calculated_sales)
		calculate_total_sales(frm, cdt, cdn)
	},
});

function calculate_sales_qty(frm, cdt, cdn) {
	var child = locals[cdt][cdn]
	if (child.closing_electrical) {
		frappe.model.set_value(cdt, cdn, "calculated_sales", child.closing_electrical - child.opening_electrical)
	}	
}

function calculate_mechanical_difference(frm, cdt, cdn) {
	var child = locals[cdt][cdn]
	frappe.model.set_value(cdt, cdn, "mechanical_difference", child.closing_mechanical - child.opening_mechanical)
}

function calculate_total_sales(frm, cdt, cdn) {
	// frappe.msgprint("Inside Calculated Total Sales")
	var child = locals[cdt][cdn]
	var total_credit_sales = 0;
	if (child.pump) {
		frappe.call({
			method: "dsr.dsr.doctype.shift.shift.calculate_total_sales",
			args: { 'shift': frm.doc.name, 'pump': child.pump, 'total_qty': child.calculated_sales },
			async: false,
			callback: function (r) {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "calculated_sales_price", Number((r.message[0]).toFixed(2)))
					frm.doc.attendant_pump.forEach((d, index) => {
						if (d.pump == child.pump) {
							frappe.model.set_value(d.doctype, d.name, "cash_to_be_deposited", Number((r.message[2]).toFixed(2)))
							frappe.model.set_value(d.doctype, d.name, "cash_shortage", d.cash_to_be_deposited - d.cash_deposited)
							frappe.model.set_value(d.doctype, d.name, "credit_sales", Number((r.message[1]).toFixed(2)))
						}
					});
				}
			}
		});
		refresh_field("attendant_pump")
	}
	calculate_attendant_deposit_totals(frm)
}

function calculate_attendant_deposit_totals(frm) {
	var total_cash_sales_to_be_deposited = 0;
	var total_deposited = 0;
	var total_cash_shortage = 0;
	var total_credit_sales = 0;

	frm.doc.attendant_pump.forEach((d, index) => {
		frappe.model.set_value(d.doctype, d.name, "cash_shortage", d.cash_to_be_deposited - d.cash_deposited)
		total_deposited = total_deposited + d.cash_deposited;
		total_cash_sales_to_be_deposited = total_cash_sales_to_be_deposited + d.cash_to_be_deposited;
		total_cash_shortage = total_cash_shortage + d.cash_to_be_deposited - d.cash_deposited;
		total_credit_sales = total_credit_sales + d.credit_sales
		// console.log(total_credit_sales, d.pump)
	});
	refresh_field("attendant_pump")
	frm.set_value("total_cash_sales_to_be_deposited", total_cash_sales_to_be_deposited)
	refresh_field("total_cash_sales_to_be_deposited")
	frm.set_value("total_deposited", total_deposited)
	refresh_field("total_deposited")
	frm.set_value("total_cash_shortage", total_cash_shortage)
	refresh_field("total_cash_shortage")
	frm.set_value("total_credit_sales", total_credit_sales)
	refresh_field("total_credit_sales")
}

frappe.ui.form.on('Attendant Pump', {
	pump: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.pump) {
			frm.doc.attendant_pump.forEach((d, index) => {
				if (d.pump == child.pump && d.name != child.name) {
					frappe.model.set_value(child.doctype, child.name, "pump", "")
					frappe.throw(__("Pump {0} Already Assign {1} In Row {2}", [d.pump, d.attendant, d.idx]))
				}
			});
		}
	},
	cash_deposited: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		// if (child.pump) {
		// 	frm.doc.attendant_pump.forEach((d, index) => {
		// 		if (d.name == child.name) {
		// 			frappe.model.set_value(child.doctype, child.name, "cash_deposited", Number(d.cash_deposited))
		// 			refresh_field("cash_deposited", d.name, d.parentfield);
		// 		}
		// 	});
		// }
		if (child.cash_to_be_deposited - child.cash_deposited != 0) {
			var cash_difference = child.cash_to_be_deposited - child.cash_deposited;
			if (cash_difference < -1000 || cash_difference > 1000) {
				frappe.model.set_value(child.doctype, child.name, "cash_deposited", 0)
				frappe.throw(__("Cash deposited for " + child.attendant + " for pump " + child.pump + " cannot be so different than cash to be deposited. Please counter check the cash deposited."))
			}
		}
		calculate_attendant_deposit_totals(frm)
	}
});

function calculate_other_sales_totals(frm) {
	calculate_attendant_deposit_totals(frm)

	frappe.call({
		method: "dsr.dsr.doctype.shift.shift.get_total_retail_banking",
		args: { 'shift': frm.doc.name },
		async: false,
		callback: function (r) {
			// console.log(r.message)
			if (r.message) {
				frm.set_value("total_bank_deposit", r.message)
				// console.log(frm.doc.total_bank_deposit)
			}
		}
	});
	refresh_field("total_bank_deposit")

	frappe.call({
		method: "dsr.dsr.doctype.shift.shift.get_total_expenses",
		args: { 'shift': frm.doc.name },
		async: false,
		callback: function (r) {
			// console.log(r.message)
			if (r.message) {
				frm.set_value("total_expenses", r.message)
				// console.log(frm.doc.total_expenses)
			}
		}
	});
	refresh_field("total_expenses")

	// console.log('cih',cash_in_hand, 'ob', frm.doc.opening_balance, 'td', frm.doc.total_deposited, 'cs', frm.doc.total_cash_shortage, 'tbd', frm.doc.total_bank_deposits, 'te', frm.doc.total_expenses)
	var cash_in_hand = (frm.doc.opening_balance || 0) + (frm.doc.total_deposited || 0) - (frm.doc.total_bank_deposit || 0) - (frm.doc.total_expenses || 0);
	frm.set_value("cash_in_hand", cash_in_hand)
	refresh_field("cash_in_hand")
}

/**
 * Returns true if list_a is subset of list_b
 * @param {Array} list_a
 * @param {Array} list_b
 */
function is_subset(list_a, list_b) {
	
	return list_a.every(item => list_b.includes(item));
}