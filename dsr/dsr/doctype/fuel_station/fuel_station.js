// Copyright (c) 2019, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fuel Station', {
	setup: function(frm) {
		frm.set_query('default_cash_account', function() {
			return {
				filters: {
					'company': frm.doc.company,
					"account_type": "Cash",
					"is_group": 0,
				}
			}
		});
		frm.set_query('cash_customer_pos_profile', function() {
			return {
				filters: {
					'company': frm.doc.company,
				}
			}
		});
		frm.set_query('stock_adjustment', function() {
			return {
				filters: {
					'company': frm.doc.company,
					"account_type": "Stock Adjustment",
					"is_group": 0,
				}
			}
		});
		frm.set_query('default_warehouse', function() {
			return {
				filters: {
					'company': frm.doc.company,
					"is_group": 0,
				}
			}
		});
		frm.set_query('cost_center', function() {
			return {
				filters: {
					'company': frm.doc.company,
				}
			}
		});
	},
	company: function(frm) {
		frm.set_value("cost_center", "")
		frm.set_value("default_cash_account", "")
	}
});
