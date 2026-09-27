app_name = "lazychat_intregation"
app_title = "LazyChat"
app_publisher = "PTB"
app_description = "LazyChat Intregation with ERPNext for item create, customer create and sales Order creation"
app_email = "sayedtkg@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "lazychat_intregation",
# 		"logo": "/assets/lazychat_intregation/logo.png",
# 		"title": "LazyChat",
# 		"route": "/lazychat_intregation",
# 		"has_permission": "lazychat_intregation.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lazychat_intregation/css/lazychat_intregation.css"
# app_include_js = "/assets/lazychat_intregation/js/lazychat_intregation.js"

# include js, css files in header of web template
# web_include_css = "/assets/lazychat_intregation/css/lazychat_intregation.css"
# web_include_js = "/assets/lazychat_intregation/js/lazychat_intregation.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lazychat_intregation/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

doctype_js = {
	"Item": "public/js/item.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lazychat_intregation/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lazychat_intregation.utils.jinja_methods",
# 	"filters": "lazychat_intregation.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lazychat_intregation.install.before_install"
# after_install = "lazychat_intregation.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lazychat_intregation.uninstall.before_uninstall"
# after_uninstall = "lazychat_intregation.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lazychat_intregation.utils.before_app_install"
# after_app_install = "lazychat_intregation.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lazychat_intregation.utils.before_app_uninstall"
# after_app_uninstall = "lazychat_intregation.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "lazychat_intregation.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lazychat_intregation.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Item": {
		# Push create/update to LazyChat API whenever an Item is saved
		"on_update": "lazychat_intregation.utils.product_sync.on_item_update",
	},
	"Item Price": {
		# Re-sync product price to LazyChat API whenever Item Price changes or is deleted
		"on_update": "lazychat_intregation.utils.product_sync.on_item_price_update",
		"on_trash": "lazychat_intregation.utils.product_sync.on_item_price_update",
	},
	"Stock Ledger Entry": {
		# Re-sync product stock qty to LazyChat API whenever inventory changes
		"on_submit": "lazychat_intregation.utils.product_sync.on_stock_ledger_update",
		"on_cancel": "lazychat_intregation.utils.product_sync.on_stock_ledger_update",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
		"*/10 * * * *": [
			"lazychat_intregation.utils.order_fetch.scheduled_fetch_orders"
		]
	}
}

# Testing
# -------

# before_tests = "lazychat_intregation.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "lazychat_intregation.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lazychat_intregation.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lazychat_intregation.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lazychat_intregation.utils.before_request"]
# after_request = ["lazychat_intregation.utils.after_request"]

# Job Events
# ----------
# before_job = ["lazychat_intregation.utils.before_job"]
# after_job = ["lazychat_intregation.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lazychat_intregation.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

