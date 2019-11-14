// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fuel Tank', {
	refresh(frm) {
		// your code here
	}
})

frappe.ui.form.on('Fuel Tank Calibration', {
	litres:function(frm,cdt,cdn) {
	    var child = locals[cdt][cdn];
	    console.log(cur_frm);
	    if(cur_frm.doc.tank_capacity){
			var capacity = cur_frm.doc.tank_capacity * 0.95 ;
			var input_litres = child.litres;
            if (child.litres){
                    if(parseFloat(child.litres) > capacity){
						frappe.model.set_value(cdt,cdn,"litres",'')
						frappe.throw(__("Fuel capacity exceeded 95%. Total fuel tank capacity is {0}ltrs and allowable capacity is {1}ltrs only. The calibration litres input is {2}ltrs",
						[cur_frm.doc.tank_capacity,capacity,input_litres]));
					}
            
            }
	    }
	    else{
	        frappe.throw(__("Set Tank Capasity First"))
	    }
	}
})