import json
import frappe
from lazychat_intregation.utils.auth import validate_bearer_token
from lazychat_intregation.utils.customer import get_or_create_customer
from lazychat_intregation.utils.order_fetch import _get_sales_type_value, _reserve_stock_for_sales_order


@frappe.whitelist(allow_guest=True)
def create_order():
	"""
	POST /api/method/lazychat_intregation.api.orders.create_order

	Receives a LazyChat order payload and creates a Sales Order in ERPNext.
	If the customer does not exist, they are created automatically along with Contact & Address.

	Authentication: Authorization: Bearer <order_api_token>
	"""
	validate_bearer_token("order_api_token")
	settings = frappe.get_single("LazyChat Settings")
	
	if not bool(getattr(settings, "enable_integration", True)):
		frappe.throw("LazyChat Integration is currently disabled", frappe.PermissionError)

	try:
		data = json.loads(frappe.request.data or "{}")
	except Exception:
		frappe.throw("Invalid JSON in request body", frappe.ValidationError)

	contact = data.get("contact") or {}
	customer_name = (contact.get("name") or "LazyChat Customer").strip()
	phone = (contact.get("phone") or "").strip()
	address = (contact.get("address") or "").strip()
	line_items = data.get("line_items") or []
	delivery_charge = float(data.get("deliveryCharge") or 0)
	lazychat_order_id = str(data.get("invoice_number") or data.get("id") or "").strip()
	note = (data.get("note") or "").strip()
	payment_method = (data.get("payment_method") or "").strip()

	if lazychat_order_id:
		existing_so = (
			frappe.db.get_value("Sales Order", {"invoice_number": lazychat_order_id}, "name")
			or frappe.db.get_value("Sales Order", {"po_no": lazychat_order_id}, "name")
		)
		if existing_so:
			frappe.response["type"] = "json"
			frappe.response["message"] = {
				"status": "success",
				"sales_order": existing_so,
				"message": f"Sales Order {existing_so} already exists for LazyChat Order {lazychat_order_id}.",
			}
			return

	if not line_items:
		frappe.throw("Order payload has no line_items", frappe.ValidationError)

	cust_info = get_or_create_customer(customer_name, phone, address)
	customer = cust_info["customer"]
	contact_person = cust_info.get("contact")
	address_docname = cust_info.get("address")

	delivery_date = frappe.utils.add_days(frappe.utils.today(), 7)
	so_items = []

	for li in line_items:
		candidates = [
			str(li.get("sku") or "").strip(),
			str(li.get("variation_id") or "").strip(),
			str(li.get("product_id") or "").strip(),
		]
		item_code = next((c for c in candidates if c and frappe.db.exists("Item", c)), None)

		if not item_code:
			frappe.log_error(
				f"LazyChat order {lazychat_order_id}: could not match item "
				f"sku={li.get('sku')} / product_id={li.get('product_id')} in ERPNext",
				"LazyChat Order - Item Not Found",
			)
			continue

		so_items.append({
			"item_code": item_code,
			"item_name": li.get("name") or item_code,
			"qty": float(li.get("quantity") or 1),
			"rate": float(li.get("price") or 0),
			"delivery_date": delivery_date,
			"warehouse": settings.default_warehouse or None,
		})

	if not so_items:
		frappe.throw(
			"None of the line_items could be matched to ERPNext Items.",
			frappe.ValidationError,
		)

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

	if frappe.get_meta("Sales Order").has_field("invoice_number"):
		so_payload["invoice_number"] = lazychat_order_id

	if frappe.get_meta("Sales Order").has_field("sales_type"):
		so_payload["sales_type"] = _get_sales_type_value()

	if contact_person:
		so_payload["contact_person"] = contact_person
		try:
			contact_doc = frappe.get_doc("Contact", contact_person)
			so_payload["contact_display"] = (
				getattr(contact_doc, "get_formatted_name", lambda: None)()
				or f"{contact_doc.first_name or ''} {contact_doc.last_name or ''}".strip()
				or contact_doc.name
			)
			contact_mob = getattr(contact_doc, "mobile_no", None)
			contact_ph = getattr(contact_doc, "phone", None)
			if not contact_mob and hasattr(contact_doc, "phone_nos"):
				for pn in contact_doc.phone_nos:
					if pn.is_primary_mobile_no or pn.is_primary_phone:
						contact_mob = pn.phone
						break
				if not contact_mob and contact_doc.phone_nos:
					contact_mob = contact_doc.phone_nos[0].phone

			so_payload["contact_mobile"] = contact_mob or phone or None
			so_payload["contact_phone"] = contact_ph or phone or None
			if getattr(contact_doc, "email_id", None):
				so_payload["contact_email"] = contact_doc.email_id
		except Exception:
			pass
	if address_docname:
		so_payload["customer_address"] = address_docname
		so_payload["shipping_address_name"] = address_docname

	so = frappe.get_doc(so_payload)
	so.flags.ignore_permissions = True
	so.insert()
	frappe.db.commit()

	# Reserve stock for each item in Draft Sales Order
	_reserve_stock_for_sales_order(so)

	frappe.response["type"] = "json"
	frappe.response["message"] = {
		"status": "success",
		"sales_order": so.name,
		"customer": customer,
		"contact": contact_person,
		"address": address_docname,
		"message": f"Sales Order {so.name} created successfully.",
	}
