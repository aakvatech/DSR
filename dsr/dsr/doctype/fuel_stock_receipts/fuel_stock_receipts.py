# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from dsr.custom_api import make_stock_adjustment_entry,get_linked_docs_info,cancle_linked_docs,cancel_doc,delete_doc,delete_linked_docs


class FuelStockReceipts(Document):
	def before_submit(self):
		on_submit_fuel_stock_Receipt(self)

	def on_cancel(self):
		linked_doc_list = get_linked_docs_info(self.doctype,self.name)
		cancle_linked_docs(linked_doc_list)
		if self.purchase_invoice:
			cancel_doc("Purchase Invoice",self.purchase_invoice)
		if self.stock_adjustment:
			cancel_doc("Stock Entry",self.stock_adjustment)



	def on_trash(self):
		linked_doc_list = get_linked_docs_info(self.doctype,self.name)
		delete_linked_docs(linked_doc_list)
		if self.purchase_invoice:
			delete_doc("Purchase Invoice",self.purchase_invoice)
		if self.stock_adjustment:
			delete_doc("Stock Entry",self.stock_adjustment)




@frappe.whitelist()
def on_submit_fuel_stock_Receipt(self):
	cost_center = get_cost_center_from_fuel_station(self.fuel_station)
	if not cost_center:
		frappe.throw(_("Cost Center Not Defined In Fuel Station"))

	supplier = frappe.db.get_value("Fuel Station",self.fuel_station,"oil_company")
	if not supplier:
		frappe.throw(_("Petroleum Products Company Not Defined In Fuel Station"))

	company = frappe.db.get_value("Fuel Station",self.fuel_station,"company")
	if not company:
		frappe.throw(_("Company Not Defined In Fuel Station"))

	stock_adjustment = frappe.db.get_value("Fuel Station",self.fuel_station,"stock_adjustment")
	if not stock_adjustment:
		frappe.throw(_("Expense Not Defined In Fuel Station"))

	items = []
	item_stock_object = []
	for row in self.fuel_stock_receipt_tanks:
		if row.difference_ltrs > 0:
			fuel_item = frappe.db.get_value("Fuel Tank",row.fuel_tank,"fuel_item")
			if not fuel_item:
				frappe.throw(_("Fuel Item Not Defined In Fuel Tank"))
			warehouse = frappe.db.get_value("Fuel Tank",row.fuel_tank,"warehouse")
			if not warehouse:
				frappe.throw(_("Warehouse Not Defined In Fuel Tank"))
			item_details = frappe.get_doc("Fuel Item",fuel_item)
			if not item_details.item:
				frappe.throw(_("Item Not Defined In Fuel Item"))
			if not item_details.mera_wholesale_price:
				frappe.throw(_("MERA Wholesale Price Not Defined In Fuel Item"))
			fuel_station = frappe.db.get_value("Fuel Tank",row.fuel_tank,"fuel_station")
			if not fuel_station:
				frappe.throw(_("Fuel Station Not Define In Fuel Tank"))
			item_row = dict(
				item_code = item_details.item,
				qty = row.difference_ltrs,
				fuel_tank = row.fuel_tank,
				rate = item_details.mera_wholesale_price,
				warehouse = warehouse,
				cost_center = cost_center)
			items.append(item_row)
			user_remarks = "Fuel Stock Receipt " + self.name + " for delivery Note " + str(self.delivery_note) + " for shift " + str(self.shift) + " Shortage recorded for fuel item " +self.fuel_item + " = " + str(self.fuel_shortage)

			pinv_doc_name = make_purchase_invoice(supplier,self.date,company,items,self.name, self.fuel_station,user_remarks)
			if pinv_doc_name:
				self.purchase_invoice = pinv_doc_name

		if self.fuel_shortage != 0:
			item_stock_row = dict(
				item_code = item_details.item,
				qty = self.fuel_shortage * (-1), 
				s_warehouse = warehouse,
				cost_center = cost_center,
				expense_account= stock_adjustment)	
			item_stock_object.append(item_stock_row)
			stock_entry_doc_name = make_stock_adjustment_entry(cost_center,self.date,company,item_stock_object,self.fuel_shortage,self.name, self.fuel_station,user_remarks,warehouse,stock_adjustment)
			if stock_entry_doc_name:
				self.stock_adjustment = stock_entry_doc_name


def make_purchase_invoice(supplier,date,company,item_object,fuel_stock_receipt_no=None,fuel_station=None,user_remarks=None):
	pinv_doc = frappe.get_doc(dict(
		doctype = "Purchase Invoice",
		supplier = supplier,
		posting_date = date,
		company = company,
		items = item_object,
		update_stock = 1,
		remarks = user_remarks,
		fuel_station = fuel_station,
		fuel_stock_receipts = fuel_stock_receipt_no
	)).insert(ignore_permissions = True)
	if pinv_doc:
		frappe.flags.ignore_account_permission = True
		pinv_doc.submit()
		return pinv_doc.name	

def get_cost_center_from_fuel_station(fuel_station):
	cost_center = frappe.db.get_value("Fuel Station",fuel_station,"cost_center")
	if cost_center:
		return cost_center
	else:
		frappe.throw(_("Cost Center Not Define In Fuel Station"))	
