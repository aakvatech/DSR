from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint,flt
from frappe.sessions import Session, clear_sessions, delete_session
from frappe import _

@frappe.whitelist()
def on_submit_expense_record(self,method):
	if not self.fuel_station:
		frappe.throw(_("Fuel Station Required"))
	if not self.expense_type:
		frappe.throw(_("Expense Type Required"))
	expense_account = frappe.db.get_value("Expense Type",self.expense_type,"expense_account")
	if not expense_account:
		frappe.throw(_("Expense account not specified in expense type {0}").format(self.expense_type))
	cash_account = frappe.db.get_value("Fuel Station",self.fuel_station,"default_cash_account")
	if not cash_account:
		frappe.throw(_("Cash account not specified in fuel station {0}").format(self.fuel_station))
	account_details = make_account_row(expense_account,cash_account,self.amount,self.fuel_station)
	company = get_company_from_fuel_station(self.fuel_station)
	user_remark = self.name + " " + self.doctype + " was created at " + self.fuel_station + " for " + self.expense_type + " bill no " + self.bill_no + " during shift " + self.shift
	res = make_journal_entry(account_details,self.date,self.bill_no,company, user_remark,self.fuel_station)
	frappe.db.set_value(self.doctype,self.name,"journal_entry",res)

def make_account_row(debit_account,credit_account,amount,fuel_station):
	accounts = []
	debit_row = dict(
		account = debit_account,
		debit_in_account_currency = amount,
		cost_center = get_cost_center_from_fuel_station(fuel_station)
	)
	accounts.append(debit_row)
	credit_row = dict(
		account = credit_account,
		credit_in_account_currency = amount,
		cost_center = get_cost_center_from_fuel_station(fuel_station)
	)
	accounts.append(credit_row)
	return accounts

@frappe.whitelist()
def make_journal_entry(accounts,date,bill_no=None,company=None,user_remark=None,fuel_station=None):
	if len(accounts) <= 0:
		frappe.throw(_("Something went while creating journal entry"))
	jv_doc = frappe.get_doc(dict(
		doctype = "Journal Entry",
		posting_date = date,
		accounts = accounts,
		bill_no = bill_no,
		company = company,
		fuel_station = fuel_station,
		user_remark = user_remark
	))
	jv_doc.flags.ignore_permissions = True
	frappe.flags.ignore_account_permission = True
	jv_doc.save()
	jv_doc.submit()
	return jv_doc.name

@frappe.whitelist()
def on_cancel_jv_cancel(self,method):
	if self.journal_entry:
		journal_entry_doc = frappe.get_doc("Journal Entry",self.journal_entry)
		if journal_entry_doc:
			journal_entry_doc.cancel(ignore_permissions=True)

@frappe.whitelist()
def on_submit_cash_deposited(self,method):
	bank_account = frappe.db.get_value("Bank Account",self.name_of_bank,"account")
	if not bank_account:
		frappe.throw(_("Account not specified in bank account {0}").format(self.name_of_bank))
	cash_account = frappe.db.get_value("Fuel Station",self.fuel_station,"default_cash_account")
	if not cash_account:
		frappe.throw(_("Cash account not specified in fuel station {0}").format(self.fuel_station))
	account_details = make_account_row(bank_account,cash_account,self.amount,self.fuel_station)
	company = get_company_from_fuel_station(self.fuel_station)
	user_remark = self.name + " " + self.doctype + " was created at " + self.fuel_station + " for " + self.name_of_bank + " during shift " + self.shift
	# Do not create bank journal for credit sales reference deposits
	if not self.credit_sales_reference:
		res = make_journal_entry(account_details,self.date,self.credit_sales_reference,company,user_remark,self.fuel_station)
		frappe.db.set_value(self.doctype,self.name,"journal_entry",res)

@frappe.whitelist()
def get_item_from_fuel_item(fuel_item):
	item = frappe.db.get_value("Fuel Item",fuel_item,"item")
	if item:
		return item
	else:
		frappe.throw(_("Item Not Defined In Fuel Item"))

@frappe.whitelist()
def get_pump_warehouse(pump):
	warehouse = frappe.db.get_value("Pump",pump,"warehouse")
	if warehouse: 
		return warehouse
	else:
		frappe.throw(_("Warehouse Not Defined In Pump"))

