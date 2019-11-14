# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class CashReceivedForOtherStation(Document):
	def on_submit(self):
		for item in self.other_station_credit:
			frappe.db.set_value(item.doctype,item.name,"balance_qty",item.quantity)

	def validate(self):
		for item in self.other_station_credit:
			validate_balance_qty_for_truck(self.for_fuel_station,item.truck_number)


def validate_balance_qty_for_truck(fuel_station,vehicle):
	data = frappe.db.sql("""
select
   c.balance_qty as 'balance_qty'
from
   `tabOther Station Credit` as c 
   inner join
      `tabCash Received For Other Station` as p 
      on c.parent = p.name 
where
   p.for_fuel_station = %s 
   and c.truck_number = %s

""",(fuel_station,vehicle),as_dict=1)
	if len(data) >= 1:
		if data[0].balance_qty >= 1:
			frappe.throw(_("Vehicle {0} Have Already Balanace {1}").format(vehicle,data[0].balance_qty))