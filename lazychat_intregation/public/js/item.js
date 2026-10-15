frappe.ui.form.on("Item", {
	refresh: function(frm) {
		if (!frm.is_new() && frappe.model.can_read("LazyChat Product")) {
			frappe.db.get_value("LazyChat Product", { item: frm.doc.name }, ["name", "sync_status", "synced_to_lazychat"], function(r) {
				if (r && r.name) {
					var status = r.sync_status || "Pending";
					var indicator_color = status === "Synced" ? "green" : (status === "Failed" ? "red" : "orange");
					
					frm.dashboard.add_indicator(
						__("LazyChat: {0}", [status]),
						indicator_color
					);

					frm.add_custom_button(__("LazyChat Product"), function() {
						frappe.set_route("Form", "LazyChat Product", r.name);
					}, __("View"));

					// Add Sync to LazyChat button
					frm.add_custom_button(__("Sync to LazyChat"), function() {
						frappe.call({
							method: "lazychat_intregation.lazychat.doctype.lazychat_product.lazychat_product.sync_single_product",
							args: { docname: r.name },
							freeze: true,
							freeze_message: __("Syncing product to LazyChat..."),
							callback: function(res) {
								if (!res.exc) {
									frappe.msgprint(__("Product synced to LazyChat successfully!"));
									frm.reload_doc();
								}
							}
						});
					}, __("LazyChat"));
				} else {
					frm.dashboard.add_indicator(__("LazyChat: Not Mapped"), "grey");

					// Add Publish to LazyChat button for unmapped items
					frm.add_custom_button(__("Publish to LazyChat"), function() {
						frappe.confirm(
							__("This will create a new LazyChat Product and sync it. Continue?"),
							function() {
								frappe.call({
									method: "lazychat_intregation.api.products.publish_item_to_lazychat",
									args: { item_code: frm.doc.item_code },
									freeze: true,
									freeze_message: __("Publishing to LazyChat..."),
									callback: function(res) {
										if (!res.exc) {
											frappe.msgprint(__("Item published to LazyChat successfully!"));
											frm.reload_doc();
										}
									}
								});
							}
						);
					}, __("LazyChat"));
				}
			});
		}
	}
});
