frappe.ui.form.on(cur_frm.doc.doctype, {
    shift: function(frm, cdt, cdn) {
		frm.set_query('shift', function() {
			return {
				filters: {
					'shift_status': 'Open'
				}
			}
		});
    }
});

var auto_shift_selection = function (frm, cdt, cdn) {
	if (frm.doc.__islocal) {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Shift",
				fields: ["name", "fuel_station", "date"],
				order_by: "creation desc",
				limit_page_length: 1
			},
			async: false,
			callback: function (r) {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "shift", r.message[0].name)
					frappe.model.set_value(cdt, cdn, "date", r.message[0].date)
					frappe.model.set_value(cdt, cdn, "fuel_station", r.message[0].fuel_station)
				}
			}
		});
	}
}