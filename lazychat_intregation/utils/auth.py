import frappe


def validate_bearer_token(token_field: str) -> None:
	"""
	Validate the incoming ``Authorization: Bearer <token>`` header against
	the token stored in LazyChat Settings.

	:param token_field: Field name on LazyChat Settings that holds the expected token.
	:raises frappe.AuthenticationError: If the token is missing or does not match.
	"""
	auth_header = frappe.get_request_header("Authorization") or ""

	if not auth_header.startswith("Bearer "):
		frappe.throw(
			"Missing or malformed Authorization header. Expected: Authorization: Bearer <token>",
			frappe.AuthenticationError,
		)

	provided_token = auth_header[len("Bearer "):]

	settings = frappe.get_single("LazyChat Settings")
	expected_token = settings.get_password(token_field) or ""

	if not expected_token:
		frappe.throw(
			f"LazyChat Settings: '{token_field}' is not configured. "
			"Please set it in LazyChat Settings before using this API.",
			frappe.PermissionError,
		)

	if provided_token != expected_token:
		frappe.throw("Invalid Bearer token", frappe.AuthenticationError)
