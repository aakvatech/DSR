# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _


class FuelStockReceipts(Document):
	def before_submit(self):
		on_submit_fuel_stock_Receipt(self)


@frappe.whitelist()
def on_submit_fuel_stock_Receipt(self):
	supplier = frappe.db.get_value("Fuel Station",self.fuel_station,"oil_company")
	if not supplier:
		frappe.throw(_("Petroleum Products Company Not Define In Fuel Station"))

	company = frappe.db.get_value("Fuel Station",self.fuel_station,"company")
	if not company:
		frappe.throw(_("Company Not Define In Fuel Station"))
	item_object = []
	for row in self.fuel_stock_receipt_tanks:
		fuel_item = frappe.db.get_value("Fuel Tank",row.fuel_tank,"fuel_item")
		if not fuel_item:
			frappe.throw(_("Fuel Item Not Define In Fuel Tank"))
		warehouse = frappe.db.get_value("Fuel Tank",row.fuel_tank,"warehouse")
		if not warehouse:
			frappe.throw(_("Warehouse Not Define In Fuel Tank"))
		item_details = frappe.get_doc("Fuel Item",fuel_item)
		if not item_details.item:
			frappe.throw(_("Item Not Define In Fuel Item"))
		if not item_details.mera_wholesale_price:
			frappe.throw(_("Mera Wholesale Price Not Define In Fuel Item"))
		item_row = dict(
			item_code = item_details.item,
			qty = row.difference_ltrs,
			rate = item_details.mera_wholesale_price,
			warehouse = warehouse
		)
		item_object.append(item_row)
	make_purchase_invoice(supplier,self.date,company,item_object)

def make_purchase_invoice(supplier,date,company,item_object):
	pinv_doc = frappe.get_doc(dict(
		supplier = supplier,
		posting_date = date,
		company = company,
		items = item_object
	)).insert(ignore_permissions = True)
	pinv_doc.submit()

			