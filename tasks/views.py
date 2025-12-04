from datetime import datetime

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

    return render(request, "tasks/task_form.html", {
        "form": form,
        "action": "Create",
    })


# ---------------------------
# EDIT TASK (MANAGER or ASSIGNED EMPLOYEE)
# ---------------------------
@login_required
def task_edit_view(request, task_id):
    profile = EmployeeProfile.objects.get(user=request.user)

    # Get task depending on mode
    if settings.DB_MODE == "local":
        task_obj = get_object_or_404(Task, pk=task_id)
        task = {
            "task_id": str(task_obj.id),
            "title": task_obj.title,
            "description": task_obj.description,
            "assigned_to": task_obj.assigned_to,
            "status": task_obj.status,
            "due_date": task_obj.due_date,
            "created_by": task_obj.created_by,
        }
    else:
        task = ddb_get_task(task_id)
        task_obj = None  # not used in cloud mode

    # Permission rule
    if profile.role != "MANAGER" and task["assigned_to"] != request.user.username:
        messages.error(request, "You do not have permission to edit this task.")
        return redirect("dashboard")

    # Import comments hybrid logic
    from comments.forms import CommentForm
    from comments.models import Comment
    from comments.dynamodb_comments import get_comments_for_task as ddb_get_comments

    if settings.DB_MODE == "local":
        comments_qs = Comment.objects.filter(task=task_obj).order_by("-timestamp")
        comments = []
        for c in comments_qs:
            comments.append({
                "username": c.author,
                "content": c.text,
                "created_at": c.timestamp,
            })
    else:
        comments = ddb_get_comments(task_id)

    # Parse due_date (already datetime in local mode)
    if settings.DB_MODE == "local":
        due_dt = task_obj.due_date
    else:
        try:
            due_dt = datetime.fromisoformat(task["due_date"])
        except Exception:
            due_dt = datetime.utcnow()

    # POST -> Save updates
    if request.method == "POST":
        form = TaskForm(request.POST, user_role=profile.role)
        if form.is_valid():
            cleaned = form.cleaned_data

            # EMPLOYEE: only update status
            if profile.role == "EMPLOYEE":
                if settings.DB_MODE == "local":
                    task_obj.status = cleaned["status"]
                    task_obj.save()
                else:
                    ddb_update_task(task_id, {
                        "title": task["title"],
                        "description": task["description"],
                        "assigned_to": task["assigned_to"],
                        "due_date": due_dt,
                        "status": cleaned["status"],
                    })
                messages.success(request, "Task status updated!")
                return redirect("dashboard")

            # MANAGER: full update
            if settings.DB_MODE == "local":
                task_obj.title = cleaned["title"]
                task_obj.description = cleaned["description"]
                task_obj.assigned_to = cleaned["assigned_to"]
                task_obj.status = cleaned["status"]
                task_obj.due_date = cleaned["due_date"]
                task_obj.save()
            else:
                ddb_update_task(task_id, cleaned)

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
