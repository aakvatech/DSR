// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fuel Stock Receipts', {
	setup: function(frm) {
		frm.set_query('fuel_item', function() {
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
        if(frm.doc.__islocal){
			auto_shift_selection(frm,cdt,cdn)
		};
		validate_difference_ltrs_reading(frm)
	},
	refresh: function(frm) {
        if(frm.doc.fuel_station){
			validate_actual_quantity_reading(frm)
        };
	},
	fuel_station:function(frm,cdt,cdn) {
	    if(frm.doc.fuel_station){
			get_fuel_tank(frm,cdt,cdn)
		}
	},
	fuel_item:function(frm,cdt,cdn) {
	    if(frm.doc.fuel_item) {
			get_fuel_tank(frm,cdt,cdn)
		}
		
	},
	actual_quantity:function(frm,cdt,cdn) {
		if(frm.doc.quantity_as_per_dn){
			frappe.model.set_value(cdt,cdn,"fuel_shortage",parseFloat(frm.doc.quantity_as_per_dn)-parseFloat(frm.doc.actual_quantity))
		}
	},
	quantity_as_per_dn:function(frm,cdt,cdn) {
		if(frm.doc.actual_quantity && frm.doc.quantity_as_per_dn) {
			frappe.model.set_value(cdt,cdn,"fuel_shortage",parseFloat(frm.doc.quantity_as_per_dn)-parseFloat(frm.doc.actual_quantity))
		}
	}
});

function validate_actual_quantity_reading(frm){

	frappe.db.get_value('Fuel Station', {'name': frm.doc.fuel_station}, 'allow_change_of_dip_balance', (r) => {
		var message = r.allow_change_of_dip_balance;
		if (message == 1){
			frm.set_df_property("actual_quantity", "read_only", false);
		}
		else {
			frm.set_df_property("actual_quantity", "read_only", true);
		}
		refresh_field("actual_quantity");
	});

}

function validate_difference_ltrs_reading(frm){
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: 'Fuel Station',
			fieldname: 'allow_change_of_dip_balance',
			filters: {name: frm.doc.fuel_station},
			},
		async: false,
		callback: function (r) {
			var message = r.message.allow_change_of_dip_balance;
			if (message == 1){
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks","difference_ltrs",frm.doc.name).in_list_view = 1;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "before_mm", frm.doc.name).in_list_view = 0
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "after_mm", frm.doc.name).in_list_view = 0
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "difference_ltrs", frm.doc.name).read_only = 0;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "before_mm", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "before_ltrs", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "after_mm", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "after_ltrs", frm.doc.name).read_only = 1;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "before_mm", frm.doc.name).hidden = 1;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "before_ltrs", frm.doc.name).hidden = 1;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "after_mm", frm.doc.name).hidden = 1;
			frappe.meta.get_docfield("Fuel Stock Receipt Tanks", "after_ltrs", frm.doc.name).hidden = 1;
			refresh_field("fuel_stock_receipt_tanks");
			}
		}
	});
}

//get fuel tank item and fuel station
function get_fuel_tank(frm,cdt,cdn){
	var doc = locals[cdt][cdn]
	if(doc.fuel_station && doc.fuel_item){
		frappe.call({
			method:"frappe.client.get_list",
			args:{
				doctype:'Fuel Tank',
				filters:{'fuel_station':doc.fuel_station,'fuel_item':doc.fuel_item},
				fields:["name"]
			},
			async: false,
			callback:function(r){
				frm.clear_table("fuel_stock_receipt_tanks");
				r.message.forEach(d => {
					var child = frm.add_child("fuel_stock_receipt_tanks")
					frappe.model.set_value(child.doctype,child.name,"fuel_tank",d.name);	                })
				refresh_field("fuel_stock_receipt_tanks");
			}
		})
	}
}

