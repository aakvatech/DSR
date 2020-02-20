# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from dsr.custom_api import get_linked_docs_info,delete_linked_docs

class CashDeposited(Document):
	def on_cancel(self):
		linked_doc_list = get_linked_docs_info(self.doctype,self.name)
		delete_linked_docs(linked_doc_list)
		if self.journal_entry:
			journal_entry_doc = frappe.get_doc("Journal Entry",self.journal_entry)
			if journal_entry_doc.docstatus == 1:
				journal_entry_doc.flags.ignore_permissions=True
				journal_entry_doc.cancel()
				frappe.msgprint(_("{0} {1} is Canceled").format("Journal Entry",journal_entry_doc.name))
