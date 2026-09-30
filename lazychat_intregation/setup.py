import frappe

ROLES = ["LazyChat Manager", "LazyChat User"]


def after_install():
	create_roles()


def create_roles():
	"""Create default roles for LazyChat integration if they do not exist."""
	for role_name in ROLES:
		if not frappe.db.exists("Role", role_name):
			role = frappe.get_doc(
				{
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
					"is_custom": 1,
					"disabled": 0,
				}
			)
			role.insert(ignore_permissions=True)
	frappe.db.commit()
