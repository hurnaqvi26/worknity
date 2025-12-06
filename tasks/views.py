from datetime import datetime, timezone

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.models import EmployeeProfile
from accounts.utils import role_required
from .forms import TaskForm
from .models import Task


# Keep existing DynamoDB helpers for cloud mode
# Import DynamoDB helpers ONLY when in cloud mode
from tasks.forms import TaskForm
from tasks.utils import (
    load_task,
    load_comments,
    parse_due_date,
    user_has_permission,
)
TASK_FORM_TEMPLATE = "tasks/task_form.html"

if settings.DB_MODE == "cloud":
    from .dynamodb_tasks import (
        create_task as ddb_create_task,
        get_all_tasks as ddb_get_all_tasks,
        get_task as ddb_get_task,
        update_task as ddb_update_task,
        delete_task as ddb_delete_task,
    )


# ---------------------------
# DASHBOARD
# ---------------------------
@login_required
def dashboard_view(request):
    profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)

    if settings.DB_MODE == "local":
        qs = Task.objects.all().order_by("-created_at")
        tasks = []
        for t in qs:
            tasks.append({
                "task_id": str(t.id),
                "title": t.title,
                "description": t.description,
                "assigned_to": t.assigned_to,
                "status": t.status,
                "due_date": t.due_date,
                "created_by": t.created_by,
            })
    else:
        tasks = ddb_get_all_tasks()

    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "COMPLETED")
    in_progress = sum(1 for t in tasks if t["status"] == "IN_PROGRESS")
    pending = sum(1 for t in tasks if t["status"] == "PENDING")

    return render(request, "tasks/dashboard.html", {
        "profile": profile,
        "tasks": tasks,
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "pending": pending,
    })


# ---------------------------
# CREATE TASK (MANAGER ONLY)
# ---------------------------
@role_required(["MANAGER"])
def task_create_view(request):
    profile = EmployeeProfile.objects.get(user=request.user)

    if request.method == "POST":
        form = TaskForm(request.POST, user_role=profile.role)
        if form.is_valid():
            data = form.cleaned_data
            data["created_by"] = request.user.username

            if settings.DB_MODE == "local":
                Task.objects.create(
                    title=data["title"],
                    description=data["description"],
                    assigned_to=data["assigned_to"],
                    created_by=data["created_by"],
                    status=data["status"],
                    due_date=data["due_date"],
                )
            else:
                ddb_create_task(data)

            messages.success(request, "Task created successfully!")
            return redirect("dashboard")
    else:
        form = TaskForm(user_role=profile.role)

    return render(request, TASK_FORM_TEMPLATE, {
        "form": form,
        "action": "Create",
    })


# ---------------------------
# EDIT TASK (MANAGER or ASSIGNED EMPLOYEE)
# ---------------------------
# -------------------------------
# @login_required
# def task_edit_view(request, task_id):
#     profile = EmployeeProfile.objects.get(user=request.user)

#     # ---- Helper Functions ----------------------------------------------------
#     def load_task():
#         """Return (task_dict, task_obj_or_None) for local or cloud mode."""
#         if settings.DB_MODE == "local":
#             task_obj_local = get_object_or_404(Task, pk=task_id)
#             return ({
#                 "task_id": str(task_obj_local.id),
#                 "title": task_obj_local.title,
#                 "description": task_obj_local.description,
#                 "assigned_to": task_obj_local.assigned_to,
#                 "status": task_obj_local.status,
#                 "due_date": task_obj_local.due_date,
#                 "created_by": task_obj_local.created_by,
#             }, task_obj_local)
#         return ddb_get_task(task_id), None

#     def user_has_permission(task_data):
#         """Check if user is allowed to edit this task."""
#         return profile.role == "MANAGER" or task_data["assigned_to"] == request.user.username

#     def load_comments(task_obj):
#         """Load comments depending on DB mode."""
#         from comments.forms import CommentForm
#         from comments.models import Comment
#         from comments.dynamodb_comments import get_comments_for_task as ddb_get_comments

#         if settings.DB_MODE == "local":
#             return [
#                 {
#                     "username": c.author,
#                     "content": c.text,
#                     "created_at": c.timestamp
#                 }
#                 for c in Comment.objects.filter(task=task_obj).order_by("-timestamp")
#             ]
#         return ddb_get_comments(task_id)

#     def parse_due_date(task_data, task_obj):
#         """Ensure due_date is always a datetime."""
#         if settings.DB_MODE == "local":
#             return task_obj.due_date
#         try:
#             return datetime.fromisoformat(task_data["due_date"])
#         except Exception:
#             return datetime.now(timezone.utc)

#     def update_task_employee(task_obj, cleaned, task_data, due_dt):
#         """Employee can only update status & due_date."""
#         if settings.DB_MODE == "local":
#             task_obj.status = cleaned["status"]
#             task_obj.due_date = cleaned["due_date"]
#             task_obj.save()
#         else:
#             ddb_update_task(task_id, {
#                 "title": task_data["title"],
#                 "description": task_data["description"],
#                 "assigned_to": task_data["assigned_to"],
#                 "due_date": due_dt,
#                 "status": cleaned["status"],
#             })

