# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.utils import cint,flt,now_datetime
from frappe.model.document import Document

class Shift(Document):
	pass
	# def validate(self):
	# 	doc = frappe.get_all("Shift",filters={'shift_status': 'Open','fuel_station':self.fuel_station},fields=["name"])
	# 	if len(doc) >= 1:
	# 		frappe.throw(_("{0} Is Not Close Yet").format(doc[0].name))

@frappe.whitelist()
def close_shift(name,status=None):
	frappe.db.set_value("Shift",name,"shift_status",status)
	frappe.db.set_value("Shift",name,"close_date_and_time",now_datetime())

@frappe.whitelist()
def get_last_shift_data(fuel_station):
	shift_list = frappe.get_all("Shift",filters={'shift_status': 'Closed','fuel_station':fuel_station},fields=["name"],order_by="creation")
	if len(shift_list) >= 1:
		return frappe.get_doc("Shift",shift_list[0].name)
	else:
		frappe.throw(_("No Any Closed Shift Available"))

@frappe.whitelist()
def calculate_total_sales(shift,pump,total_qty):
	credit_sales = get_credit_sales_details(shift,pump)
	credit_qty = 0
	credit_sales_total = 0
	if credit_sales:
		credit_qty = credit_sales[0]['qty'] or 0
		credit_sales_total = credit_sales[0]['amount'] or 0
	retail_total_qty = flt(total_qty) - flt(credit_qty)
	retail_rate = get_rate(pump)
	retail_total_sales = retail_total_qty * retail_rate
	total_sales = flt(retail_total_sales) + flt(credit_sales_total)
	return (total_sales,credit_sales_total,retail_total_sales)

def get_credit_sales_details(shift,pump):
	return frappe.db.sql("""select sum(quantity) as qty,sum(amount) as amount from `tabCredit Sales` where shift=%s and pump=%s limit 1""",(shift,pump),as_dict=1)

def get_rate(pump):
	fuel_item = frappe.db.get_value("Pump",pump,"fuel_item")
	rate = frappe.db.get_value("Fuel Item",fuel_item,"station_retail_price")
	if not rate:
		frappe.throw(_("Station Retail Price Not Avaialable For Item {0}").format(fuel_item))
	return rate