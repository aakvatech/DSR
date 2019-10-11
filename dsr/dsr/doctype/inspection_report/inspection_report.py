# -*- coding: utf-8 -*-
# Copyright (c) 2019, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class InspectionReport(Document):
	pass


# def get_litres_from_fuel_tank(fuel_tank,dip_reading):
# 	data = frappe.get_all("Fuel Tank",filters = [["Fuel Tank","name","=",fuel_tank],["Fuel Tank","fuel_station","=",station],["Fuel Tank Calibration","milimeters","=",dip_reading]])
@frappe.whitelist()
def get_litres_from_dip_reading(fuel_tank,station,dip_reading):
	reading_data = frappe.db.sql("""select
   c.litres as 'litres' 
from
   `tabFuel Tank Calibration` as c 
   inner join
      `tabFuel Tank` as p 
      on c.parent = p.name 
where
   p.name =%s 
   and p.fuel_station =%s 
   and c.milimeters =%s""",(fuel_tank,station,dip_reading),as_dict=1)
	if len(reading_data) >= 1:
	   return reading_data[0].litres
	else:
		return 0