@frappe.whitelist()
def get_company_from_fuel_station(fuel_station):
	company = frappe.db.get_value("Fuel Station",fuel_station,"company")
	if not company:
		frappe.throw(_("Company Not Defined In Fuel Station"))
	return company

@frappe.whitelist()
def get_oil_company_from_fuel_station(fuel_station):
	customer = frappe.db.get_value("Fuel Station",fuel_station,"oil_company")
	if customer:
		return customer
	else:
		frappe.throw(_("Customer Not Defined In Fuel Station"))

@frappe.whitelist()
def get_cost_center_from_fuel_station(fuel_station):
	cost_center = frappe.db.get_value("Fuel Station",fuel_station,"cost_center")
	if cost_center:
		return cost_center
	else:
		frappe.throw(_("Cost Center Not Defined In Fuel Station"))

@frappe.whitelist()
def list_tally_company(**kwargs):
	kwargs=frappe._dict(kwargs)
	# frappe.log_error(str(kwargs))
	data = kwargs.get('data', '') or " "
	company = data.get('company') or " "
	tally_company_list = frappe.db.sql("SELECT t.tally_company, t.company, t.fiscal_year, c.abbr FROM `tabTally Integration Company` t INNER JOIN `tabCompany` c on t.company = c.name WHERE t.company = '" + company + "' ORDER BY t.fiscal_year DESC LIMIT 1", as_dict=1)
	return tally_company_list

@frappe.whitelist()
def list_journal():
	# journal_doclist=frappe.db.sql("SELECT name FROM `tabJournal Entry` WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND docstatus = 1 ORDER BY name DESC", as_dict=1)
	journal_doclist=frappe.db.sql("SELECT trx.name as name, tly.name as tally_company, c.abbr as abbr FROM `tabJournal Entry` trx INNER JOIN `tabCompany` c ON trx.company = c.name INNER JOIN `tabTally Integration Company` tly ON c.name = tly.company WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND trx.docstatus = 1 and posting_date > '2020-01-01' ORDER BY tly.name, trx.name DESC", as_dict=1)
	return journal_doclist

@frappe.whitelist()
def list_payments():
	# payment_doclist=frappe.db.sql("SELECT name FROM `tabPayment Entry` WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND docstatus = 1 ORDER BY name DESC", as_dict=1)
	payment_doclist=frappe.db.sql("SELECT trx.name as name, tly.name as tally_company, c.abbr as abbr FROM `tabPayment Entry` trx INNER JOIN `tabCompany` c ON trx.company = c.name INNER JOIN `tabTally Integration Company` tly ON c.name = tly.company WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND trx.docstatus = 1 and posting_date > '2020-01-01' ORDER BY tly.name, trx.name DESC", as_dict=1)
	return payment_doclist

@frappe.whitelist()
def list_sales():
	# sales_doclist=frappe.db.sql("SELECT name FROM `tabSales Invoice` WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND docstatus = 1 ORDER BY name DESC", as_dict=1)
	sales_doclist=frappe.db.sql("SELECT trx.name as name, tly.name as tally_company, c.abbr as abbr FROM `tabSales Invoice` trx INNER JOIN `tabCompany` c ON trx.company = c.name INNER JOIN `tabTally Integration Company` tly ON c.name = tly.company WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND trx.docstatus = 1 and posting_date > '2020-01-01' ORDER BY tly.name, trx.name DESC", as_dict=1)
	return sales_doclist

@frappe.whitelist()
def list_purchase():
	# purchase_doclist=frappe.db.sql("SELECT name FROM `tabPurchase Invoice` WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND docstatus = 1 ORDER BY name DESC", as_dict=1)
	purchase_doclist=frappe.db.sql("SELECT trx.name as name, tly.name as tally_company, c.abbr as abbr FROM `tabPurchase Invoice` trx INNER JOIN `tabCompany` c ON trx.company = c.name INNER JOIN `tabTally Integration Company` tly ON c.name = tly.company WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND trx.docstatus = 1 and posting_date > '2020-01-01' ORDER BY tly.name, trx.name DESC", as_dict=1)
	return purchase_doclist

