frappe.ui.form.on("LazyChat Settings", {
	refresh: function(frm) {
		frm.add_custom_button(__("Fetch Orders from LazyChat"), function() {
			frappe.call({
				method: "lazychat_intregation.utils.order_fetch.fetch_and_process_orders",
				freeze: true,
				freeze_message: __("Fetching orders from LazyChat API..."),
				callback: function(r) {
					if (r.message) {
						frappe.msgprint(
							__("Fetch complete! Total fetched: {0}, Sales Orders Created: {1}", [
								r.message.fetched,
								r.message.created
							])
						);
						frm.reload_doc();
					}
				}
			});
		}, __("Orders"));

		frm.add_custom_button(__("Sync All Products to LazyChat"), function() {
			frappe.confirm(
				__("Are you sure you want to push all active products to LazyChat?"),
				function() {
					frappe.call({
						method: "lazychat_intregation.utils.product_sync.sync_all_products_job",
						freeze: true,
						freeze_message: __("Enqueuing bulk product sync to LazyChat..."),
						callback: function(r) {
							if (!r.exc) {
								frappe.msgprint(__("Bulk product sync has been queued in the background. Check Error Log for status."));
							}
						}
					});
				}
			);
		}, __("Products")).addClass("btn-primary");
	}
});
