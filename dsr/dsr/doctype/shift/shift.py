# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.utils import cint,flt,now_datetime
from frappe.model.document import Document
import json
from dsr.custom_api import get_mera_retail_rate,get_company_from_fuel_station,make_sales_invoice,make_stock_adjustment_entry,get_cost_center_from_fuel_station,get_item_from_fuel_item,get_pump_warehouse

class Shift(Document):
	def before_save(self):
		# Below added to calculate the totals upon a change in the values.
		self.total_bank_deposit = (get_total_banking(self.name) or 0)
		self.total_expenses = (get_total_expenses(self.name) or 0)
		self.opening_balance = (self.opening_balance or 0)
		self.total_deposited = (self.total_deposited or 0)
		self.total_cash_shortage = (self.total_cash_shortage or 0)
		self.total_bank_deposit = (self.total_bank_deposit or 0)
		self.total_expenses = (self.total_expenses or 0)
		self.cash_in_hand = self.opening_balance + self.total_deposited - self.total_cash_shortage - self.total_bank_deposit - self.total_expenses

	def on_change(self):
		delete_item_total_table(self.name)
		add_total_for_dip_reading(self)
		add_total_for_meter_reading(self)
		add_total_for_inward(self)
		add_total_for_credit_sales(self)

	def before_submit(self):
		'''
		Ensure that the shift is closed before submission
		'''
		if (self.shift_status != "Closed"):
			frappe.throw(_("Shift cannot be submitted unless it is closed"),
				frappe.DocstatusTransitionError)

	def on_submit(self):
		'''
		To create Sales Invoice for Cash sales and Stock Entry for Tank Shortage
		'''
		#def make_sales_invoice(customer,company,date,items,fuel_station,shift,pump,credit_id,ignore_pricing_rule=1,update_stock=1,user_remarks=None):
		company = get_company_from_fuel_station(self.fuel_station)
		if not company:
			frappe.throw(_("Company Not Defined In Fuel Station"))		
		warehouse = frappe.db.get_value("Fuel Station",self.fuel_station,"default_warehouse")
		if not warehouse:
			frappe.throw(_("Default Warehouse Not Defined In Fuel Station"))		
		items = []
		for total_row in self.shift_fuel_item_totals:
			item_dict = dict(
				item_code = get_item_from_fuel_item(total_row.fuel_item),
				qty = self.quantity,
				rate = frappe.db.get_value("Fuel Item",total_row.fuel_item,"station_retail_price"),
				warehouse = get_pump_warehouse(self.pump),
				cost_center = get_cost_center_from_fuel_station(self.fuel_station)
			)
			items.append(item_dict)
		user_remarks = "Cash Sales of the day for shif " + self.name + " at fuel station " + self.fuel_station
		invoice_doc = make_sales_invoice("Cash Customer",company,self.date,items,self.fuel_station,self.name,"","",1,1,user_remarks)
		if invoice_doc:
				frappe.db.set_value("Shift",self.name,"cash_sales_invoice",invoice_doc.name)
		user_remarks = "Cash Sales of the day for shif " + self.name + " at fuel station " + self.fuel_station
		cost_center = get_cost_center_from_fuel_station(self.fuel_station)
		stock_adjustment = frappe.db.get_value("Fuel Station",self.fuel_station,"stock_adjustment")
		if not stock_adjustment:
			frappe.throw(_("Expense Not Defined In Fuel Station"))
		item_stock_object = []
		#Make 1 stock etnry per fuel item. Get default warehouse from Fuel Station for now.
		qty = 0
		stock_entry_doc = make_stock_adjustment_entry(cost_center,self.date,company,item_stock_object,qty,"",self.fuel_station,user_remarks,warehouse,stock_adjustment)
		if stock_entry_doc:
				frappe.db.set_value("Shift",self.name,"stock_entry",stock_entry_doc.name)

		return

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
def get_total_banking(shift):
	banking = frappe.db.sql("""select sum(amount) from `tabCash Deposited` where shift=%s and docstatus=1""",(shift))
	if len(banking) >= 1:
		return banking[0][0]
	else:
		return 0

@frappe.whitelist()
def get_total_expenses(shift):
	expenses = frappe.db.sql("""select sum(amount) from `tabExpense Record` where shift=%s and docstatus=1""",(shift))
	if len(expenses) >= 1:
		return expenses[0][0]
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
	frappe.db.set_value(doc.doctype,doc.name,str(field_name),field_value or 0)
	return doc

def delete_item_total_table(doc_name):
	frappe.db.sql("""delete from `tabShift Fuel Item Total` where parent=%s""",doc_name)

def set_total(doc_name,doctype,field_name,field_value):
	frappe.db.set_value(doctype,doc_name,str(field_name),flt(field_value) or 0)

@frappe.whitelist()
def close_shift(name,status=None):
	frappe.db.set_value("Shift",name,"shift_status",status)
	frappe.db.set_value("Shift",name,"close_date_and_time",now_datetime())

@frappe.whitelist()
def get_last_shift_data(fuel_station):
	shift_list = frappe.get_all("Shift",filters={'shift_status': 'Closed','fuel_station':fuel_station},fields=["name"],order_by="creation desc")
	if len(shift_list) >= 1:
		return frappe.get_doc("Shift",shift_list[0].name)

@frappe.whitelist()
def calculate_total_sales(shift,pump,total_qty):
	credit_sales = get_credit_sales_details(shift,pump)
	credit_qty = 0
	credit_sales_total = 0
	retail_total_sales = 0
	if credit_sales:
		# credit_qty = credit_sales[0].get('qty',0.0)
		credit_qty = credit_sales[0] or 0
		credit_sales_total = credit_sales[1] or 0
		# credit_sales_total = credit_sales[0].get('amount',0.0)
	# frappe.msgprint(credit_qty, credit_sales_total)
	retail_total_qty = (flt(total_qty) - flt(credit_qty)) or 0
	retail_rate = get_mera_retail_rate(pump)
	retail_total_sales = retail_total_qty * retail_rate
	total_sales = flt(retail_total_sales) + flt(credit_sales_total)
	return (total_sales,credit_sales_total,retail_total_sales)

def get_credit_sales_details(shift,pump):
	credit_sales_details = frappe.db.sql("""select sum(quantity) as qty,sum(amount) as amount from `tabCredit Sales` where shift=%s and pump=%s and docstatus=1 limit 1""",(shift,pump),as_dict=1)
	dou_details = frappe.db.sql("""select sum(quantity) as qty,sum(amount) as amount from `tabDispensed for Office Use` where shift=%s and pump=%s and docstatus=1 limit 1""",(shift,pump),as_dict=1)
	credit_sales_qty = 0
	credit_sales_amount = 0
	# frappe.msgprint(str(credit_sales_details))
	if 'amount' in credit_sales_details[0]:
		credit_sales_amount = credit_sales_details[0].get('amount',0) or 0
	if 'qty' in credit_sales_details[0]:
		credit_sales_qty = credit_sales_details[0].get('qty',0) or 0
	# frappe.msgprint(str(credit_sales_amount))
	dou_credit_sales_qty = 0
	dou_credit_sales_amount = 0
	# frappe.msgprint(str(dou_details))
	if 'amount' in dou_details[0]:
		dou_credit_sales_amount = dou_details[0].get('amount',0) or 0
	if 'qty' in dou_details[0]:
		dou_credit_sales_qty = dou_details[0].get('qty',0) or 0
	total_credit_qty = credit_sales_qty + dou_credit_sales_qty
	total_credit_amount = credit_sales_amount + dou_credit_sales_amount
	return (total_credit_qty, total_credit_amount)
