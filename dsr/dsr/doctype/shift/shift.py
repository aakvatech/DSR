# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.utils import cint,flt,now_datetime
from frappe.model.document import Document
import json
from dsr.custom_api import get_mera_retail_rate,get_company_from_fuel_station,make_sales_invoice_for_shift,make_stock_adjustment_entry,get_cost_center_from_fuel_station,get_item_from_fuel_item,get_pump_warehouse,get_item_from_pump,get_customer_from_fuel_station,get_pos_from_fuel_station,make_sales_pos_payment,get_station_retail_price
from frappe.utils import getdate, nowdate, add_days

class Shift(Document):
	def validate(self):
		set_amount_totals(self)

		set_quantity_totals(self)


	def before_submit(self):
		'''
		Ensure that the shift is closed before submission
		'''
		if (self.shift_status != "Closed"):
			frappe.throw(_("Shift cannot be submitted unless it is closed"), frappe.DocstatusTransitionError)

		set_amount_totals(self)

		set_quantity_totals(self)


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
		user_remarks = "Cash Sales of the day for shif " + self.name + " at fuel station " + self.fuel_station

		items = []
		for pump_row in self.pump_meter_reading:
			if pump_row.calculated_cash_sales > 0 :
				item_dict = dict(
					warehouse = get_pump_warehouse(pump_row.pump),
					item_code = get_item_from_pump(pump_row.pump),
					qty = pump_row.calculated_cash_sales,
					rate = get_station_retail_price(pump_row.pump),
					cost_center = get_cost_center_from_fuel_station(self.fuel_station)
				)
				items.append(item_dict)
		if len(items) > 0:
			invoice_doc = make_sales_invoice_for_shift(
					customer = get_customer_from_fuel_station(self.fuel_station),
					company = get_company_from_fuel_station(self.fuel_station),
					date = self.date,
					items = items,
					update_stock = 1,
					fuel_station = self.fuel_station,
					shift = self.name,
					pump = "",
					credit_id = "",
					user_remarks = user_remarks,
				)
			if invoice_doc:
				make_sales_pos_payment(invoice_doc)
		# 		frappe.db.set_value("Shift",self.name,"cash_sales_invoice",invoice_doc.name)
		
		user_remarks = "Fuel shortage of the day for shift " + self.name + " at fuel station " + self.fuel_station
		cost_center = get_cost_center_from_fuel_station(self.fuel_station)
		stock_adjustment = frappe.db.get_value("Fuel Station",self.fuel_station,"stock_adjustment")
		if not stock_adjustment:
			frappe.throw(_("Expense Not Defined In Fuel Station"))
		items = []
		# Make 1 stock etnry per fuel item. Get default warehouse from Fuel Station for now.

		for row in self.shift_fuel_item_totals:
			if (row.difference_quantity != 0):
				fuel_item = frappe.get_doc("Fuel Item",row.fuel_item)
				item_dict = dict(
				item_code = fuel_item.item,
				qty = row.difference_quantity, 
				s_warehouse = warehouse,
				cost_center = cost_center,
				expense_account= stock_adjustment)
				# set qty_zero to false so that even if one of the fuel item is having transactions then stock entry is created
				items.append(item_dict)
		if len(items) > 0:
			qty = 0 # as the stock entry creation requires this field
			fuel_stock_receipt_no=None # as the stock entry creation requires this field
			stock_entry_doc_name = make_stock_adjustment_entry(cost_center,self.date,company,items,qty,fuel_stock_receipt_no,self.fuel_station,user_remarks,warehouse,stock_adjustment)
			self.stock_entry = stock_entry_doc_name

def set_amount_totals(self):
	# Below added to calculate the amount totals upon a save of the document.
	self.total_bank_deposit = (get_total_retail_banking(self.name) or 0)
	self.total_credit_sales = (get_total_credit_sales_amount(self.name) or 0)
	self.total_expenses = (get_total_expenses(self.name) or 0)
	self.opening_balance = (self.opening_balance or 0)
	self.total_deposited = (self.total_deposited or 0)
	self.total_cash_shortage = (self.total_cash_shortage or 0)
	self.total_bank_deposit = (self.total_bank_deposit or 0)
	self.total_expenses = (self.total_expenses or 0)
	self.cash_in_hand = self.opening_balance + self.total_deposited - self.total_bank_deposit - self.total_expenses

