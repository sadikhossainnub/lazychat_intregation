frappe.ui.form.on("LazyChat Product", {
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Sync to LazyChat"), function() {
				frappe.call({
					method: "lazychat_intregation.lazychat.doctype.lazychat_product.lazychat_product.sync_single_product",
					args: { docname: frm.doc.name },
					freeze: true,
					freeze_message: __("Syncing product to LazyChat API..."),
					callback: function(r) {
						if (!r.exc) {
							frappe.msgprint(__("Product sync requested. Refreshing page..."));
							frm.reload_doc();
						}
					}
				}).addClass("btn-primary");
			});
		}
	}
});

frappe.listview_settings["LazyChat Product"] = {
	add_fields: ["sync_status", "synced_to_lazychat"],
	get_indicator: function(doc) {
		if (doc.sync_status === "Synced") {
			return [__("Synced"), "green", "sync_status,=,Synced"];
		} else if (doc.sync_status === "Failed") {
			return [__("Failed"), "red", "sync_status,=,Failed"];
		} else {
			return [__("Pending"), "orange", "sync_status,=,Pending"];
		}
	},
	onload: function(listview) {
		listview.page.add_inner_button(__("Import / Sync Items from ERPNext"), function() {
			frappe.confirm(
				__("Generate or Update LazyChat Products from all active ERPNext Items?"),
				function() {
					frappe.call({
						method: "lazychat_intregation.lazychat.doctype.lazychat_product.lazychat_product.generate_lazychat_products_from_items",
						freeze: true,
						freeze_message: __("Importing ERPNext Items into LazyChat Product..."),
						callback: function(r) {
							if (r.message) {
								frappe.msgprint(
									__("Import complete! Created: {0}, Updated: {1}", [r.message.created, r.message.updated])
								);
								listview.refresh();
							}
						}
					});
				}
			);
		});
	}
};
