# tasks/views.py

from datetime import datetime, timezone
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.models import EmployeeProfile
from accounts.utils import role_required

from tasks.forms import TaskForm
from tasks.models import Task

from tasks.utils import (
    load_task,
    load_comments,
    parse_due_date,
    user_has_permission,
    update_employee_task,
    update_manager_task,
)

TASK_FORM_TEMPLATE = "tasks/task_form.html"

# Cloud imports
if settings.DB_MODE == "cloud":
    from tasks.dynamodb_tasks import (
        create_task as ddb_create_task,
        get_all_tasks as ddb_get_all_tasks,
        delete_task as ddb_delete_task,
    )


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------
@login_required
def dashboard_view(request):
    profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)

    if settings.DB_MODE == "local":
        task_list = Task.objects.all().order_by("-created_at")
        tasks = [
            {
                "task_id": str(t.id),
                "title": t.title,
                "description": t.description,
                "assigned_to": t.assigned_to,
                "status": t.status,
                "due_date": t.due_date,
                "created_by": t.created_by,
            }
            for t in task_list
        ]
    else:
        tasks = ddb_get_all_tasks()

    return render(request, "tasks/dashboard.html", {
        "profile": profile,
        "tasks": tasks,
        "total": len(tasks),
        "completed": sum(t["status"] == "COMPLETED" for t in tasks),
        "in_progress": sum(t["status"] == "IN_PROGRESS" for t in tasks),
        "pending": sum(t["status"] == "PENDING" for t in tasks),
    })


# ----------------------------------------------------------------------
# CREATE
# ----------------------------------------------------------------------
@role_required(["MANAGER"])
def task_create_view(request):
    profile = EmployeeProfile.objects.get(user=request.user)

    if request.method == "POST":
        form = TaskForm(request.POST, user_role=profile.role)
        if form.is_valid():
            data = form.cleaned_data
            data["created_by"] = request.user.username

            if settings.DB_MODE == "local":
                Task.objects.create(**data)
            else:
                ddb_create_task(data)

            messages.success(request, "Task created successfully!")
            return redirect("dashboard")

    else:
        form = TaskForm(user_role=profile.role)

    return render(request, TASK_FORM_TEMPLATE, {"form": form, "action": "Create"})


# ----------------------------------------------------------------------
# EDIT
# ----------------------------------------------------------------------
@login_required
def task_edit_view(request, task_id):
    profile = EmployeeProfile.objects.get(user=request.user)

    # Load task
    task, task_obj = load_task(task_id)

    # Permission check
    if not user_has_permission(profile, task, request.user):
        messages.error(request, "You do not have permission to edit this task.")
        return redirect("dashboard")

    comments = load_comments(task_obj, task_id)
    due_dt = parse_due_date(task, task_obj)

    if request.method == "POST":
        form = TaskForm(request.POST, user_role=profile.role)

        if form.is_valid():
            cleaned = form.cleaned_data

            if profile.role == "EMPLOYEE":
                update_employee_task(task_obj, task_id, cleaned, due_dt)
                messages.success(request, "Task status updated!")
                return redirect("dashboard")

            update_manager_task(task_obj, task_id, cleaned)
            messages.success(request, "Task updated successfully!")
            return redirect("dashboard")

    else:
        form = TaskForm(
            initial={
                "title": task["title"],
                "description": task["description"],
                "assigned_to": task["assigned_to"],
                "status": task["status"],
                "due_date": due_dt,
            },
            user_role=profile.role,
        )

    from comments.forms import CommentForm

    return render(request, TASK_FORM_TEMPLATE, {
        "form": form,
        "action": "Update",
        "comments": comments,
        "comment_form": CommentForm(),
        "task_id": task_id,
    })


# ----------------------------------------------------------------------
# DELETE
# ----------------------------------------------------------------------
@role_required(["ADMIN"])
def task_delete_view(request, task_id):
    if settings.DB_MODE == "local":
        get_object_or_404(Task, pk=task_id).delete()
    else:
        ddb_delete_task(task_id)

    messages.error(request, "Task deleted!")
    return redirect("dashboard")
