import json
import requests
import frappe
from lazychat_intregation.utils.customer import get_or_create_customer


def _get_sales_type_value() -> str:
	"""Find the matching option string for sales_type on Sales Order."""
	meta = frappe.get_meta("Sales Order")
	field = meta.get_field("sales_type")
	if not field:
		return "LazyChat"

	if field.fieldtype == "Select" and field.options:
		options = [o.strip() for o in field.options.split("\n") if o.strip()]
		for opt in options:
			if opt.lower() in ["lazychat", "lazy chat", "lazy_chat"]:
				return opt
		return options[0] if options else "LazyChat"

	return "LazyChat"


def _extract_orders_list(raw_data) -> list:
	"""
	Safely extract a list of order dicts from any LazyChat API JSON response structure.
	"""
	if not raw_data:
		return []

	if isinstance(raw_data, str):
		try:
			raw_data = json.loads(raw_data)
		except Exception:
			return []

	if isinstance(raw_data, list):
		return raw_data

	if isinstance(raw_data, dict):
		if isinstance(raw_data.get("data"), dict):
			data_dict = raw_data.get("data")
			if isinstance(data_dict.get("orders"), list):
				return data_dict.get("orders")
			elif isinstance(data_dict.get("items"), list):
				return data_dict.get("items")

		for key in ["orders", "data", "results", "items"]:
			val = raw_data.get(key)
			if isinstance(val, list):
				return val

		if "id" in raw_data or "invoice_number" in raw_data or "entries" in raw_data:
			return [raw_data]

		dict_vals = list(raw_data.values())
		if dict_vals and isinstance(dict_vals[0], (dict, str)):
			return dict_vals

	return []


def _resolve_item_code(candidates: list, entry: dict) -> str | None:
	"""
	Resolves a non-template ERPNext Item code from candidate SKUs.
	If matched item is a template (has_variants=1), resolves a child variant.
	"""
	for code in candidates:
		if code and frappe.db.exists("Item", code):
			if not frappe.db.get_value("Item", code, "has_variants"):
				return code

	template_code = None
	for code in candidates:
		if code and frappe.db.exists("Item", code):
			template_code = code
			break

	if not template_code:
		return None

	p_data = entry.get("product_data") or {}
	v_id = str(entry.get("variation_id") or "")

	attr_value = None
	if v_id and isinstance(p_data.get("variations"), list):
		for v in p_data["variations"]:
			if isinstance(v, dict) and (str(v.get("id")) == v_id or str(v.get("sku")) == v_id):
				attrs = v.get("attributes") or []
				if isinstance(attrs, list) and len(attrs) > 0 and isinstance(attrs[0], dict):
					attr_value = attrs[0].get("value")
				elif isinstance(attrs, dict):
					attr_value = next(iter(attrs.values()), None)
				break

	if attr_value:
		variant_match = frappe.db.sql(
			"""
			SELECT parent FROM `tabItem Variant Attribute`
			WHERE attribute_value = %s
			AND parent IN (SELECT name FROM `tabItem` WHERE variant_of = %s AND disabled = 0)
			LIMIT 1
			""",
			(attr_value, template_code),
			as_dict=True,
		)
		if variant_match:
			return variant_match[0].parent

	first_variant = frappe.db.get_value(
		"Item",
		{"variant_of": template_code, "disabled": 0},
		"name",
	)
	return first_variant or template_code


