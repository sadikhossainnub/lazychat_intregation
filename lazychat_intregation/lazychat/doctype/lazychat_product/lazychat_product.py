import requests
import frappe
from frappe.model.document import Document

LAZYCHAT_API_URL = "https://app.lazychat.io/api/v1/products/createOrUpdate"


class LazyChatProduct(Document):
	def on_update(self):
		"""Automatically enqueue sync to LazyChat API when saved."""
		# Prevent recursive loop when updating sync status fields
		if self.flags.in_sync_update:
			return

		frappe.enqueue(
			"lazychat_intregation.lazychat.doctype.lazychat_product.lazychat_product.sync_single_product",
			docname=self.name,
			queue="short",
			enqueue_after_commit=True,
		)

	def get_image_url(self) -> str:
		"""Return absolute image URL for thumbnail_image."""
		if not self.thumbnail_image:
			return ""
		if self.thumbnail_image.startswith("http://") or self.thumbnail_image.startswith("https://"):
			return self.thumbnail_image
		return f"{frappe.utils.get_url()}{self.thumbnail_image}"

	def push_to_lazychat_api(self):
		"""Direct call to push product data to LazyChat API and update document status."""
		settings = frappe.get_single("LazyChat Settings")
		shop_token = settings.get_password("shop_token") if settings.shop_token else None

		if not shop_token:
			self.db_set({
				"sync_status": "Failed",
				"sync_error": "LazyChat Shop Token is missing in LazyChat Settings.",
			})
			frappe.throw("LazyChat Shop Token is missing in LazyChat Settings.")

		payload = {
			"title": self.title,
			"regular_price": float(self.regular_price or 0.0),
			"thumbnail_image": self.get_image_url(),
			"sku": self.sku,
			"brand": self.brand or "",
			"partner_id": self.partner_id or self.sku,
		}

		headers = {
			"Authorization": f"Bearer {shop_token}",
			"Content-Type": "application/json",
			"Accept": "application/json",
		}

		try:
			response = requests.post(LAZYCHAT_API_URL, json=payload, headers=headers, timeout=10)
			if response.ok:
				self.flags.in_sync_update = True
				self.db_set({
					"synced_to_lazychat": 1,
					"sync_status": "Synced",
					"last_sync_datetime": frappe.utils.now_datetime(),
					"sync_error": "",
				})
			else:
				err_msg = f"HTTP {response.status_code}: {response.text}"
				self.flags.in_sync_update = True
				self.db_set({
					"synced_to_lazychat": 0,
					"sync_status": "Failed",
					"sync_error": err_msg[:500],
				})
				frappe.log_error(f"LazyChat Product Sync Failed ({self.name}): {err_msg}", "LazyChat API Error")
		except Exception as e:
			err_msg = str(e)
			self.flags.in_sync_update = True
			self.db_set({
				"synced_to_lazychat": 0,
				"sync_status": "Failed",
				"sync_error": err_msg[:500],
			})
			frappe.log_error(frappe.get_traceback(), f"LazyChat Product Sync Exception ({self.name})")


@frappe.whitelist()
def sync_single_product(docname: str):
	"""Enqueued job helper to sync a single LazyChat Product."""
	if frappe.db.exists("LazyChat Product", docname):
		doc = frappe.get_doc("LazyChat Product", docname)
		doc.push_to_lazychat_api()


@frappe.whitelist()
def generate_lazychat_products_from_items():
	"""
	Utility to pull enabled ERPNext Items into LazyChat Product DocType records,
	and enqueue them for sync.
	"""
	settings = frappe.get_single("LazyChat Settings")
	items = frappe.get_all("Item", filters={"disabled": 0}, fields=["name", "item_code", "item_name", "image", "brand", "standard_rate"])

	created = 0
	updated = 0

	for item in items:
		# Check price from price list if configured
		rate = float(item.standard_rate or 0.0)
		if settings.default_price_list:
			ip = frappe.get_all("Item Price", filters={"item_code": item.item_code, "price_list": settings.default_price_list, "selling": 1}, fields=["price_list_rate"], limit=1)
			if ip and ip[0].price_list_rate:
				rate = float(ip[0].price_list_rate)

		if frappe.db.exists("LazyChat Product", item.item_code):
			doc = frappe.get_doc("LazyChat Product", item.item_code)
			doc.title = item.item_name or item.item_code
			doc.item = item.name
			doc.regular_price = rate
			doc.thumbnail_image = item.image or ""
			doc.brand = item.brand or ""
			doc.partner_id = item.item_code
			doc.save(ignore_permissions=True)
			updated += 1
		else:
			doc = frappe.get_doc({
				"doctype": "LazyChat Product",
				"sku": item.item_code,
				"title": item.item_name or item.item_code,
				"item": item.name,
				"regular_price": rate,
				"thumbnail_image": item.image or "",
				"brand": item.brand or "",
				"partner_id": item.item_code,
			})
			doc.insert(ignore_permissions=True)
			created += 1

	return {"created": created, "updated": updated}