def set_quantity_totals(self):
	# Below added to calculate the quantity totals upon a save of the document.
	self.shift_fuel_item_totals = []
	data = []

	# Prepare fuel item list from fuel items of the station
	fuel_item_list = frappe.get_list("Fuel Item", filters={"fuel_station": self.fuel_station})
	for fuel_item in fuel_item_list:
		fuel_item_related_tank_list = frappe.get_list("Fuel Tank", fields=("name"), filters={"fuel_item": fuel_item.name})
		fuel_item_related_pump_list = frappe.get_list("Pump", fields=("name"), filters={"fuel_item": fuel_item.name})

		tank_usage_quantity = 0
		for row in self.dip_reading:
			if any(fuel_tank['name'] == row.fuel_tank for fuel_tank in fuel_item_related_tank_list):
				tank_usage_quantity += (row.difference_in_liters or 0) * -1
		inward_quantity = get_total_quatity_inward_from_stock_receipt(self.name, fuel_item.name) or 0
		total_sales_quantity = 0
		for row in self.pump_meter_reading:
			if any(pump['name'] == row.pump for pump in fuel_item_related_pump_list):
				total_sales_quantity += row.calculated_sales or 0
		total_credit_sales = get_total_credit_sales(self.name, fuel_item.name) or 0

		data.append({
			"fuel_item": fuel_item.name,
			"tank_usage_quantity": tank_usage_quantity or 0,
			"inward_quantity": inward_quantity or 0,
			"total_sales_quantity": total_sales_quantity or 0,
			"difference_quantity": (tank_usage_quantity + inward_quantity - total_sales_quantity) or 0,
			"credit_sales_quantity": total_credit_sales or 0,
			"cash_sales_quantity": (total_sales_quantity - total_credit_sales) or 0
		})
	self.update({
		"shift_fuel_item_totals": data
	})

def get_total_quatity_inward_from_stock_receipt(shift,fuel_item):
	stock_receipt = frappe.db.sql("""SELECT SUM(actual_quantity)
		FROM   `tabFuel Stock Receipts`
		WHERE  shift = %s
			AND fuel_item = %s
			AND docstatus in (0,1)""",(shift,fuel_item))
	if len(stock_receipt) >= 1:
		return stock_receipt[0][0] or 0
	else:
		return 0

def get_total_credit_sales(shift,fuel_item):
	credit_sales = frappe.db.sql("""SELECT SUM(quantity) FROM `tabCredit Sales` WHERE shift=%s AND fuel_item=%s and docstatus in (0,1) """,(shift,fuel_item))
	if len(credit_sales) >= 1:
		return credit_sales[0][0] or 0
	else:
		return 0

def get_total_credit_sales_amount(shift):
	credit_sales = frappe.db.sql("""SELECT SUM(amount) FROM `tabCredit Sales` WHERE shift=%s and docstatus in (0,1) """,(shift))
	if len(credit_sales) >= 1:
		return credit_sales[0][0] or 0
	else:
		return 0

@frappe.whitelist()
def get_total_retail_banking(shift):
	banking = frappe.db.sql("""SELECT SUM(amount) FROM `tabCash Deposited` WHERE shift=%s AND (credit_sales_reference = '' OR credit_sales_reference IS NULL) and docstatus in (0,1) """,(shift))
	# frappe.msgprint(str(banking))
	if len(banking) >= 1:
		return banking[0][0] or 0
	else:
		return 0

@frappe.whitelist()
def get_total_expenses(shift):
	expenses = frappe.db.sql("""select sum(amount) from `tabExpense Record` where shift=%s and docstatus in (0,1) """,(shift))
	if len(expenses) >= 1:
		return expenses[0][0] or 0
	else:
		return 0