@frappe.whitelist()
def list_stockentry():
	# stockentry_doclist=frappe.db.sql("SELECT name FROM `tabStock Entry` WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND docstatus = 1 ORDER BY name DESC", as_dict=1)
	stockentry_doclist=frappe.db.sql("SELECT trx.name as name, tly.name as tally_company, c.abbr as abbr FROM `tabStock Entry` trx INNER JOIN `tabCompany` c ON trx.company = c.name INNER JOIN `tabTally Integration Company` tly ON c.name = tly.company WHERE (tally_remoteid IS NULL or tally_remoteid = '') AND trx.docstatus = 1 and posting_date > '2020-01-01' ORDER BY tly.name, trx.name DESC", as_dict=1)
	return stockentry_doclist

@frappe.whitelist()
def update_journal(**kwargs):
	kwargs=frappe._dict(kwargs)
	# frappe.log_error(str(kwargs))
	data = kwargs.get('data', '') or " "
	doctype = "Journal Entry"
	update_result = update_record(doctype, data)
	return update_result

@frappe.whitelist()
def update_payments(**kwargs):
	kwargs=frappe._dict(kwargs)
	# frappe.log_error(str(kwargs))
	data = kwargs.get('data', '') or " "
	doctype = "Payment Entry"
	update_result = update_record(doctype, data)
	return update_result

@frappe.whitelist()
def update_sales(**kwargs):
	kwargs=frappe._dict(kwargs)
	# frappe.log_error(str(kwargs))
	data = kwargs.get('data', '') or " "
	doctype = "Sales Invoice"
	update_result = update_record(doctype, data)
	return update_result

@frappe.whitelist()
def update_purchase(**kwargs):
	kwargs=frappe._dict(kwargs)
	# frappe.log_error(str(kwargs))
	data = kwargs.get('data', '') or " "
	doctype = "Purchase Invoice"
	update_result = update_record(doctype, data)
	return update_result

@frappe.whitelist()
def update_stockentry(**kwargs):
	kwargs=frappe._dict(kwargs)
	# frappe.log_error(str(kwargs))
	data = kwargs.get('data', '') or " "
	doctype = "Stock Entry"
	update_result = update_record(doctype, data)
	return update_result

def update_record(doctype, data):
	docname = data.get('name') or " "
	voucher_uid = data.get('voucher_uid') or " "
	error = data.get('error') or " "
	success = data.get('success') or " "
	if(frappe.get_doc(doctype, docname)):
		tally_remote_update = None
		tally_error_update = frappe.db.set_value(doctype, docname, "tally_error", error)
		if (success == "true"):
			tally_remote_update = frappe.db.set_value(doctype, docname, "tally_remoteid", voucher_uid)
		if not (tally_remote_update or tally_error_update):
			status_text = "Something went wrong while updating " + docname + " record for " + doctype + " with Tally voucher number " + voucher_uid + ". Please check the access rights to the document."
		else:
			status_text = "Error " + error + " on Voucher " + voucher_uid + " updated the " + docname + " record for " + doctype + " correctly."
	else:
		status_text = docname + " record for " + doctype + " was not found!"
	return status_text


@frappe.whitelist()
def reset_tally_related_data(self,method):
	frappe.db.set_value(self.doctype,self.name,"tally_error",None)
	frappe.db.set_value(self.doctype,self.name,"tally_remoteid",None)

@frappe.whitelist()
def make_sales_invoice(customer,company,date,items,fuel_station,shift,pump,credit_id,ignore_pricing_rule=1,update_stock=1,user_remarks=None):
	invoice_doc = frappe.get_doc(dict(
		doctype = "Sales Invoice",
		customer = customer,
		company = company,
		posting_date = date,
		due_date = date,
		ignore_pricing_rule = ignore_pricing_rule,
		items = items,
		update_stock = 1,
		fuel_station = fuel_station,
		shift = shift,
		pump = pump,
		credit_sales = credit_id,
		remarks = user_remarks,
		cost_center = get_cost_center_from_fuel_station(fuel_station)
	)).insert(ignore_permissions=True)
	if invoice_doc:
		frappe.flags.ignore_account_permission = True
		invoice_doc.submit()
		return invoice_doc

