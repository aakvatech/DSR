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
    			callback: function (r) {
    			    if(r.message){
    				    console.log(r.message[0].owner)
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
    			callback: function (r) {
    			    if(r.message){
    				    frappe.model.set_value(cdt,cdn,"shift",r.message[0].name)
    				    frappe.model.set_value(cdt,cdn,"fuel_station",r.message[0].fuel_station)

    				}
    			}
    		});    		

        }
	},
	fuel_station:function(frm,cdt,cdn){
	    var doc = locals[cdt][cdn]
	    if(doc.fuel_station){
	        frappe.call({
	            method:"frappe.client.get_list",
	            args:{
	                doctype:'Fuel Tank',
	                filters:{'fuel_station':doc.fuel_station},
	                fields:["name","tank_capacity"]
	            },
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
	            callback:function(r){
	                frm.clear_table("inspection_report_dispenser");
	                r.message.forEach(d => {
	                    var child = frm.add_child("inspection_report_dispenser");
	                   frappe.model.set_value(child.doctype,child.name,"pump",d.name);
	                })
	                refresh_field("inspection_report_dispenser");

	            }
	        })
	    }
	}
});