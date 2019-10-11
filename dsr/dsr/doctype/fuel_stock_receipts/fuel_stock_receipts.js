// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fuel Stock Receipts', {
	onload: function(frm,cdt,cdn) {
        if(frm.doc.__islocal){
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
	},
	fuel_station:function(frm,cdt,cdn){
		var doc = locals[cdt][cdn];
	    if(doc.fuel_station){
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
	},
	fuel_item:function(frm,cdt,cdn){
		var doc = locals[cdt][cdn];
	    if(doc.fuel_item){
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
		
	},
	actual_quantity:function(frm,cdt,cdn){
		if(frm.doc.quantity_as_per_dn){
			frappe.model.set_value(cdt,cdn,"fuel_shortage",parseFloat(frm.doc.quantity_as_per_dn)-parseFloat(frm.doc.actual_quantity))
		}
	},
	quantity_as_per_dn:function(frm,cdt,cdn){
		if(frm.doc.actual_quantity && frm.doc.quantity_as_per_dn){
		frappe.model.set_value(cdt,cdn,"fuel_shortage",parseFloat(frm.doc.quantity_as_per_dn)-parseFloat(frm.doc.actual_quantity))
	}
}

});


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

		cur_frm.set_value("actual_quantity",tank_doc.difference_ltrs)
	
	}


})
