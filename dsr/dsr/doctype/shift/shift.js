// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shift', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('Dip Reading', {
	closing_mm: function(frm,cdt,cdn) {
		var tank_doc = locals[cdt][cdn];
		if(!cur_frm.doc.fuel_station){
			frappe.model.set_value(cdt,cdn,"closing_mm",'');
			frappe.throw(__("Select Fuel Station"))
		}
		if(!tank_doc.fuel_tank){
			frappe.model.set_value(cdt,cdn,"closing_mm",'');
			frappe.throw(__("Select Fuel Tank"))
		}
		if (tank_doc.closing_mm){
			frappe.call({
				method:"dsr.dsr.doctype.inspection_report.inspection_report.get_litres_from_dip_reading",
				args:{'fuel_tank':tank_doc.fuel_tank,'station':cur_frm.doc.fuel_station,'dip_reading':tank_doc.closing_mm},
				callback:function(r){
					if (r.message > 0){
						frappe.model.set_value(cdt,cdn,"closing_liters",r.message);
					}
					else{
						frappe.model.set_value(cdt,cdn,"closing_mm",'');
						frappe.throw(__("Reading Not In Calibration Chart"))
					}
					console.log(r.message)
				}
			})
		}

	}

})
