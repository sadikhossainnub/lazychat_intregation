import frappe
from frappe import _

@frappe.whitelist()
def custom_make_delivery_note(source_name, target_doc=None, kwargs=None):
	"""
	Custom override for erpnext.selling.doctype.sales_order.sales_order.make_delivery_note.
	Intercepts KeyError and unreserved stock inconsistencies and shows a user-friendly message.
	"""
	from erpnext.selling.doctype.sales_order import sales_order as original_so_module

	try:
		return original_so_module.make_delivery_note(source_name, target_doc=target_doc, kwargs=kwargs)
	except KeyError as e:
		frappe.throw(
			_(
				"অর্ডারটির আইটেমে অসঙ্গতি পাওয়া গেছে! অনুগ্রহ করে অব্যবহৃত আইটেমটি Unreserve করুন। (Missing / Inconsistent Item ID: {0})"
			).format(str(e))
		)
