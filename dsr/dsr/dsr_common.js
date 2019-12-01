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