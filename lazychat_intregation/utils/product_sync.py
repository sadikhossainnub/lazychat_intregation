import frappe


def item_to_lazychat_product(item_doc) -> dict:
	"""Formats an ERPNext Item doc into LazyChat API product payload structure."""
	return {
		"id": item_doc.name,
		"sku": item_doc.item_code,
		"name": item_doc.item_name or item_doc.item_code,
		"price": float(item_doc.standard_rate or 0),
		"image": item_doc.image or "",
		"brand": item_doc.brand or "",
	}


def sync_item_to_lazychat_product(item_code: str) -> None:
	"""
	When an ERPNext Item is saved, find or create the corresponding 'LazyChat Product'
	document and trigger its sync to LazyChat API.
	"""
	if not frappe.db.exists("Item", item_code):
		return

	item = frappe.get_doc("Item", item_code)
	if item.disabled:
		return

	settings = frappe.get_single("LazyChat Settings")
	rate = float(item.standard_rate or 0.0)

	if settings.default_price_list:
		ip = frappe.get_all(
			"Item Price",
			filters={"item_code": item_code, "price_list": settings.default_price_list, "selling": 1},
			fields=["price_list_rate"],
			limit=1,
		)
		if ip and ip[0].price_list_rate:
			rate = float(ip[0].price_list_rate)

	if frappe.db.exists("LazyChat Product", item_code):
		doc = frappe.get_doc("LazyChat Product", item_code)
		doc.title = item.item_name or item.item_code
		doc.item = item.name
		doc.regular_price = rate
		doc.thumbnail_image = item.image or ""
		doc.brand = item.brand or ""
		doc.partner_id = item.item_code
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({
			"doctype": "LazyChat Product",
			"sku": item_code,
			"title": item.item_name or item_code,
			"item": item.name,
			"regular_price": rate,
			"thumbnail_image": item.image or "",
			"brand": item.brand or "",
			"partner_id": item_code,
		})
		doc.insert(ignore_permissions=True)


def on_item_update(doc, method=None) -> None:
	"""
	Frappe doc event hook for Item on_update.
	Enqueues background job to create/update LazyChat Product and push to LazyChat.
	"""
	frappe.enqueue(
		"lazychat_intregation.utils.product_sync.sync_item_to_lazychat_product",
		item_code=doc.item_code,
		queue="short",
		enqueue_after_commit=True,
	)


@frappe.whitelist()
def sync_all_products_job() -> None:
	"""
	Whitelisted method called from Desk UI (LazyChat Settings button)
	to trigger bulk product sync.
	"""
	frappe.enqueue(
		"lazychat_intregation.lazychat.doctype.lazychat_product.lazychat_product.generate_lazychat_products_from_items",
		queue="long",
		enqueue_after_commit=True,
	)
