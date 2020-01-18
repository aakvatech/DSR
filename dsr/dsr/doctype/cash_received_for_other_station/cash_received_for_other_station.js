// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt
frappe.ui.form.on('Cash Received For Other Station', {
	onload: function(frm,cdt,cdn) {
		auto_shift_selection(frm,cdt,cdn)
	},
	fuel_item: function(frm,cdt,cdn){
		if(frm.doc.fuel_item) {
			erpnext.utils.copy_value_in_all_rows(frm.doc, frm.doc.doctype, frm.doc.name, "other_station_credit", "fuel_item");
		}

	},
	setup:function(frm,cdt,cdn){
		frm.set_query('shift', function() {
			return {
				filters: {
					'shift_status': 'Open'
				}
			}
		});
		frm.set_query('for_fuel_station', function() {
			return {
				query: "dsr.custom_api.get_all_fuel_stations"
			};
		});
	}
});

frappe.ui.form.on('Other Station Credit', {
	fuel_item:function(frm,cdt,cdn){
		set_rate(frm,cdt,cdn)

	},
	truck_number:function(frm,cdt,cdn){
		validate_truck_duplication(frm,cdt,cdn)
		set_rate(frm,cdt,cdn)

	},
	quantity:function(frm,cdt,cdn){
		calculate_amount(frm,cdt,cdn)
	},
	rate:function(frm,cdt,cdn){
		calculate_amount(frm,cdt,cdn)
	},
	other_station_credit_add: function(frm, cdt, cdn) {
		var doc = frappe.get_doc(cdt, cdn);
		frm.script_manager.copy_from_first_row("other_station_credit", doc, ["fuel_item"]);
		
	},
	other_station_credit_remove: function(frm,cdt,cdn){
		// console.log('delete')
		calculate_total(cur_frm)
	}


})

var auto_shift_selection = function(frm, cdt, cdn) {
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
					// console.log(r.message)
					frappe.model.set_value(cdt, cdn, "shift", r.message[0].name)
					frappe.model.set_value(cdt, cdn, "date", r.message[0].date)
					frappe.model.set_value(cdt, cdn, "fuel_station", r.message[0].fuel_station)

				}
			}
		});
	}

}

var validate_truck_duplication = function(frm,cdt,cdn){
	var doc = locals[cdt][cdn]
	frm.doc.other_station_credit.forEach((d) => {
		if(d.truck_number == doc.truck_number && d.name != doc.name){
			frappe.throw(__("Duplicate Truck Selection. Truck {0} Is Already Selected In Row {1}").format(d.truck_number,d.idx))
		}

	})
}

var set_rate = function(frm,cdt,cdn){
	var doc = locals[cdt][cdn]
	frappe.model.get_value('Fuel Item', {'name': doc.fuel_item}, 'station_retail_price',
	function(data) {
		if(data.station_retail_price){
			frappe.model.set_value(cdt,cdn,"rate",data.station_retail_price)
		}
	}
);

}

var calculate_amount = function(frm,cdt,cdn){
	var doc = locals[cdt][cdn]
	if (doc.quantity && doc.rate){
		frappe.model.set_value(cdt,cdn,"amount",doc.quantity*doc.rate)
		calculate_total(cur_frm)
	}
}

var calculate_total = function(frm){
	// console.log(frm.doc.other_station_credit)
	var total_amount = 0
	var total_qty = 0
	frm.doc.other_station_credit.forEach((d) => {
		total_amount += d.amount
		total_qty += d.quantity

	})
	frappe.model.set_value(frm.doc.doctype,frm.doc.name,"total_quantity",total_qty)
	frappe.model.set_value(frm.doc.doctype,frm.doc.name,"total_amount",total_amount)


}
