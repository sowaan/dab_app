import frappe
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import (
    PayrollEntry, 
    get_salary_withholdings, 
    remove_payrolled_employees, 
    get_salary_structure, 
    set_fields_to_select, 
    set_searchfield,
    set_filter_conditions,
    set_match_conditions
)
from frappe.utils import date_diff
from frappe.query_builder.functions import Count


class DABPayrollEntry(PayrollEntry):
    def make_filters(self):
        #get all selected projects list if selected
        project_list = [d.projects for d in self.custom_projects] if self.custom_projects else []

        filters = frappe._dict(
            company=self.company,
            branch=self.branch,
            department=self.department,
            designation=self.designation,
            grade=self.grade,
            currency=self.currency,
            start_date=self.start_date,
            end_date=self.end_date,
            # project=self.custom_project_in_employee,
            projects=project_list,  # use all selected projects
            payroll_payable_account=self.payroll_payable_account,
            salary_slip_based_on_timesheet=self.salary_slip_based_on_timesheet,
        )

        if not self.salary_slip_based_on_timesheet:
            filters.update(dict(payroll_frequency=self.payroll_frequency))

        return filters
    
    @frappe.whitelist()
    def fill_employee_details(self):
        filters = self.make_filters()
        employees = get_employee_list(filters=filters, as_dict=True, ignore_match_conditions=True)
        self.set("employees", [])

        if not employees:
            error_msg = _(
                "No employees found for the mentioned criteria:<br>Company: {0}<br> Currency: {1}<br>Payroll Payable Account: {2}<br>Projectin Employee:{3} "
            ).format(
                frappe.bold(self.company),
                frappe.bold(self.currency),
                frappe.bold(self.payroll_payable_account),
                frappe.bold(self.custom_project_in_employee),
            )
            if self.branch:
                error_msg += "<br>" + _("Branch: {0}").format(frappe.bold(self.branch))
            if self.department:
                error_msg += "<br>" + _("Department: {0}").format(frappe.bold(self.department))
            if self.designation:
                error_msg += "<br>" + _("Designation: {0}").format(frappe.bold(self.designation))
            if self.start_date:
                error_msg += "<br>" + _("Start date: {0}").format(frappe.bold(self.start_date))
            if self.end_date:
                error_msg += "<br>" + _("End date: {0}").format(frappe.bold(self.end_date))
            frappe.throw(error_msg, title=_("No employees found"))

        self.set("employees", employees)
        self.number_of_employees = len(self.employees)
        self.update_employees_with_withheld_salaries()

        return self.get_employees_with_unmarked_attendance()
    
    def update_employees_with_withheld_salaries(self):
        withheld_salaries = get_salary_withholdings(self.start_date, self.end_date, pluck="employee")

        for employee in self.employees:
            if employee.employee in withheld_salaries:
                employee.is_salary_withheld = 1
				
    @frappe.whitelist()
    def get_employees_with_unmarked_attendance(self) -> list[dict] | None:
        if not self.validate_attendance:
            return

        unmarked_attendance = []
        employee_details = self.get_employee_and_attendance_details()
        default_holiday_list = frappe.db.get_value(
            "Company", self.company, "default_holiday_list", cache=True
        )

        for emp in self.employees:
            details = next((record for record in employee_details if record.name == emp.employee), None)
            if not details:
                continue

            start_date, end_date = self.get_payroll_dates_for_employee(details)
            holidays = self.get_holidays_count(
                details.holiday_list or default_holiday_list, start_date, end_date
            )
            payroll_days = date_diff(end_date, start_date) + 1
            unmarked_days = payroll_days - (holidays + details.attendance_count)

            if unmarked_days > 0:
                unmarked_attendance.append(
                    {
                        "employee": emp.employee,
                        "employee_name": emp.employee_name,
                        "unmarked_days": unmarked_days,
                    }
                )

        return unmarked_attendance

    def get_employee_and_attendance_details(self) -> list[dict]:
        """Returns a list of employee and attendance details like
        [
                {
                        "name": "HREMP00001",
                        "date_of_joining": "2019-01-01",
                        "relieving_date": "2022-01-01",
                        "holiday_list": "Holiday List Company",
                        "attendance_count": 22
                }
        ]
        """
        employees = [emp.employee for emp in self.employees]

        Employee = frappe.qb.DocType("Employee")
        Attendance = frappe.qb.DocType("Attendance")

        return (
            frappe.qb.from_(Employee)
            .left_join(Attendance)
            .on(
                (Employee.name == Attendance.employee)
                & (Attendance.attendance_date.between(self.start_date, self.end_date))
                & (Attendance.docstatus == 1)
            )
            .select(
                Employee.name,
                Employee.date_of_joining,
                Employee.relieving_date,
                Employee.holiday_list,
                Count(Attendance.name).as_("attendance_count"),
            )
            .where(Employee.name.isin(employees))
            .groupby(Employee.name)
        ).run(as_dict=True)

def get_employee_list(
	filters: frappe._dict,
	searchfield=None,
	search_string=None,
	fields: list[str] | None = None,
	as_dict=True,
	limit=None,
	offset=None,
	ignore_match_conditions=False,
) -> list:
	sal_struct = get_salary_structure(
		filters.company,
		filters.currency,
		filters.salary_slip_based_on_timesheet,
		filters.payroll_frequency,
	)

	if not sal_struct:
		return []

	emp_list = get_filtered_employees(
		sal_struct,
		filters,
		searchfield,
		search_string,
		fields,
		as_dict=as_dict,
		limit=limit,
		offset=offset,
		ignore_match_conditions=ignore_match_conditions,
	)

	if as_dict:
		employees_to_check = {emp.employee: emp for emp in emp_list}
	else:
		employees_to_check = {emp[0]: emp for emp in emp_list}

	return remove_payrolled_employees(employees_to_check, filters.start_date, filters.end_date)

def get_filtered_employees(
	sal_struct,
	filters,
	searchfield=None,
	search_string=None,
	fields=None,
	as_dict=False,
	limit=None,
	offset=None,
	ignore_match_conditions=False,
) -> list:
	SalaryStructureAssignment = frappe.qb.DocType("Salary Structure Assignment")
	Employee = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.from_(Employee)
		.join(SalaryStructureAssignment)
		.on(Employee.name == SalaryStructureAssignment.employee)
		.where(
			(SalaryStructureAssignment.docstatus == 1)
			& (Employee.status != "Inactive")
			& (Employee.company == filters.company)
            #& (Employee.custom_project == filters.project)
			& ((Employee.date_of_joining <= filters.end_date) | (Employee.date_of_joining.isnull()))
			& ((Employee.relieving_date >= filters.start_date) | (Employee.relieving_date.isnull()))
			& (SalaryStructureAssignment.salary_structure.isin(sal_struct))
			& (SalaryStructureAssignment.payroll_payable_account == filters.payroll_payable_account)
			& (filters.end_date >= SalaryStructureAssignment.from_date)
		)
	)   

    # Apply project filter only if provided
	if filters.get("projects"):
		query = query.where(Employee.custom_projects.isin(filters.projects))
          
	query = set_fields_to_select(query, fields)
	query = set_searchfield(query, searchfield, search_string, qb_object=Employee)
	query = set_filter_conditions(query, filters, qb_object=Employee)

	if not ignore_match_conditions:
		query = set_match_conditions(query=query, qb_object=Employee)

	if limit:
		query = query.limit(limit)

	if offset:
		query = query.offset(offset)

	return query.run(as_dict=as_dict)

