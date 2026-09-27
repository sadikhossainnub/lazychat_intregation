import frappe


def _get_valid_customer_group(default_group: str | None) -> str:
	"""Ensure the customer group is a valid non-group leaf."""
	if default_group and frappe.db.exists("Customer Group", default_group):
		if not frappe.db.get_value("Customer Group", default_group, "is_group"):
			return default_group

	# Fallbacks if default_group is missing or is a parent group
	for candidate in ["Individual", "Retail", "Online", "Commercial"]:
		if frappe.db.exists("Customer Group", candidate):
			if not frappe.db.get_value("Customer Group", candidate, "is_group"):
				return candidate

	non_groups = frappe.get_all("Customer Group", filters={"is_group": 0}, fields=["name"], limit=1)
	return non_groups[0].name if non_groups else "Individual"


def get_or_create_customer(name: str, phone: str, address: str) -> dict:
	"""
	Find or create an ERPNext Customer along with a Contact and Address.

	:returns: dict with {"customer": customer_name, "contact": contact_name, "address": address_name}
	"""
	settings = frappe.get_single("LazyChat Settings")
	customer_name = None
	contact_name = None
	address_name = None

	# ── 1. Try to find by mobile number via Contact Phone ───────────────────
	if phone:
		contact_phone = frappe.get_all(
			"Contact Phone",
			filters={"phone": phone},
			fields=["parent"],
			limit=1,
		)
		if contact_phone:
			contact_name = contact_phone[0].parent
			contact_doc = frappe.get_doc("Contact", contact_name)
			for link in contact_doc.links:
				if link.link_doctype == "Customer":
					customer_name = link.link_name
					break

	# ── 2. Try to find by customer_name if not found via phone ─────────────
	if not customer_name and name:
		existing = frappe.get_all(
			"Customer",
			filters={"customer_name": name},
			fields=["name"],
			limit=1,
		)
		if existing:
			customer_name = existing[0].name

	# ── 3. Create a new Customer if not found ────────────────────────────────
	if not customer_name:
		customer_group = _get_valid_customer_group(settings.default_customer_group)
		customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": name or "LazyChat Customer",
			"customer_type": "Individual",
			"customer_group": customer_group,
			"territory": "All Territories",
		})
		customer.flags.ignore_permissions = True
		customer.insert()
		customer_name = customer.name

	# ── 4. Create Contact if not already linked ──────────────────────────────
	if not contact_name:
		contact_doc = frappe.get_doc({
			"doctype": "Contact",
			"first_name": (name or "").split(" ")[0] or "LazyChat",
			"last_name": " ".join((name or "").split(" ")[1:]) or None,
			"links": [{"link_doctype": "Customer", "link_name": customer_name}],
		})
		if phone:
			contact_doc.append("phone_nos", {
				"phone": phone,
				"is_primary_mobile_no": 1,
				"is_primary_phone": 1,
			})
		contact_doc.flags.ignore_permissions = True
		contact_doc.insert()
		contact_name = contact_doc.name

	# ── 5. Create Address if provided ─────────────────────────────────────────
	if address:
		existing_addr = frappe.get_all(
			"Dynamic Link",
			filters={"parenttype": "Address", "link_doctype": "Customer", "link_name": customer_name},
			fields=["parent"],
			limit=1,
		)
		if existing_addr:
			address_name = existing_addr[0].parent
		else:
			country = frappe.defaults.get_global_default("country") or "Bangladesh"
			city = "Dhaka"
			if "dhaka" in address.lower():
				city = "Dhaka"
			elif "chittagong" in address.lower() or "chattogram" in address.lower():
				city = "Chittagong"
			elif "sylhet" in address.lower():
				city = "Sylhet"
			elif "rajshahi" in address.lower():
				city = "Rajshahi"
			elif "khulna" in address.lower():
				city = "Khulna"

			addr_doc = frappe.get_doc({
				"doctype": "Address",
				"address_title": name or "LazyChat Customer",
				"address_type": "Shipping",
				"address_line1": address,
				"city": city,
				"country": country,
				"phone": phone or "",
				"links": [{"link_doctype": "Customer", "link_name": customer_name}],
			})
			addr_doc.flags.ignore_permissions = True
			addr_doc.insert()
			address_name = addr_doc.name

	frappe.db.commit()

	return {
		"customer": customer_name,
		"contact": contact_name,
		"address": address_name,
	}
