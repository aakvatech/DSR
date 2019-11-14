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
		frappe.throw(_("Something Wrong for create journal entry"))
	jv_doc = frappe.get_doc(dict(
		doctype = "Journal Entry",
		posting_date = date,
		accounts = accounts,
		bill_no = bill_no
	)).insert()
	jv_doc.submit()
	return jv_doc.name

@frappe.whitelist()
def on_cancel_jv_cancel(self,method):
	if self.journal_entry:
		journal_entry_doc = frappe.get_doc("Journal Entry",self.journal_entry)
		journal_entry_doc.cancel()

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

