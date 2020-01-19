// Copyright (c) 2020, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Daily Quantity Sales Report"] = {
    "filters": [
        {
            "fieldname":"fuel_station",
            "label": __("Fuel Station"),
            "fieldtype": "Link",
            'options': 'Fuel Station',
            "reqd": 1,
            "width": "60px"
        },
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1,
            "width": "60px"
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1,
            "width": "60px"
        }
    ]
}