def make_stock_adjustment_entry(cost_center,date,company,item_stock_object,qty,fuel_stock_receipt_no, fuel_station,user_remarks=None,warehouse=None,stock_adjustment=None):
	stock_entry_doc =frappe.get_doc(dict(
		doctype = "Stock Entry",
		posting_date= date,
		items = item_stock_object,
		stock_entry_type='Material Issue',
		purpose='Material Issue',
		company= company, 
		remarks = user_remarks,
		fuel_station = fuel_station,
		fuel_stock_receipts = fuel_stock_receipt_no,
		)).insert(ignore_permissions = True)
	if stock_entry_doc:
		frappe.flags.ignore_account_permission = True
		stock_entry_doc.submit()
		return stock_entry_doc.name
	

@frappe.whitelist()
def get_mera_retail_rate(pump):
	fuel_item = frappe.db.get_value("Pump",pump,"fuel_item")
	rate = frappe.db.get_value("Fuel Item",fuel_item,"station_retail_price")
	if not rate:
		frappe.throw(_("Station Retail Price Not Avaialable For Item {0}").format(fuel_item))
	return rate

@frappe.whitelist()
def get_mera_wholesale_rate(item_code):
	rate = frappe.db.get_value("Fuel Item",item_code,"mera_wholesale_price")
	if not rate:
		frappe.throw(_("MERA Wholesale Price Not Avaialable For Item {0}").format(item_code))
	return rate

def get_all_fuel_stations(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select name
		from `tabFuel Station`"""
		)

def get_item_from_pump(pump):
	fuel_item = frappe.db.get_value("Pump",pump,"fuel_item")
	if not fuel_item:
		frappe.throw(_("Fuel Item Not Defined For Pump {0}").format(pump))
	item = get_item_from_fuel_item(fuel_item)
	return item


def get_customer_from_fuel_station(fuel_station):
	cash_customer = frappe.db.get_value("Fuel Station",fuel_station,"cash_customer")
	if cash_customer:
		return cash_customer
	else:
		frappe.throw(_("Cash Customer Not Defined In Fuel Station"))


def get_pos_from_fuel_station(fuel_station):
	cash_customer_pos_profile = frappe.db.get_value("Fuel Station",fuel_station,"cash_customer_pos_profile")
	if cash_customer_pos_profile:
		return cash_customer_pos_profile
	else:
		frappe.throw(_("Cash Customer POS Profile Not Defined In Fuel Station"))

def get_account_pyment_mode(mode_of_payment,company):
	mode_of_payment_doc = frappe.get_doc("Mode of Payment",mode_of_payment)
	if mode_of_payment_doc:
		for account_row in mode_of_payment_doc.accounts:
			if account_row.company == company:
				return account_row.default_account
	else:
		frappe.throw(_("Default Account Not Defined In Mode of Payment"))
	

def make_sales_invoice_for_shift(customer,company,date,items,fuel_station,shift,pump,credit_id,ignore_pricing_rule=1,update_stock=1,user_remarks=None):
	invoice_doc = frappe.get_doc(dict(
		doctype = "Sales Invoice",
		customer = customer,
		company = company,
		posting_date = date,
		due_date = date,
		ignore_pricing_rule = ignore_pricing_rule,
		items = items,
		update_stock = 1,
		fuel_station = fuel_station,
		shift = shift,
		pump = pump,
		credit_sales = credit_id,
		remarks = user_remarks,
		cost_center = get_cost_center_from_fuel_station(fuel_station),
	)).insert(ignore_permissions=True)
	if invoice_doc:
		frappe.flags.ignore_account_permission = True
		return invoice_doc

def make_slaes_pos_payment(invoice_doc):
	invoice_doc.is_pos = 1
	invoice_doc.pos_profile = get_pos_from_fuel_station(invoice_doc.fuel_station)
	payment_row = invoice_doc.append("payments",{})
	payment_row.mode_of_payment = "Cash"
	payment_row.amount = invoice_doc.grand_total
	payment_row.base_amount = invoice_doc.grand_total
	payment_row.account = get_account_pyment_mode("Cash",invoice_doc.company)
	invoice_doc.submit()
