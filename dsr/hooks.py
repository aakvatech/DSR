# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "dsr"
app_title = "Dsr"
app_publisher = "Aakvatech Limited"
app_description = "Daily Sales Report with Inventory for Fuel Stations"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@aakvatech.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dsr/css/dsr.css"
# app_include_js = "/assets/dsr/js/dsr.js"

# include js, css files in header of web template
# web_include_css = "/assets/dsr/css/dsr.css"
# web_include_js = "/assets/dsr/js/dsr.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "dsr.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "dsr.install.before_install"
# after_install = "dsr.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dsr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

fixtures = [{"doctype":"Custom Fields", "filters": [["_user_tag", "like", ("%DSR%")]]}, {"doctype":"Notification", "filters": [{"is_standard":0}]}, 'Auto Email Report', "Translation", {"doctype":"Print Format", "filters": [{"module":"DSR"}]}, {"doctype":"Report", "filters": [{"module":"DSR"}]} ]

doc_events = {
	"Expense Record": {
		"on_submit": "dsr.custom_api.on_submit_expense_record",
		"on_cancel":"dsr.custom_api.on_cancel_jv_cancel"
	},
	"Cash Deposited": {
		"on_submit": "dsr.custom_api.on_submit_cash_deposited",
		"on_cancel":"dsr.custom_api.on_cancel_jv_cancel"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dsr.tasks.all"
# 	],
# 	"daily": [
# 		"dsr.tasks.daily"
# 	],
# 	"hourly": [
# 		"dsr.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dsr.tasks.weekly"
# 	]
# 	"monthly": [
# 		"dsr.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "dsr.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dsr.event.get_events"
# }

