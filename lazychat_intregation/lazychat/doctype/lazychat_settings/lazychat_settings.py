import frappe
from frappe.model.document import Document


class LazyChatSettings(Document):
	pass


def get_settings():
	"""Convenience helper — returns the singleton LazyChat Settings document."""
	return frappe.get_single("LazyChat Settings")
