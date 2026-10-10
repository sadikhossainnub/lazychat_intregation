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
				} else {
					frm.dashboard.add_indicator(__("LazyChat: Not Mapped"), "grey");
				}
			});
		}
	}
});
