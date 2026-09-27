import frappe


def get_item_stock_qty(item_code: str, warehouse: str | None = None) -> float:
	"""
	Calculate actual stock quantity for an item from Bin.
	If warehouse is specified in LazyChat Settings, return stock for that warehouse.
	Otherwise, return sum across all warehouses.
	"""
	if not item_code:
		return 0.0

	if warehouse:
		qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
		return float(qty or 0.0)

	result = frappe.db.sql(
		"SELECT SUM(actual_qty) FROM `tabBin` WHERE item_code = %s",
		(item_code,),
	)
	if result and result[0][0] is not None:
		return float(result[0][0])
	return 0.0


def get_item_price(item_code: str, price_list: str | None = None, fallback_rate: float = 0.0) -> float:
	"""
	Get selling price for an item from Item Price table if default_price_list is set,
	otherwise fallback to standard_rate.
	"""
	if not item_code:
		return float(fallback_rate or 0.0)

	if price_list:
		ip = frappe.get_all(
			"Item Price",
			filters={"item_code": item_code, "price_list": price_list, "selling": 1},
			fields=["price_list_rate"],
			limit=1,
		)
		if ip and ip[0].price_list_rate is not None:
			return float(ip[0].price_list_rate)
	return float(fallback_rate or 0.0)


def item_to_lazychat_product(item_doc) -> dict:
	"""Formats an ERPNext Item doc into LazyChat API product payload structure."""
	settings = frappe.get_single("LazyChat Settings")
	rate = get_item_price(item_doc.item_code, settings.default_price_list, fallback_rate=item_doc.standard_rate or 0.0)
	stock_qty = get_item_stock_qty(item_doc.item_code, settings.default_warehouse)

	return {
		"id": item_doc.name,
		"sku": item_doc.item_code,
		"name": item_doc.item_name or item_doc.item_code,
		"price": rate,
		"regular_price": rate,
		"stock_qty": stock_qty,
		"quantity": stock_qty,
		"stock": stock_qty,
		"in_stock": stock_qty > 0,
		"image": item_doc.image or "",
		"brand": item_doc.brand or "",
	}


def sync_item_to_lazychat_product(item_code: str) -> None:
	"""
	When an ERPNext Item, Item Price, or Stock level changes,
	update the corresponding 'LazyChat Product' document and push to LazyChat API.
	"""
	if not item_code or not frappe.db.exists("Item", item_code):
		return

	item = frappe.get_doc("Item", item_code)
	if item.disabled:
		return

	settings = frappe.get_single("LazyChat Settings")
	rate = get_item_price(item_code, settings.default_price_list, fallback_rate=item.standard_rate or 0.0)
	stock_qty = get_item_stock_qty(item_code, settings.default_warehouse)
	in_stock = 1 if stock_qty > 0 else 0

	if frappe.db.exists("LazyChat Product", item_code):
		doc = frappe.get_doc("LazyChat Product", item_code)
		doc.title = item.item_name or item.item_code
		doc.item = item.name
		doc.regular_price = rate
		doc.stock_qty = stock_qty
		doc.in_stock = in_stock
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
			"stock_qty": stock_qty,
			"in_stock": in_stock,
			"thumbnail_image": item.image or "",
			"brand": item.brand or "",
			"partner_id": item_code,
		})
		doc.insert(ignore_permissions=True)


def on_item_update(doc, method=None) -> None:
	"""Frappe doc event hook for Item on_update."""
	frappe.enqueue(
		"lazychat_intregation.utils.product_sync.sync_item_to_lazychat_product",
		item_code=doc.item_code,
		queue="short",
		enqueue_after_commit=True,
	)


def on_item_price_update(doc, method=None) -> None:
	"""Frappe doc event hook for Item Price on_update and on_trash."""
	settings = frappe.get_single("LazyChat Settings")
	if not bool(getattr(settings, "enable_price_sync", True)):
		return

	if doc.item_code:
		frappe.enqueue(
			"lazychat_intregation.utils.product_sync.sync_item_to_lazychat_product",
			item_code=doc.item_code,
			queue="short",
			enqueue_after_commit=True,
		)


def on_stock_ledger_update(doc, method=None) -> None:
	"""Frappe doc event hook for Stock Ledger Entry on_submit and on_cancel."""
	settings = frappe.get_single("LazyChat Settings")
	if not bool(getattr(settings, "enable_stock_sync", True)):
		return

	if doc.item_code:
		frappe.enqueue(
			"lazychat_intregation.utils.product_sync.sync_item_to_lazychat_product",
			item_code=doc.item_code,
			queue="short",
			enqueue_after_commit=True,
		)


@frappe.whitelist()
def sync_all_products_job() -> None:
	"""Whitelisted method called from Desk UI to trigger bulk product sync."""
	frappe.enqueue(
		"lazychat_intregation.lazychat.doctype.lazychat_product.lazychat_product.generate_lazychat_products_from_items",
		queue="long",
		enqueue_after_commit=True,
	)