#     def update_task_manager(task_obj, cleaned):
#         """Manager updates full task."""
#         if settings.DB_MODE == "local":
#             for field in ["title", "description", "assigned_to", "status", "due_date"]:
#                 setattr(task_obj, field, cleaned[field])
#             task_obj.save()
#         else:
#             ddb_update_task(task_id, cleaned)

# @login_required
# def task_edit_view(request, task_id):
#     profile = EmployeeProfile.objects.get(user=request.user)

#     # Load task (now handled by utils)
#     task, task_obj = load_task(task_id)

#     if not user_has_permission(profile, task, request.user):
#         messages.error(request, "You do not have permission to edit this task.")
#         return redirect("dashboard")

#     comments = load_comments(task_obj, task_id)
#     due_dt = parse_due_date(task, task_obj)

#     # POST
#     if request.method == "POST":
#         form = TaskForm(request.POST, user_role=profile.role)

#         if form.is_valid():
#             cleaned = form.cleaned_data

#             if profile.role == "EMPLOYEE":
#                 _update_employee_task(task_obj, task_id, cleaned, due_dt)
#                 messages.success(request, "Task status updated!")
#                 return redirect("dashboard")

#             _update_manager_task(task_obj, task_id, cleaned)
#             messages.success(request, "Task updated successfully!")
#             return redirect("dashboard")

#     else:
#         form = TaskForm(
#             initial={
#                 "title": task["title"],
#                 "description": task["description"],
#                 "assigned_to": task["assigned_to"],
#                 "status": task["status"],
#                 "due_date": due_dt,
#             },
#             user_role=profile.role,
#         )

#     return render(request, TASK_FORM_TEMPLATE, {
#         "form": form,
#         "action": "Update",
#         "comments": comments,
#         "comment_form": CommentForm(),
#         "task_id": task_id,
#     })

@login_required
def task_edit_view(request, task_id):
    profile = get_user_profile(request)
    task, task_obj = load_task_data(task_id)
    enforce_permission(profile, task, request)

    comments = load_comments_data(task_obj, task_id)
    due_dt = parse_due_date(task, task_obj)

    if request.method == "POST":
        return handle_post_request(request, profile, task_obj, task_id, due_dt, task)

    form = build_task_form(task, due_dt, profile.role)
    return render_task_form(request, form, comments, task_id)

    # ---- Main Logic ----------------------------------------------------------
    task_data, task_obj = load_task()

    if not user_has_permission(task_data):
        messages.error(request, "You do not have permission to edit this task.")
        return redirect("dashboard")

    comments = load_comments(task_obj)
    due_dt = parse_due_date(task_data, task_obj)

    if request.method == "POST":
        form = TaskForm(request.POST, user_role=profile.role)

        if form.is_valid():
            cleaned = form.cleaned_data

            if profile.role == "EMPLOYEE":
                update_task_employee(task_obj, cleaned, task_data, due_dt)
                messages.success(request, "Task status updated!")
                return redirect("dashboard")

            update_task_manager(task_obj, cleaned)
            messages.success(request, "Task updated successfully!")
            return redirect("dashboard")

    else:
        form = TaskForm(
            initial={
                "title": task_data["title"],
                "description": task_data["description"],
                "assigned_to": task_data["assigned_to"],
                "status": task_data["status"],
                "due_date": due_dt,
            },
            user_role=profile.role,
        )

    return render(request, "tasks/task_form.html", {
        "form": form,
        "action": "Update",
        "comments": comments,
        "comment_form": CommentForm(),
        "task_id": task_id,
    })

# ---------------------------
# DELETE TASK (ADMIN ONLY)
# ---------------------------
@role_required(["ADMIN"])
def task_delete_view(request, task_id):
    if settings.DB_MODE == "local":
        task_obj = get_object_or_404(Task, pk=task_id)
        task_obj.delete()
    else:
        ddb_delete_task(task_id)

    messages.error(request, "Task deleted!")
    return redirect("dashboard")

def _update_employee_task(task_obj, task_id, cleaned, due_dt):
    from tasks.dynamodb_tasks import update_task as ddb_update_task

    if settings.DB_MODE == "local":
        task_obj.status = cleaned["status"]
        task_obj.due_date = cleaned["due_date"]
        task_obj.save()
    else:
        ddb_update_task(task_id, {
            "status": cleaned["status"],
            "due_date": due_dt,
        })


def _update_manager_task(task_obj, task_id, cleaned):
    from tasks.dynamodb_tasks import update_task as ddb_update_task

    if settings.DB_MODE == "local":
        task_obj.title = cleaned["title"]
        task_obj.description = cleaned["description"]
        task_obj.assigned_to = cleaned["assigned_to"]
        task_obj.status = cleaned["status"]
        task_obj.due_date = cleaned["due_date"]
        task_obj.save()
    else:
        ddb_update_task(task_id, cleaned)

