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
	res = make_journal_entry(account_details,self.date,self.bill_no,company, user_remark)
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

def make_journal_entry(accounts,date,bill_no=None,company=None,user_remark=None):
	if len(accounts) <= 0:
		frappe.throw(_("Something went while creating journal entry"))
	jv_doc = frappe.get_doc(dict(
		doctype = "Journal Entry",
		posting_date = date,
		accounts = accounts,
		bill_no = bill_no,
		company = company,
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
	res = make_journal_entry(account_details,self.date,self.credit_sales_reference,company)
	frappe.db.set_value(self.doctype,self.name,"journal_entry",res)

def get_company_from_fuel_station(fuel_station):
	company = frappe.db.get_value("Fuel Station",fuel_station,"company")
	if not company:
		frappe.throw(_("Compant Not Define In Fuel Station"))
	return company

def get_cost_center_from_fuel_station(fuel_station):
	cost_center = frappe.db.get_value("Fuel Station",fuel_station,"cost_center")
	if cost_center:
		return cost_center
	else:
		frappe.throw(_("Cost Center Not Define In Fuel Station"))	

@frappe.whitelist()
def list_journal():
	journal_doclist=frappe.db.sql("SELECT name FROM `tabJournal Entry` WHERE (tally_remoteid IS NULL or tally_remoteid = '') ORDER BY name DESC LIMIT 2", as_dict=1)
	return journal_doclist

@frappe.whitelist()
def list_payments():
	payment_doclist=frappe.db.sql("SELECT name FROM `tabPayment Entry` ORDER BY name DESC LIMIT 3", as_dict=1)
	return payment_doclist

@frappe.whitelist()
def list_sales():
	sales_doclist=frappe.db.sql("SELECT name FROM `tabSales Invoice` ORDER BY name DESC LIMIT 3", as_dict=1)
	return sales_doclist

@frappe.whitelist()
def list_purchase():
	purchase_doclist=frappe.db.sql("SELECT name FROM `tabPurchase Invoice` ORDER BY name DESC LIMIT 3", as_dict=1)
	return purchase_doclist

@frappe.whitelist()
def list_stockentry():
	stockentry_doclist=frappe.db.sql("SELECT name FROM `tabStock Entry` ORDER BY name DESC LIMIT 3", as_dict=1)
	return stockentry_doclist

@frappe.whitelist()
def update_journal(**kwargs):
	kwargs=frappe._dict(kwargs)
	frappe.log_error(str(kwargs))
	data = kwargs.get('data', '')
	doctype = "Journal Entry"
	docname = data.get('journal_name')
	voucher_uid = data.get('voucher_uid')
	update_result = update_record(doctype, docname, voucher_uid)
	return update_result

@frappe.whitelist()
def update_payments(**kwargs):
	kwargs=frappe._dict(kwargs)
	frappe.log_error(str(kwargs))
	data = kwargs.get('data', '')
	doctype = "Payment Entry"
	docname = data.get('sales_name')
	voucher_uid = data.get('voucher_uid')
	update_result = update_record(doctype, docname, voucher_uid)
	return update_result

@frappe.whitelist()
def update_sales(**kwargs):
	kwargs=frappe._dict(kwargs)
	frappe.log_error(str(kwargs))
	data = kwargs.get('data', '')
	doctype = "Sales Invoice"
	docname = data.get('sales_name')
	voucher_uid = data.get('voucher_uid')
	update_result = update_record(doctype, docname, voucher_uid)
	return update_result

@frappe.whitelist()
def update_purchase(**kwargs):
	kwargs=frappe._dict(kwargs)
	frappe.log_error(str(kwargs))
	data = kwargs.get('data', '')
	doctype = "Purchase Invoice"
	docname = data.get('purchase_name')
	voucher_uid = data.get('voucher_uid')
	update_result = update_record(doctype, docname, voucher_uid)
	return update_result

@frappe.whitelist()
def update_stockentry(**kwargs):
	kwargs=frappe._dict(kwargs)
	frappe.log_error(str(kwargs))
	data = kwargs.get('data', '')
	doctype = "Stock Entry"
	docname = data.get('stock_name')
	voucher_uid = data.get('voucher_uid')
	update_result = update_record(doctype, docname, voucher_uid)
	return update_result

def update_record(doctype, docname, voucher_id)
	if(frappe.get_doc(doctype, docname)):
		if (!frappe.db.set_value(doctype, docname, "tally_remoteid", voucher_uid)):
			status_text = "Something went wrong while updating" + doctype + " record for " + docname + " with Tally voucher number " + voucher_uid + ". Please check the access rights to the document."
	else:
		status_text = "Voucher " + voucher_uid + " is not updated as " + doctype + " record for " + docname + " was not found!"
		frappe.log_error(status_text)
	return 

def internal_login_logout_for_transaction(login=True):
	from frappe.auth import LoginManager
	login_manager = LoginManager()
	if login == True:
		login_manager.authenticate("Administrator","dsr-BM$123")
		login_manager.post_login()
	else:
		delete_session(frappe.session.sid, user='Administrator', reason="Internal Logout")

