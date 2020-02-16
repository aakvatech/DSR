# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
import requests
from requests.exceptions import Timeout
import json
from frappe.utils import today, get_datetime, add_to_date, getdate
# from urllib.parse import urlparse, urlunparse
# from frappe.utils.password import get_decrypted_password

class DSRSettings(Document):
	def validate(self):
		# check_api()
		pass

def get_url():
	if frappe.db.get_value("DSR Settings", None, "system_url"):
		url = frappe.db.get_value("DSR Settings", None, "system_url")
		return url
	else:
		frappe.throw(_("Please set System URL"))

def get_system_api_key():
	if frappe.db.get_value("DSR Settings", None, "system_api_key"):
		system_api_key = frappe.db.get_value("DSR Settings", None, "system_api_key")
		return system_api_key
	else:
		frappe.throw(_("Please make sure you have System API Key"))


def get_system_api_secret():
	if frappe.db.get_value("DSR Settings", None, "system_api_secret"):
		dsr_doc = frappe.get_doc("DSR Settings")
		system_api_secret = dsr_doc.get_password(fieldname="system_api_secret", raise_exception=False)
		return system_api_secret
	else:
		frappe.throw(_("Please make sure you have System API Secret"))

def get_host():
	if frappe.db.get_value("DSR Settings", None, "host"):
		host = frappe.db.get_value("DSR Settings", None, "host")
		return host
	else:
		return


def get_headers():
	headers = {'Host': get_host(), 'Authorization': "token " +  get_system_api_key() + ":" + get_system_api_secret()}
	return headers

@frappe.whitelist()
def check_api():
	url = get_url() + "/api/resource/Item"
	frappe.msgprint(str(url))
	frappe.msgprint(str(get_headers()))
	try:
		response = requests.request("GET",url = url, headers = get_headers(), timeout=5)
	except Timeout:
		frappe.msgprint(_("Error Please check the Other Server Request timeout"))
	else:
		if response.status_code == 200 :
			res = json.loads(response.text)
			frappe.msgprint(str(res))
		else:
			frappe.msgprint(str(response.status_code))


# @frappe.whitelist()
# def check_api():

# 	url1 = get_url() + "/api/resource/Credit Sales"
# 	parsed_url = urlparse(url1)
# 	frappe.msgprint(str(parsed_url))
# 	params = {'start': '0', 'count': '1', 'currency': '20', 'country': 'CDN'}
# 	url = urlunparse(parsed_url[:1] + (get_host(),) + parsed_url[2:])
# 	frappe.msgprint(str(url))
# 	frappe.msgprint(str(get_headers()))
# 	try:
# 		response = requests.get(url, headers={'Host': parsed_url.netloc}, params=params, timeout=5)
# 	except Timeout:
# 		frappe.msgprint(_("Error Please check the Other Server Request timeout"))
# 	else:
# 		if response.status_code == 200 :
# 			res = json.loads(response.text)
# 			frappe.msgprint(str(res))
# 		else:
# 			frappe.msgprint(str(response.status_code))
