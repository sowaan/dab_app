app_name = "dab_app"
app_title = "DAB App"
app_publisher = "Sowaan Pvt. Ltd"
app_description = "Customizations for Daral Buraq"
app_email = "info@sowaan.com"
app_license = "mit"


# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "dab_app",
# 		"logo": "/assets/dab_app/logo.png",
# 		"title": "DAB App",
# 		"route": "/dab_app",
# 		"has_permission": "dab_app.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# fixtures = [
#     {
#         "doctype": "Custom Field",
#         "filters": [["module", "=", "DAB App"]]
#     },
#     {
#         "doctype": "DocType",
#         "filters": [["custom", "=", 1], ["module", "=", "DAB App"]]
#     }
# ]

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            ["name", "in", ["Vehicle-custom_rental"]]
        ]
    },
    {
        "doctype": "DocType",
        "filters": [["custom", "=", 1], ["module", "=", "DAB App"]]
    }
]



# fixtures = [
# 	{
# 		"doctype":"Custom Field",
# 		"filters":[["module", "=", "DAB App"]]
# 	}
# ]

doc_events = {
    "Purchase Invoice": {
        "on_cancel": "dab_app.api.purchase_invoice_reset_contract_flag.purchase_invoice_reset_contract_flag",
        "on_trash": "dab_app.api.purchase_invoice_reset_contract_flag.purchase_invoice_reset_contract_flag"
    }
}

# include js, css files in header of desk.html
# app_include_css = "/assets/dab_app/css/dab_app.css"
# app_include_js = "/assets/dab_app/js/dab_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/dab_app/css/dab_app.css"
# web_include_js = "/assets/dab_app/js/dab_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dab_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dab_app/public/icons.svg"

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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "dab_app.utils.jinja_methods",
# 	"filters": "dab_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dab_app.install.before_install"
# after_install = "dab_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dab_app.uninstall.before_uninstall"
# after_uninstall = "dab_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dab_app.utils.before_app_install"
# after_app_install = "dab_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dab_app.utils.before_app_uninstall"
# after_app_uninstall = "dab_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dab_app.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Payroll Entry": "dab_app.overrides.dab_payroll_entry.DABPayrollEntry"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# doc_events = {
#     "*": {  # optional: or you can target specific doctypes
#         "before_save": "dab_app.api.backdate_permission.validate_back_date_permission"
#     }
# }


doc_events = {
    "Purchase Invoice": {
        "on_trash": "dab_app.api.supplier_rental.remove_invoicing_history_on_invoice_delete",
        #"before_save": "dab_app.api.backdate_permission.validate_back_date_permission"
        #"validate": "dab_app.api.backdate_permission.check_back_date_permission"
    }
}


# Scheduled Tasks
# ---------------




# scheduler_events = {
# 	"all": [
# 		"dab_app.tasks.all"
# 	],
# 	"daily": [
# 		"dab_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"dab_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dab_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dab_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "dab_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dab_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dab_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dab_app.utils.before_request"]
# after_request = ["dab_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["dab_app.utils.before_job"]
# after_job = ["dab_app.utils.after_job"]

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
# 	"dab_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }






