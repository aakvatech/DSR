from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint,flt
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
	account_details = make_account_row(expense_account,cash_account,self.amount)
	res = make_journal_entry(account_details,self.date,self.bill_no)
	frappe.db.set_value(self.doctype,self.name,"journal_entry",res)

def make_account_row(debit_account,credit_account,amount):
	accounts = []
	debit_row = dict(
		account = debit_account,
		debit_in_account_currency = amount
	)
	accounts.append(debit_row)
	credit_row = dict(
		account = credit_account,
		credit_in_account_currency = amount
	)
	accounts.append(credit_row)
	return accounts

def make_journal_entry(accounts,date,bill_no=None):
	if len(accounts) <= 0:
		frappe.throw(_("Something went while creating journal entry"))
	jv_doc = frappe.get_doc(dict(
		doctype = "Journal Entry",
		posting_date = date,
		accounts = accounts,
		bill_no = bill_no
	))
	jv_doc.flags.ignore_permissions = True
	jv_doc.save(ignore_permissions = True)
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
	account_details = make_account_row(bank_account,cash_account,self.amount)
	res = make_journal_entry(account_details,self.date,self.credit_sales_reference)
	frappe.db.set_value(self.doctype,self.name,"journal_entry",res)

@frappe.whitelist()
def list_journal():
	journal_doclist=frappe.db.sql("SELECT name FROM `tabJournal Entry` ORDER BY name DESC LIMIT 3", as_dict=1)
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
def update_journal(data):
	return {"message":"Journal updated"}

@frappe.whitelist()
def update_payments(data):
	return {"message":"Payment updated"}

@frappe.whitelist()
def update_sales(data):
	return {"message":"Sales Invoice updated"}

@frappe.whitelist()
def update_purchase(data):
	return {"message":"Purchase Invoice updated"}

@frappe.whitelist()
def update_stockentry(data):
	return {"message":"Stock Entry updated"}