def process_single_lazychat_order(data) -> str | None:
	"""
	Takes a single LazyChat order dict (e.g. INV-000001) and creates a Sales Order in ERPNext
	if it hasn't been created already.
	"""
	if not data:
		return None

	if isinstance(data, str):
		try:
			data = json.loads(data)
		except Exception:
			return None

	if not isinstance(data, dict):
		return None

	settings = frappe.get_single("LazyChat Settings")
	lazychat_order_id = str(data.get("invoice_number") or data.get("id") or "").strip()

	if not lazychat_order_id:
		return None

	existing_so = frappe.db.get_value("Sales Order", {"po_no": lazychat_order_id}, "name")
	if existing_so:
		return existing_so

	phone = str(data.get("phone") or "").strip()
	address = str(data.get("address") or "").strip()

	customer_name = "LazyChat Customer"
	if isinstance(data.get("contact"), dict) and data.get("contact").get("name"):
		customer_name = data.get("contact").get("name").strip()
	elif data.get("customer_name"):
		customer_name = str(data.get("customer_name")).strip()
	elif data.get("name"):
		customer_name = str(data.get("name")).strip()
	elif phone:
		customer_name = f"Customer {phone}"

	entries = data.get("entries") or data.get("line_items") or []
	if not entries:
		return None

	cust_info = get_or_create_customer(customer_name, phone, address)
	customer = cust_info["customer"]
	contact_person = cust_info.get("contact")
	address_docname = cust_info.get("address")

	delivery_date = frappe.utils.add_days(frappe.utils.today(), 7)
	so_items = []

	for entry in entries:
		if isinstance(entry, str):
			try:
				entry = json.loads(entry)
			except Exception:
				continue

		if not isinstance(entry, dict):
			continue

		p_data = entry.get("product_data") or {}
		v_id = str(entry.get("variation_id") or "")

		candidates = []

		if v_id and isinstance(p_data.get("variations"), list):
			for v in p_data["variations"]:
				if isinstance(v, dict) and (str(v.get("id")) == v_id or str(v.get("sku")) == v_id):
					if v.get("sku"):
						candidates.append(str(v["sku"]).strip())
					if v.get("partner_id"):
						candidates.append(str(v["partner_id"]).strip())

		if p_data.get("sku"):
			candidates.append(str(p_data["sku"]).strip())
		if p_data.get("partner_id"):
			candidates.append(str(p_data["partner_id"]).strip())

		if entry.get("sku"):
			candidates.append(str(entry["sku"]).strip())
		if entry.get("variation_id"):
			candidates.append(str(entry["variation_id"]).strip())
		if entry.get("product_id"):
			candidates.append(str(entry["product_id"]).strip())

		item_code = _resolve_item_code(candidates, entry)

		if not item_code:
			frappe.log_error(
				f"LazyChat Order {lazychat_order_id}: Could not match item for candidates {candidates} in ERPNext",
				"LazyChat Order Fetch - Item Not Found",
			)
			continue

		rate = float(entry.get("rate") or entry.get("price") or 0)
		qty = float(entry.get("quantity") or 1)

		so_items.append({
			"item_code": item_code,
			"qty": qty,
			"rate": rate,
			"delivery_date": delivery_date,
			"warehouse": settings.default_warehouse or None,
		})

	if not so_items:
		return None

	company = settings.default_company or frappe.defaults.get_global_default("company")
	currency = settings.default_currency or frappe.defaults.get_global_default("currency") or "BDT"
	price_list = settings.default_price_list or "Standard Selling"

	so_payload = {
		"doctype": "Sales Order",
		"customer": customer,
		"company": company,
		"selling_price_list": price_list,
		"currency": currency,
		"delivery_date": delivery_date,
		"po_no": lazychat_order_id,
		"items": so_items,
	}

	# Set mandatory sales_type field if present on Sales Order
	if frappe.get_meta("Sales Order").has_field("sales_type"):
		so_payload["sales_type"] = _get_sales_type_value()

	if contact_person:
		so_payload["contact_person"] = contact_person
	if address_docname:
		so_payload["customer_address"] = address_docname
		so_payload["shipping_address_name"] = address_docname

	so = frappe.get_doc(so_payload)
	so.flags.ignore_permissions = True
	so.insert()
	frappe.db.commit()

	return so.name


@frappe.whitelist()
def fetch_and_process_orders(page: int = 1) -> dict:
	"""
	Calls LazyChat POST Orders API (https://app.lazychat.io/api/v1/orders),
	fetches orders page by page, and creates Sales Orders in ERPNext.
	"""
	settings = frappe.get_single("LazyChat Settings")
	shop_token = settings.get_password("shop_token") if settings.shop_token else None
	api_url = settings.fetch_orders_url or "https://app.lazychat.io/api/v1/orders"

	if not shop_token:
		frappe.throw("LazyChat Shop Token is missing in LazyChat Settings.")

	headers = {
		"Authorization": f"Bearer {shop_token}",
		"Content-Type": "application/json",
		"Accept": "application/json",
	}

	payload = {
		"page": int(page or 1)
	}

	try:
		response = requests.post(api_url, json=payload, headers=headers, timeout=15)
		if not response.ok:
			frappe.log_error(
				f"LazyChat Order Fetch Error (HTTP {response.status_code}): {response.text}",
				"LazyChat Order Fetch Failed",
			)
			frappe.throw(f"LazyChat API returned HTTP {response.status_code}: {response.text[:200]}")

		raw_data = response.json()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "LazyChat Order Fetch Exception")
		frappe.throw(f"Error fetching orders from LazyChat: {str(e)}")

	orders_list = _extract_orders_list(raw_data)

	created_so_list = []
	for order_item in orders_list:
		try:
			so_name = process_single_lazychat_order(order_item)
			if so_name:
				created_so_list.append(so_name)
		except Exception:
			order_id = order_item.get("invoice_number") or order_item.get("id") if isinstance(order_item, dict) else str(order_item)
			frappe.log_error(
				frappe.get_traceback(),
				f"LazyChat Order Processing Error for ID {order_id}",
			)

	settings.db_set("last_order_fetch_datetime", frappe.utils.now_datetime())

	return {
		"page": page,
		"fetched": len(orders_list),
		"created": len(created_so_list),
		"sales_orders": created_so_list,
	}


def scheduled_fetch_orders():
	"""
	Cron task executed every 10 minutes by Frappe scheduler.
	Fetches page 1 of orders from LazyChat.
	"""
	settings = frappe.get_single("LazyChat Settings")
	if not settings.enable_auto_fetch_orders:
		return

	try:
		fetch_and_process_orders(page=1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "LazyChat Scheduled Order Fetch Error")
