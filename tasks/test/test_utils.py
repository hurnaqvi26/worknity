from datetime import datetime, timezone, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from tasks.models import Task
from tasks.utils import (
    load_task,
    parse_due_date,
    user_has_permission,
    update_employee_task,
    update_manager_task,
)
from accounts.models import EmployeeProfile
from django.conf import settings


class UtilsTestCase(TestCase):

    def setUp(self):
        settings.DB_MODE = "local"

        self.user_manager = User.objects.create(username="manager")
        self.user_employee = User.objects.create(username="employee")

        EmployeeProfile.objects.create(user=self.user_manager, role="MANAGER")
        EmployeeProfile.objects.create(user=self.user_employee, role="EMPLOYEE")

        self.task = Task.objects.create(
            title="Test Task",
            description="Testing",
            assigned_to="employee",
            status="PENDING",
            due_date=datetime.now(timezone.utc) + timedelta(days=1),
            created_by="manager",
        )

    # ----------------------------
    # load_task()
    # ----------------------------
    def test_load_task_returns_dict_and_obj(self):
        task_dict, task_obj = load_task(self.task.id)
        self.assertEqual(task_dict["title"], "Test Task")
        self.assertEqual(task_obj.id, self.task.id)

    # ----------------------------
    # parse_due_date()
    # ----------------------------
    def test_parse_due_date_local_mode(self):
        task_dict, task_obj = load_task(self.task.id)
        due = parse_due_date(task_dict, task_obj)
        self.assertTrue(isinstance(due, datetime))

    # ----------------------------
    # user_has_permission()
    # ----------------------------
    def test_user_permission_manager(self):
        profile = EmployeeProfile.objects.get(user=self.user_manager)
        task_dict, _ = load_task(self.task.id)
        self.assertTrue(user_has_permission(profile, task_dict, self.user_manager))

    def test_user_permission_employee(self):
        profile = EmployeeProfile.objects.get(user=self.user_employee)
        task_dict, _ = load_task(self.task.id)
        self.assertTrue(user_has_permission(profile, task_dict, self.user_employee))

    def test_user_permission_denied(self):
        other_user = User.objects.create(username="other")
        EmployeeProfile.objects.create(user=other_user, role="EMPLOYEE")
        profile = EmployeeProfile.objects.get(user=other_user)
        task_dict, _ = load_task(self.task.id)
        self.assertFalse(user_has_permission(profile, task_dict, other_user))

    # ----------------------------
    # update_employee_task()
    # ----------------------------
    def test_employee_can_update_status(self):
        task_dict, task_obj = load_task(self.task.id)
        cleaned = {"status": "IN_PROGRESS", "due_date": task_obj.due_date}

        update_employee_task(task_obj, self.task.id, cleaned, task_obj.due_date)
        task_obj.refresh_from_db()

        self.assertEqual(task_obj.status, "IN_PROGRESS")

    # ----------------------------
    # update_manager_task()
    # ----------------------------
    def test_manager_can_edit_all_fields(self):
        task_dict, task_obj = load_task(self.task.id)
        cleaned = {
            "title": "Updated",
            "description": "Updated desc",
            "assigned_to": "manager",
            "status": "COMPLETED",
            "due_date": task_obj.due_date,
        }

        update_manager_task(task_obj, self.task.id, cleaned)
        task_obj.refresh_from_db()

        self.assertEqual(task_obj.title, "Updated")
        self.assertEqual(task_obj.status, "COMPLETED")
