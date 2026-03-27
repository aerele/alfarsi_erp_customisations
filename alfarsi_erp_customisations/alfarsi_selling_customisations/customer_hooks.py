import frappe


def customer_on_update(doc, method):
	old_doc = doc.get_doc_before_save()

	if not old_doc:
		return

	if old_doc.is_frozen == 1 and doc.is_frozen == 0:
		roles = frappe.get_roles()
		if "Chief Mentor" not in roles:
			return

		send_unfreeze_email(doc)


def send_unfreeze_email(doc):
	current_user = frappe.session.user
	sender_mail = frappe.db.get_value("User", current_user, "email")
	sales_person = None

	if doc.custom_sales_person:
		sales_person = doc.custom_sales_person

	elif doc.sales_team:
		sales_person = doc.sales_team[0].sales_person

	email = None

	if sales_person:
		employee = frappe.db.get_value("Sales Person", sales_person, "employee")
		email = frappe.db.get_value("Employee", employee, "user_id")

	if not email:
		frappe.log_error(f"No email for {sales_person}", "Credit Control")
		return

	frappe.sendmail(
		recipients=[email],
		sender=sender_mail,
		reply_to=sender_mail,
		subject="Customer Credit Hold Released",
		message=frappe.render_template(
			"templates/emails/customer_unfreeze.html",
			{
				"customer": doc.name,
				"user": current_user,
			},
		),
	)

	doc.add_comment("Comment", f"Customer unfrozen by {current_user} and email sent to {email}")
