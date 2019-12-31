# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document

class CustomerGeneratedLPO(Document):
	# def on_submit(self):
	# 	if self.other_station_cash_record:
	# 		balance_qty = frappe.db.get_value("Other Station Credit",self.other_station_cash_record,"balance_qty")
	# 		if balance_qty:
	# 			if balance_qty < self.quantity:
	# 				frappe.throw(_("Balance Qty is {0} not sufficient and Applied Qty is {1}").format(balance_qty,self.quantity))
	# 			frappe.db.set_value("Other Station Credit",self.other_station_cash_record,"balance_qty",balance_qty-self.quantity)
	pass