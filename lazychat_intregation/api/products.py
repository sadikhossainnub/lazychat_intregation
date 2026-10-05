import frappe
from lazychat_intregation.utils.auth import validate_bearer_token
from lazychat_intregation.utils.product_sync import item_to_lazychat_product


@frappe.whitelist(allow_guest=True)
def get_products():
	"""
	GET /api/method/lazychat_intregation.api.products.get_products

	Returns all active ERPNext Items in LazyChat product format.
	Query Parameters:
	  - page     (int, default 1)
	  - per_page (int, default 100)

	Authentication: Authorization: Bearer <products_api_token>
	"""
	validate_bearer_token("products_api_token")
	
	settings = frappe.get_single("LazyChat Settings")
	if not bool(getattr(settings, "enable_integration", True)):
		frappe.throw("LazyChat Integration is currently disabled", frappe.PermissionError)

	page = max(1, int(frappe.local.form_dict.get("page", 1)))
	per_page = max(1, min(int(frappe.local.form_dict.get("per_page", 100)), 500))
	start = (page - 1) * per_page

	# Only fetch top-level items — variants appear nested inside variations[]
	base_filters = {"disabled": 0, "variant_of": ["is", "not set"]}

	total = frappe.db.count("Item", filters=base_filters)

	items = frappe.get_all(
		"Item",
		filters=base_filters,
		fields=[
			"name", "item_code", "item_name", "description", "brand",
			"image", "item_group", "standard_rate", "weight_per_unit",
			"has_variants", "disabled", "creation", "modified",
		],
		limit=per_page,
		start=start,
		order_by="item_code asc",
	)

	products = []
	for row in items:
		try:
			item_doc = frappe.get_doc("Item", row.item_code)
			products.append(item_to_lazychat_product(item_doc))
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"LazyChat Products API: error formatting item {row.item_code}",
			)

	frappe.response["type"] = "json"
	frappe.response["message"] = {
		"metadata": {
			"total": total,
			"page": page,
			"per_page": per_page,
		},
		"products": products,
	}
