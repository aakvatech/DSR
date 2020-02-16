// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('DSR Settings', {
	check_api: function(frm) {
		frappe.call({
			method: 'dsr.dsr.doctype.dsr_settings.dsr_settings.check_api',
			// args:{
			// 	"start_time":frm.doc.start_time,
			// 	"end_time":frm.doc.end_time,
			// },
			callback: (r) => {
				if (r.message){
					// console.log(r.message);
					frappe.msgprint(r.message);
				}
				
			}
		});
	},
});