//onload shift auto selection
function auto_shift_selection(frm,cdt,cdn){
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Shift",
			fields: ["name","fuel_station"],
			order_by: "creation desc",
			limit_page_length: 1
			},
		async: false,
		callback: function (r) {
			if(r.message){
				console.log(r.message)
				frappe.model.set_value(cdt,cdn,"shift",r.message[0].name)
				frappe.model.set_value(cdt,cdn,"fuel_station",r.message[0].fuel_station)
			}
		}
	});  
}

frappe.ui.form.on('Fuel Stock Receipt Tanks', {
	before_mm: function(frm,cdt,cdn) {
		var tank_doc = locals[cdt][cdn];
		if(!cur_frm.doc.fuel_station){
			frappe.model.set_value(cdt,cdn,"before_mm",'');
			frappe.throw(__("Select Fuel Station"))
		}
		if(!tank_doc.fuel_tank){
			frappe.model.set_value(cdt,cdn,"before_mm",'');
			frappe.throw(__("Select Fuel Tank"))
		}
		if (tank_doc.before_mm){
			frappe.call({
				method:"dsr.dsr.doctype.inspection_report.inspection_report.get_litres_from_dip_reading",
				args:{'fuel_tank':tank_doc.fuel_tank,'station':cur_frm.doc.fuel_station,'dip_reading':tank_doc.before_mm},
				callback:function(r){
					if (r.message > 0){
						frappe.model.set_value(cdt,cdn,"before_ltrs",r.message);
					}
					else{
						frappe.model.set_value(cdt,cdn,"before_mm",'');
						frappe.throw(__("Reading Not In Calibration Chart"))
					}
					console.log(r.message)
				}
			})
		}
	},
	after_mm: function(frm,cdt,cdn) {
		var tank_doc = locals[cdt][cdn];
		if(!cur_frm.doc.fuel_station){
			frappe.model.set_value(cdt,cdn,"after_mm",'');
			frappe.throw(__("Select Fuel Station"))
		}
		if(!tank_doc.fuel_tank){
			frappe.model.set_value(cdt,cdn,"after_mm",'');
			frappe.throw(__("Select Fuel Tank"))
		}
		if (tank_doc.after_mm){
			frappe.call({
				method:"dsr.dsr.doctype.inspection_report.inspection_report.get_litres_from_dip_reading",
				args:{'fuel_tank':tank_doc.fuel_tank,'station':cur_frm.doc.fuel_station,'dip_reading':tank_doc.after_mm},
				callback:function(r){
					if (r.message > 0){
						frappe.model.set_value(cdt,cdn,"after_ltrs",r.message);
					}
					else{
						frappe.model.set_value(cdt,cdn,"after_mm",'');
						frappe.throw(__("Reading Not In Calibration Chart"))
					}
					console.log(r.message)
				}
			})
		}
	},
	after_ltrs:function(frm,cdt,cdn){
		var tank_doc = locals[cdt][cdn];
		if(tank_doc.before_ltrs && tank_doc.after_ltrs){
		frappe.model.set_value(cdt,cdn,"difference_ltrs",tank_doc.after_ltrs-tank_doc.before_ltrs);
		}
	},
	before_ltrs:function(frm,cdt,cdn){
		var tank_doc = locals[cdt][cdn];
		if(tank_doc.before_ltrs && tank_doc.after_ltrs){
		frappe.model.set_value(cdt,cdn,"difference_ltrs",tank_doc.after_ltrs-tank_doc.before_ltrs);
		}
	},
	difference_ltrs:function(frm,cdt,cdn){
		var tank_doc = locals[cdt][cdn];
		var total = 0
		cur_frm.doc.fuel_stock_receipt_tanks.forEach((d, index) => {
			if(d.difference_ltrs){
			total += d.difference_ltrs
			}
		});
		frappe.model.set_value(cur_frm.doc.doctype,cur_frm.doc.name,"actual_quantity",parseFloat(total));
		cur_frm.refresh_fields()
	}
})
