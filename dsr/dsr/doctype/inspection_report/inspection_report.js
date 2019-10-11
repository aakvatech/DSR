// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inspection Report', {
	onload: function(frm,cdt,cdn) {
        if(frm.doc.__islocal){
            frappe.model.set_value(cdt,cdn,"inspected_by",frappe.session.user)
    		frappe.call({
    			method: "frappe.client.get_list",
    			args: {
    				doctype: "Inspection Report",
    				fields: ["owner","inspection_date"],
    				order_by: "inspection_date desc",
    				limit_page_length: 1
					},
				async: false,
    			callback: function (r) {
    			    if(r.message.length > 0){
    				    frappe.model.set_value(cdt,cdn,"last_inspection_by",r.message[0].owner)
    				    frappe.model.set_value(cdt,cdn,"last_inspection_date",r.message[0].inspection_date)
    				}
    			}
			});
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
		console.log(doc.fuel_station)
	    if(doc.fuel_station){
	        frappe.call({
	            method:"frappe.client.get_list",
	            args:{
	                doctype:'Fuel Tank',
	                filters:{'fuel_station':doc.fuel_station},
	                fields:["name","tank_capacity"]
				},
				async: false,
	            callback:function(r){
					frm.clear_table("inspection_report_tank");
	                r.message.forEach(d => {
                        var child = frm.add_child("inspection_report_tank")
                        frappe.model.set_value(child.doctype,child.name,"fuel_tank",d.name);
                        frappe.model.set_value(child.doctype,child.name,"tank_capacity",d.tank_capacity);
	                })
	                refresh_field("inspection_report_tank");
	            }
	        })
	        frappe.call({
	            method:"frappe.client.get_list",
	            args:{
	                doctype:'Pump',
	                filters:{'fuel_station':doc.fuel_station},
	                fields:["name"]
				},
				async: false,
	            callback:function(r){
					frm.clear_table("inspection_report_dispenser");
	                r.message.forEach(d => {
	                    var child = frm.add_child("inspection_report_dispenser");
	                   frappe.model.set_value(child.doctype,child.name,"pump",d.name);
	                })
	                refresh_field("inspection_report_dispenser");

	            }
			})
	        frappe.call({
	            method:"frappe.client.get_list",
	            args:{
	                doctype:'Fuel Station',
	                filters:{'name':doc.fuel_station},
	                fields:["name","station_manager"]
				},
				async: false,
	            callback:function(r){
					if(r.message){ 
	                frappe.model.set_value(cdt,cdn,"manager_name",r.message[0].station_manager)
					}
	            }
	        })
	    }
	},
	shift:function(frm,cdt,cdn){
		if(!frm.doc.shift){
			console.log('shift')
			frappe.model.set_value(cdt,cdn,"fuel_station",'');
			frm.clear_table("inspection_report_tank");
			frm.clear_table("inspection_report_dispenser");
			refresh_field("inspection_report_dispenser");
			refresh_field("inspection_report_tank");


		}

	}
});

frappe.ui.form.on('Inspection Report Tank', {
	current_dip_reading: function(frm,cdt,cdn) {
		var tank_doc = locals[cdt][cdn];
		if(!cur_frm.doc.fuel_station){
			frappe.model.set_value(cdt,cdn,"current_dip_reading",'');
			frappe.throw(__("Select Fuel Station"))
		}
		if(!tank_doc.fuel_tank){
			frappe.model.set_value(cdt,cdn,"current_dip_reading",'');
			frappe.throw(__("Select Fuel Tank"))
		}
		if (tank_doc.current_dip_reading){
			frappe.call({
				method:"dsr.dsr.doctype.inspection_report.inspection_report.get_litres_from_dip_reading",
				args:{'fuel_tank':tank_doc.fuel_tank,'station':cur_frm.doc.fuel_station,'dip_reading':tank_doc.current_dip_reading},
				callback:function(r){
					if (r.message > 0){
						frappe.model.set_value(cdt,cdn,"current_ltrs",r.message);
					}
					else{
						frappe.model.set_value(cdt,cdn,"current_dip_reading",'');
						frappe.throw(__("Reading Not In Calibration Chart"))
					}
					console.log(r.message)
				}
			})
		}

	}

})