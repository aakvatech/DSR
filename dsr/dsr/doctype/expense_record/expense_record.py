# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from dsr.custom_api import get_linked_docs_info,cancle_linked_docs,cancel_doc,delete_doc,delete_linked_docs

class ExpenseRecord(Document):
	def on_cancel(self):
		linked_doc_list = get_linked_docs_info(self.doctype,self.name)
		cancle_linked_docs(linked_doc_list)
		if self.journal_entry:
			cancel_doc("Journal Entry",self.journal_entry)
			

	def on_trash(self):
		linked_doc_list = get_linked_docs_info(self.doctype,self.name)
		delete_linked_docs(linked_doc_list)
		if self.journal_entry:
			delete_doc("Journal Entry",self.journal_entry)