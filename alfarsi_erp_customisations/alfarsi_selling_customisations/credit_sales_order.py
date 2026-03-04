import frappe
from frappe.utils import nowdate, getdate


def validate(doc,method):
    SellingCreditControl(doc).validate()


class SellingCreditControl():

    def __init__(self, doc):
        self.doc = doc
        self.customer = doc.customer

        self.customer_credit_limit = 0
        self.customer_credit_days = 0
        self.limit_tolerance = 0

        self.outstanding_amount = 0
        self.order_amount = doc.grand_total

        self.validate_limit = False
        self.validate_days = False

        self.limit_status = "normal"
        self.days_status = "normal"


    def validate(self):
        self.update_customer_limit_details()
        if self.validate_limit:
            self.validate_credit_limit()
        if self.validate_days:
            self.validate_credit_days()
        if self.doc.docstatus == 1:
             self.check_submit_permissions()


    def update_customer_limit_details(self):

        customer_docs = frappe.db.get_value(
            "Customer",
            self.customer ,
            fieldname=["credit_limit", "credit_days", "credit_limit_tolerance", "customer_approval_role"],
            as_dict=True
        )
        settings = frappe.get_cached_doc("Credit Control Settings")

        if customer_docs.credit_limit == 0 and customer_docs.credit_days == 0:
            self.customer_credit_limit = settings.default_credit_limit
            self.customer_credit_days = settings.default_credit_days
            self.limit_tolerance = settings.default_credit_limit_tolerance
            self.approval_role = settings.default_approval_role

            self.validate_limit = True
            self.validate_days = True

        else:
            if customer_docs.credit_limit > 0:
                self.customer_credit_limit = customer_docs.credit_limit
                self.limit_tolerance = (customer_docs.credit_limit_tolerance
                                    if customer_docs.credit_limit_tolerance > 0 else settings.default_credit_limit_tolerance)
                self.validate_limit = True
            else:
                self.validate_limit = False

            if customer_docs.credit_days > 0:
                self.customer_credit_days = customer_docs.credit_days
                self.validate_days = True
            else:
                self.validate_days = False

            self.approval_role = (customer_docs.customer_approval_role
                                  if customer_docs.customer_approval_role is not None else settings.default_approval_role)
            
        self.customer_outstanding = self.get_outstanding()

        self.customer_credit_limit = float(self.customer_credit_limit or 0)
        self.customer_credit_days = int(self.customer_credit_days or 0)
        self.limit_tolerance = float(self.limit_tolerance or 0)


    def validate_credit_limit(self):
        tolerance_amt = self.customer_credit_limit * (self.limit_tolerance / 100)
        total_amt = self.customer_outstanding + self.order_amount
        credit_difference = total_amt - self.customer_credit_limit

        self.doc.custom_within_tolerance_amount = 0
        if credit_difference <= 0:
            self.limit_status = "normal"
            return
        elif credit_difference <= tolerance_amt:
            self.limit_status = "within"        
            frappe.db.set_value("Customer", self.customer, "is_frozen", 1)
            self.doc.custom_within_tolerance_amount = 1
            self.notify_limit_manager()
            frappe.msgprint("Credit limit exceeded. Chief Mentors Approval required to proceed.\nThe account is currently on credit hold as it has exceeded the approved credit limit. Kindly arrange payment of the outstanding amount to proceed further.")

        else:
            self.limit_status = "exceeded"
            frappe.throw("The account is currently on credit hold as it has exceeded the approved credit limit. Kindly arrange payment of the outstanding amount to proceed further.")


    def validate_credit_days(self):
        old_invoice = frappe.get_all(
            "Sales Invoice",
            filters = {
                "customer": self.customer,
                "docstatus": 1,
                "outstanding_amount": (">", 0)
            },
            fields=["due_date"],
            order_by = "due_date asc",
            limit = 1
        )
        if not old_invoice:
            return
        
        due_date = getdate(old_invoice[0].due_date)
        today = getdate(nowdate())
        tolerance_days = 30

        total_days_passed = (today - due_date).days

        exceeded_days = total_days_passed - int(self.customer_credit_days)

        roles = frappe.get_roles()

        self.doc.custom_within_tolerance_days = 0

        if total_days_passed <= 0:
            return
        if total_days_passed <= self.customer_credit_days:
            self.days_status = "normal"
            return
        elif exceeded_days <= tolerance_days:
            self.days_status = "within"
            frappe.db.set_value("Customer", self.customer, "is_frozen", 1)
            self.doc.custom_within_tolerance_days = 1
            self.notify_limit_manager()
            frappe.msgprint("Credit days exceeded. Chief Mentors Approval required to proceed.\nThe account is currently on credit hold as it has exceeded the approved credit period. Kindly arrange payment of the outstanding amount to proceed further.")
        else:
            self.days_status = "exceeded"
            frappe.throw("The account is currently on credit hold as it has exceeded the approved credit limit days. Kindly arrange payment of the outstanding amount to proceed further.")

    def notify_limit_manager(self):
        approval_role = frappe.db.get_value(
            "Customer",
            self.customer,
            "customer_approval_role"
        )
        if not approval_role:
            approval_role = frappe.db.get_single_value("Credit Control Settings", "default_approval_role")
        if not approval_role:
            approval_role = "Chief Mentor"
        
        users = frappe.get_all(
            "Has Role",
            filters={"role": approval_role, "parenttype": "User"},
            pluck = "parent"
        )
        if not users:
            return
        
        emails =frappe.get_all(
            "User",
            filters={"name": ["in", users]},
            pluck = "email"
        )
        if emails:
            message = frappe.render_template(
                "templates/emails/credit_limit.html",
                {"doc": self.doc, "customer": self.customer, "order_amount": self.order_amount, "outstanding_amount": self.customer_outstanding, "credit_limit": self.customer_credit_limit, "credit_difference": self.order_amount + self.customer_outstanding - self.customer_credit_limit}
            )
    
            frappe.sendmail(
                recipients=emails,
                subject="Customer Credit Limit Exceeded – Approval Required",
                message=message,
                now=False
            )


    def get_outstanding(self):

        self.outstanding_amount = 0
        outstandings = frappe.get_all(
            "Sales Invoice",
            filters={
                "customer": self.customer,
                "outstanding_amount": [">", 0],
                "docstatus": 1
            },
            fields = ["outstanding_amount"]
        )
        self.outstanding_amount = sum(o.outstanding_amount for o in outstandings)
        return self.outstanding_amount
    

    def check_submit_permissions(self):
        roles = frappe.get_roles()
        statuses = [self.limit_status, self.days_status]
        if "exceeded" in statuses:
            if not("Finance Manager" in roles or "Chief Mentor" in roles):
                frappe.throw("Only Finance Manager or Chief Mentor can submit this order as the credit limit or days are exceeded beyond the allowed tolerance.")
            return
        if "within" in statuses:
            if not(
                "Chief Mentor" in roles or "Finance Manager" in roles
            ):
                frappe.throw("Only Chief Mentor or Finance Manager can submit this order as the credit limit or days are exceeded but within the allowed tolerance.")
            return
        return
    