@frappe.whitelist()
def close_shift(name,status=None):
	unsubmitted_credit_sales = frappe.db.sql("""select count(*) from `tabCredit Sales` where shift=%s and docstatus=0""",(name))
	# frappe.msgprint(str(unsubmitted_credit_sales))
	if(unsubmitted_credit_sales[0][0] > 0):
		frappe.throw(_("Outstanding Credit Sales to be submitted. Ensure all Credit Sales for this shift are submitted and retry to close the shift."), frappe.DocstatusTransitionError)
	unsubmitted_dou = frappe.db.sql("""select count(*) from `tabDispensed for Office Use` where shift=%s and docstatus=0""",(name))
	if(unsubmitted_dou[0][0] > 0):
		frappe.throw(_("Outstanding Dispensed for Office Use to be submitted. Ensure all Dispensed for Office Use for this shift are submitted and retry to close the shift."), frappe.DocstatusTransitionError)
	unsubmitted_fuel_stock_receipts = frappe.db.sql("""select count(*) from `tabFuel Stock Receipts` where shift=%s and docstatus=0""",(name))
	if(unsubmitted_fuel_stock_receipts[0][0] > 0):
		frappe.throw(_("Outstanding Fuel Stock Receipts to be submitted. Ensure all Fuel Stock Receipts for this shift are submitted and retry to close the shift."), frappe.DocstatusTransitionError)
	unsubmitted_cash_deposited = frappe.db.sql("""select count(*) from `tabCash Deposited` where shift=%s and docstatus=0""",(name))
	if(unsubmitted_cash_deposited[0][0] > 0):
		frappe.throw(_("Outstanding Cash Deposited to be submitted. Ensure all Cash Deposited for this shift are submitted and retry to close the shift."), frappe.DocstatusTransitionError)
	unsubmitted_expense_record = frappe.db.sql("""select count(*) from `tabExpense Record` where shift=%s and docstatus=0""",(name))
	if(unsubmitted_expense_record[0][0] > 0):
		frappe.throw(_("Outstanding Expense Record to be submitted. Ensure all Expense Record for this shift are submitted and retry to close the shift."), frappe.DocstatusTransitionError)
	unsubmitted_inspection_report = frappe.db.sql("""select count(*) from `tabInspection Report` where shift=%s and docstatus=0""",(name))
	if(unsubmitted_inspection_report[0][0] > 0):
		frappe.throw(_("Outstanding Inspection Report to be submitted. Ensure all Inspection Report for this shift are submitted and retry to close the shift."), frappe.DocstatusTransitionError)

	'''
	Check if there are any fuel quantity totals more than 200liters default
	'''
	shift_doc = frappe.get_doc("Shift",name)
	allowable_difference = frappe.db.get_value("Fuel Station",shift_doc.fuel_station,"allowable_difference") or 200
	for fuel_item_total in shift_doc.shift_fuel_item_totals:
		if (fuel_item_total.difference_quantity < (allowable_difference * -1) or fuel_item_total.difference_quantity > allowable_difference):
			frappe.throw(_("The fuel item total for " + fuel_item_total.fuel_item + " is greater than the allowable difference set for the station " + shift_doc.fuel_station + " of " + str(fuel_item_total.difference_quantity) + " liters. Please make sure all fuel stock receipts are entered, dip readings and pump readings are correctly recorded."))
			
	frappe.db.set_value("Shift",name,"shift_status",status)
	frappe.db.set_value("Shift",name,"close_date_and_time",now_datetime())


@frappe.whitelist()
def get_last_shift_data(fuel_station,date=None,shift_name=None):
	if (not date or not shift_name or not fuel_station):
		return None
	shift_list = frappe.get_all("Shift",filters=[{'shift_status': 'Closed'},{'fuel_station':fuel_station},['date', '<=', date]],fields=["name", "date"],order_by="date desc, creation desc", limit_page_length=1)
	if len(shift_list) >= 1:
		# frappe.msgprint("Date " + str(date) + " and shift date is " + str(getdate(shift_list[0].date)))
		if shift_list[0].date < getdate(add_days(date, -1)):
			frappe.throw(_("The date entered " + str(date) + " is too far from the last shift date " +str(shift_list[0].date) + ". Please recheck or contact support."))
		else:
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
	if retail_total_qty < 0:
		retail_total_qty = 0
		frappe.throw(_("Cash sales cannot be negative."))
	retail_rate = get_station_retail_price(pump)
	retail_total_sales = retail_total_qty * retail_rate
	total_sales = flt(retail_total_sales) + flt(credit_sales_total)
	return (total_sales,credit_sales_total,retail_total_sales, retail_total_qty, flt(credit_qty))

def get_credit_sales_details(shift,pump):
	credit_sales_details = frappe.db.sql("""select sum(quantity) as qty,sum(amount) as amount from `tabCredit Sales` where shift=%s and pump=%s and docstatus in (0,1) limit 1""",(shift,pump),as_dict=1)
	dou_details = frappe.db.sql("""select sum(quantity) as qty,sum(amount) as amount from `tabDispensed for Office Use` where shift=%s and pump=%s and docstatus in (0,1) limit 1""",(shift,pump),as_dict=1)
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
