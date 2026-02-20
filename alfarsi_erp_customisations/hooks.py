from . import __version__ as app_version

app_name = "alfarsi_erp_customisations"
app_title = "Alfarsi Erp Customisations"
app_publisher = "Alfarsi"
app_description = "Customisations for Alfarsi ERP"
app_email = "Alfarsi"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/alfarsi_erp_customisations/css/alfarsi_erp_customisations.css"
# app_include_js = "/assets/alfarsi_erp_customisations/js/alfarsi_erp_customisations.js"

# include js, css files in header of web template
# web_include_css = "/assets/alfarsi_erp_customisations/css/alfarsi_erp_customisations.css"
# web_include_js = "/assets/alfarsi_erp_customisations/js/alfarsi_erp_customisations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "alfarsi_erp_customisations/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
				"Delivery Note": "public/js/delivery_note.js",
                "Quotation": "public/js/quotation.js",
                "Purchase Order": "public/js/purchase_order.js"
			}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "alfarsi_erp_customisations.utils.jinja_methods",
#	"filters": "alfarsi_erp_customisations.utils.jinja_filters"
# }
jinja = {
	"methods": "erpnext.accounts.party.get_dashboard_info"
}

# Installation
# ------------

# before_install = "alfarsi_erp_customisations.install.before_install"
# after_install = "alfarsi_erp_customisations.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "alfarsi_erp_customisations.uninstall.before_uninstall"
# after_uninstall = "alfarsi_erp_customisations.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "alfarsi_erp_customisations.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Packing Slip": "alfarsi_erp_customisations.overrides.packing_slip.CustomPackingSlip"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

doc_events = {
	"Leave Application": {
		"on_update_after_submit": "alfarsi_erp_customisations.public.py.leave_application_mark_as_joined.mark_rejoined",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
		"alfarsi_erp_customisations.public.py.brand_sellout_automail.send_scheduled_sellout_mails"
	],
	"cron": {
        "0 8 * * SAT": [
            "alfarsi_erp_customisations.public.py.pending_sales_orders_notification.send_notification_email"
		],
        "0 20 * * *": [
			"alfarsi_erp_customisations.public.py.daily_customer_visit_report_email.send_daily_customer_visit_reports"
		]
	},
}

# scheduler_events = {
#	"all": [
#		"alfarsi_erp_customisations.tasks.all"
#	],
#	"daily": [
#		"alfarsi_erp_customisations.tasks.daily"
#	],
#	"hourly": [
#		"alfarsi_erp_customisations.tasks.hourly"
#	],
#	"weekly": [
#		"alfarsi_erp_customisations.tasks.weekly"
#	],
#	"monthly": [
#		"alfarsi_erp_customisations.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "alfarsi_erp_customisations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "alfarsi_erp_customisations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "alfarsi_erp_customisations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"alfarsi_erp_customisations.auth.validate"
# ]
