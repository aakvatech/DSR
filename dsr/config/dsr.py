from __future__ import unicode_literals
from frappe import _
import frappe


def get_data():
	config = [
		{
			"label": _("Daily Sales Documents"),
			"items": [
				{
					"type": "doctype",
					"name": "Cash Deposited",
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "Cash Received For Other Station",
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "Credit Sales",
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "Credit Sales Collection",
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "Dispensed for Office Use",
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "Expense Record",
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "Fuel Stock Receipts",
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "Inspection Report",
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "Shift",
					"onboard": 0,
				},
			]
		},
		{
			"label": _("Daily Sales Masters"),
			"items": [
				{
					"type": "doctype",
					"name": "Attendant",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Expense Type",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Fuel Item",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Fuel Tank",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Pump",
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Daily Sales Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Fuel Station",
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "query-report",
					"name": "Register",
					"doctype": "Bill",
					"onboard": 0,
				},
			]
		},
	]
	return config
