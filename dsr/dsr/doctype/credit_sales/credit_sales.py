# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.pricing_rule.pricing_rule import get_pricing_rule_for_item
from frappe.utils import cint,flt,fmt_money
from frappe import _
from dsr.custom_api import make_sales_invoice,get_cost_center_from_fuel_station,get_item_from_fuel_item,get_company_from_fuel_station,get_pump_warehouse,get_mera_wholesale_rate,get_oil_company_from_fuel_station

class CreditSales(Document):
	def on_submit(self):
		if self.other_station_cash_record:
			balance_qty = frappe.db.get_value("Other Station Credit",self.other_station_cash_record,"balance_qty")
			if balance_qty:
				if balance_qty < self.quantity:
					frappe.throw(_("Balance Qty is {0} not sufficient and Applied Qty is {1}").format(balance_qty,self.quantity))
				frappe.db.set_value("Other Station Credit",self.other_station_cash_record,"balance_qty",balance_qty-self.quantity)
		if self.lpo:
			if (self.quantity == self.original_quantity):
				frappe.db.set_value("Customer Generated LPO",self.lpo,"fulfilled","Completely Fulfilled")
		on_submit_credit_sales(self)

	def validate(self):
		item = frappe.db.get_value("Fuel Item",self.fuel_item,"item")
		if not item:
			frappe.throw(_("Fuel Item {0} Not Assigned To Item").format(self.fuel_item))
		price_rate_details = get_price(item,self.quantity,self.credit_customer,self.fuel_station)
		if (price_rate_details):
			self.rate = price_rate_details.price_list_rate
			#frappe.errprint(flt(self.quantity) * flt(price_rate_details.price_list_rate))
			self.amount = flt(self.quantity) * flt(price_rate_details.price_list_rate)

@frappe.whitelist()
def calculate_total(qty,item):
	rate = get_mera_wholesale_rate(item)
	return flt(qty) * flt(rate)

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
		frappe.throw(_("No Cash Received At Station {0} For Vehicle {1}").format(station,vehicle))

@frappe.whitelist()
def get_price(item_code, qty=1,customer=None,fuel_station=None):
	customer_doc = frappe.get_doc("Customer",customer)
	template_item_code = frappe.db.get_value("Item", item_code, "variant_of")
	price_list = customer_doc.default_price_list or "Standard Selling"
	customer_group = customer_doc.customer_group or "All Customer Groups"
	company = frappe.db.get_value("Fuel Station",fuel_station,"company")
	if price_list:
		price = frappe.get_all("Item Price", fields=["price_list_rate", "currency"],
			filters={"price_list": price_list, "item_code": item_code})
		if template_item_code and not price:
			price = frappe.get_all("Item Price", fields=["price_list_rate", "currency"],
				filters={"price_list": price_list, "item_code": template_item_code})
		if price:
			pricing_rule = get_pricing_rule_for_item(frappe._dict({
				"item_code": item_code,
				"qty": qty,
				"customer":customer,
				"transaction_type": "selling",
				"price_list": price_list,
				"customer_group": customer_group,
				"company": company,
				"conversion_rate": 1,
				"for_shopping_cart": True,
				"currency": frappe.db.get_value("Price List", price_list, "currency")
			}))
			if pricing_rule:
				if pricing_rule.pricing_rule_for == "Discount Percentage":
					price[0].price_list_rate = flt(price[0].price_list_rate * (1.0 - (flt(pricing_rule.discount_percentage) / 100.0)))
				if pricing_rule.pricing_rule_for == "Discount Amount":
					price[0].price_list_rate = flt(price[0].price_list_rate) - flt(pricing_rule.discount_amount)
				if pricing_rule.pricing_rule_for == "Rate":
					price[0].price_list_rate = pricing_rule.price_list_rate
			price_obj = price[0]
			if price_obj:
				price_obj["formatted_price"] = fmt_money(price_obj["price_list_rate"], currency=price_obj["currency"])
				price_obj["currency_symbol"] = not cint(frappe.db.get_default("hide_currency_symbol")) \
					and (frappe.db.get_value("Currency", price_obj.currency, "symbol", cache=True) or price_obj.currency) \
					or ""
				uom_conversion_factor = frappe.db.sql("""select	C.conversion_factor
					from `tabUOM Conversion Detail` C
					inner join `tabItem` I on C.parent = I.name and C.uom = I.sales_uom
					where I.name = %s""", item_code)
				uom_conversion_factor = uom_conversion_factor[0][0] if uom_conversion_factor else 1
				price_obj["formatted_price_sales_uom"] = fmt_money(price_obj["price_list_rate"] * uom_conversion_factor, currency=price_obj["currency"])
				if not price_obj["price_list_rate"]:
					price_obj["price_list_rate"] = 0
				if not price_obj["currency"]:
					price_obj["currency"] = ""
				if not price_obj["formatted_price"]:
					price_obj["formatted_price"] = ""
			return price_obj

@frappe.whitelist()
def on_submit_credit_sales(self):
	item_obj = []
	item_dict = dict(
		item_code = get_item_from_fuel_item(self.fuel_item),
		qty = self.quantity,
		rate = self.rate,
		warehouse = get_pump_warehouse(self.pump),
		cost_center = get_cost_center_from_fuel_station(self.fuel_station)
	)
	item_obj.append(item_dict)
	company = get_company_from_fuel_station(self.fuel_station)
	oil_company = get_oil_company_from_fuel_station(self.fuel_station)
	user_remarks = "To vehicle " + self.vehicle_number + " from pump " + self.pump + " Customer LPO " + (self.lpo or self.manual_lpo_no)
	# frappe.msgprint(user_remarks)
	invoice_doc = make_sales_invoice(self.credit_customer,company,self.date,item_obj,self.fuel_station,self.shift,self.pump,self.name,user_remarks=user_remarks)
	if invoice_doc:
		frappe.db.set_value(self.doctype,self.name,"sales_invoice",invoice_doc.name)
		# Don't create unnecessary journals for oil company consumpion
		if (self.credit_customer != oil_company):
			make_journal_entry(invoice_doc)

def make_journal_entry(invoice_doc):
	accounts = []
	debit_row = dict(
		account = invoice_doc.debit_to,
		debit_in_account_currency = invoice_doc.outstanding_amount,
		party_type = "Customer",
		party = get_oil_company_from_fuel_station(invoice_doc.fuel_station),
		cost_center = get_cost_center_from_fuel_station(invoice_doc.fuel_station)
	)
	accounts.append(debit_row)
	credit_row = dict(
		account = invoice_doc.debit_to,
		credit_in_account_currency = invoice_doc.outstanding_amount,
		party_type = "Customer",
		party = invoice_doc.customer,
		cost_center = get_cost_center_from_fuel_station(invoice_doc.fuel_station),
		reference_type = invoice_doc.doctype,
		reference_name = invoice_doc.name
	)
	accounts.append(credit_row)
	jv_doc = frappe.get_doc(dict(
		doctype = "Journal Entry",
		company = invoice_doc.company,
		posting_date = invoice_doc.posting_date,
		accounts = accounts
	)).insert(ignore_permissions = True)
	jv_doc.submit()
