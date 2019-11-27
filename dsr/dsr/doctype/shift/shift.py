# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.utils import cint,flt,now_datetime
from frappe.model.document import Document
import json

class Shift(Document):
	def on_change(self):
		delete_item_total_table(self.name)
		add_total_for_dip_reading(self)
		add_total_for_meter_reading(self)
		add_total_for_inward(self)
		add_total_for_credit_sales(self)
		# for dip_read in self.dip_reading:
		# 	fuel_item = frappe.db.get_value("Fuel Tank",dip_read.fuel_tank,"fuel_item")
		# 	item_available = False
		# 	doc = frappe.get_doc(self.doctype,self.name)			
		# 	for total_row in doc.shift_fuel_item_totals:
		# 		if fuel_item == total_row.fuel_item:
		# 			frappe.msgprint(str(total_row.tank_usage_quantity))	
		# 			set_total(total_row.name,total_row.doctype,'tank_usage_quantity',flt(total_row.tank_usage_quantity) + flt(dip_read.closing_liters))
		# 			item_available = True
		# 	if item_available == False:
		# 		frappe.msgprint(str(dip_read.fuel_tank))
		# 		add_total_row(fuel_item,doc.name,'tank_usage_quantity',dip_read.closing_liters)

		# for meter_read in self.pump_meter_reading:
		# 	fuel_item = frappe.db.get_value("Pump",meter_read.pump,"fuel_item")
		# 	item_available = False
		# 	doc = frappe.get_doc(self.doctype,self.name)			
		# 	for total_row in doc.shift_fuel_item_totals:
		# 		if fuel_item == total_row.fuel_item:
		# 			frappe.msgprint(str(total_row.tank_usage_quantity))	
		# 			set_total(total_row.name,total_row.doctype,'total_sales_quantity',flt(total_row.total_sales_quantity) + flt(meter_read.calculated_sales))
		# 			item_available = True
		# 	if item_available == False:
		# 		frappe.msgprint(str(dip_read.fuel_tank))
		# 		add_total_row(fuel_item,doc.name,'total_sales_quantity',meter_read.calculated_sales)
	# def validate(self):
	# 	doc = frappe.get_all("Shift",filters={'shift_status': 'Open','fuel_station':self.fuel_station},fields=["name"])
	# 	if len(doc) >= 1:
	# 		frappe.throw(_("{0} Is Not Close Yet").format(doc[0].name))

def add_total_for_dip_reading(self):
	for dip_read in self.dip_reading:
		fuel_item = frappe.db.get_value("Fuel Tank",dip_read.fuel_tank,"fuel_item")
		item_available = False
		doc = frappe.get_doc(self.doctype,self.name)			
		for total_row in doc.shift_fuel_item_totals:
			if fuel_item == total_row.fuel_item:
				set_total(total_row.name,total_row.doctype,'tank_usage_quantity',flt(total_row.tank_usage_quantity) + flt(dip_read.closing_liters))
				item_available = True
		if item_available == False:
			add_total_row(fuel_item,doc.name,'tank_usage_quantity',dip_read.closing_liters)

def add_total_for_meter_reading(self):
	for meter_read in self.pump_meter_reading:
		fuel_item = frappe.db.get_value("Pump",meter_read.pump,"fuel_item")
		item_available = False
		doc = frappe.get_doc(self.doctype,self.name)			
		for total_row in doc.shift_fuel_item_totals:
			if fuel_item == total_row.fuel_item:
				set_total(total_row.name,total_row.doctype,'total_sales_quantity',flt(total_row.total_sales_quantity) + flt(meter_read.calculated_sales))
				item_available = True
		if item_available == False:
			add_total_row(fuel_item,doc.name,'total_sales_quantity',meter_read.calculated_sales)

def add_total_for_inward(self):
	doc = frappe.get_doc(self.doctype,self.name)			
	for total_row in doc.shift_fuel_item_totals:
		inward_qty = get_total_quatity_inward_from_stock_receipt(self.name,total_row.fuel_item)
		diff_qty = 0 
		if total_row.tank_usage_quantity:
			diff_qty += total_row.tank_usage_quantity
		if inward_qty:
			diff_qty += flt(inward_qty)
		if total_row.total_sales_quantity:
			diff_qty -= total_row.total_sales_quantity
		set_total(total_row.name,total_row.doctype,'inward_quantity',flt(inward_qty))
		set_total(total_row.name,total_row.doctype,'difference_quantity',flt(diff_qty))

def add_total_for_credit_sales(self):
	doc = frappe.get_doc(self.doctype,self.name)			
	for total_row in doc.shift_fuel_item_totals:
		credit_sales = get_total_credit_sales(self.name,total_row.fuel_item)
		cash_sales = 0
		if total_row.total_sales_quantity:
			cash_sales = flt(total_row.total_sales_quantity) - flt(credit_sales )
		set_total(total_row.name,total_row.doctype,'credit_sales_quantity',flt(credit_sales))
		set_total(total_row.name,total_row.doctype,'cash_sales_quantity',flt(cash_sales))


def get_total_quatity_inward_from_stock_receipt(shift,item):
	stock_reciept = frappe.db.sql("""SELECT Sum(actual_quantity)
FROM   `tabFuel Stock Receipts`
WHERE  shift = %s
       AND fuel_item = %s
       AND docstatus = 1""",(shift,item))
	if len(stock_reciept) >= 1:
		return stock_reciept[0][0]
	else:
		return 0

def get_total_credit_sales(shift,item):
	credit_sales = frappe.db.sql("""select sum(quantity) from `tabCredit Sales` where shift=%s and fuel_item=%s and docstatus=1""",(shift,item))
	if len(credit_sales) >= 1:
		return credit_sales[0][0]
	else:
		return 0



@frappe.whitelist()
def add_total_row(item,parent,field_name,field_value):
	doc = frappe.get_doc(dict(
		doctype = "Shift Fuel Item Total",
		parent = parent,
		parenttype = "Shift",
		parentfield = "shift_fuel_item_totals",
		fuel_item = item,
		field_name = field_value
	)).insert()
	frappe.db.set_value(doc.doctype,doc.name,str(field_name),field_value)
	return doc

def delete_item_total_table(doc_name):
	frappe.db.sql("""delete from `tabShift Fuel Item Total` where parent=%s""",doc_name)

def set_total(doc_name,doctype,field_name,field_value):
	frappe.db.set_value(doctype,doc_name,str(field_name),field_value)

@frappe.whitelist()
def close_shift(name,status=None):
	frappe.db.set_value("Shift",name,"shift_status",status)
	frappe.db.set_value("Shift",name,"close_date_and_time",now_datetime())

@frappe.whitelist()
def get_last_shift_data(fuel_station):
	shift_list = frappe.get_all("Shift",filters={'shift_status': 'Closed','fuel_station':fuel_station},fields=["name"],order_by="creation desc")
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
	return frappe.db.sql("""select sum(quantity) as qty,sum(amount) as amount from `tabCredit Sales` where shift=%s and pump=%s and docstatus=1 limit 1""",(shift,pump),as_dict=1)

def get_rate(pump):
	fuel_item = frappe.db.get_value("Pump",pump,"fuel_item")
	rate = frappe.db.get_value("Fuel Item",fuel_item,"station_retail_price")
	if not rate:
		frappe.throw(_("Station Retail Price Not Avaialable For Item {0}").format(fuel_item))
	return rate