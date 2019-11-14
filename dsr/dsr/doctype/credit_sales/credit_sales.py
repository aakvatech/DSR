# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint,flt
from frappe import _

class CreditSales(Document):
	def on_submit(self):
		if self.other_station_cash_record:
			balance_qty = frappe.db.get_value("Other Station Credit",self.other_station_cash_record,"balance_qty")
			if balance_qty:
				if balance_qty < self.quantity:
					frappe.throw(_("Balance Qty is {0} not sufficient and Applied Qty is {1}").format(balance_qty,self.quantity))
				frappe.db.set_value("Other Station Credit",self.other_station_cash_record,"balance_qty",balance_qty-self.quantity)


@frappe.whitelist()
def calculate_total(qty,item):
	rate = get_rate(item)
	return flt(qty) * flt(rate)

def get_rate(item_code):
	rate = frappe.db.get_value("Fuel Item",item_code,"mera_wholesale_price")
	if not rate:
		frappe.throw(_("Mera Wholesale Price Not Avaialable For Item {0}").format(item_code))
	return rate


@frappe.whitelist()
def get_cash_receiver_other_station_details(station,customer,vehicle):
	data = frappe.db.sql("""
select
   c.name as 'name',
   c.fuel_item as 'item',
   c.balance_qty as 'balance_qty',
   (
      select
         name 
      from
         `tabPump` 
      where
         fuel_item = c.fuel_item 
         and fuel_station = %s
   )
   as 'pump' 
from
   `tabOther Station Credit` as c 
   inner join
      `tabCash Received For Other Station` as p 
      on c.parent = p.name 
where
   p.for_fuel_station = %s 
   and p.customer = %s
   and c.truck_number = %s

""",(station,station,customer,vehicle),as_dict=1)
	if len(data) >= 1:
		return data[0]
	else:
		frappe.throw(_("No Any Cash Receive At Station {0} For Vehicle {1}").format(station,vehicle))