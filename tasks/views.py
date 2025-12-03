from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime

from accounts.models import EmployeeProfile
from accounts.utils import role_required
from .forms import TaskForm

from .dynamodb_tasks import (
    create_task,
    get_all_tasks,
    get_task,
    update_task,
    delete_task,
)


# ---------------------------
# DASHBOARD
# ---------------------------


@login_required
def dashboard_view(request):
    profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)
    tasks = get_all_tasks()

    # Manager analytics
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
    if request.method == "POST":
        form = TaskForm(request.POST, user_role="MANAGER")
        if form.is_valid():
            data = form.cleaned_data
            data["created_by"] = request.user.username

            create_task(data)
            messages.success(request, "Task created successfully!")
            return redirect("dashboard")
    else:
        form = TaskForm(user_role="MANAGER")

    return render(request, "tasks/task_form.html", {
        "form": form,
        "action": "Create"
    })


# ---------------------------
# EDIT TASK (MANAGER or ASSIGNED EMPLOYEE)
# ---------------------------
@login_required
def task_edit_view(request, task_id):
    profile = EmployeeProfile.objects.get(user=request.user)
    task = get_task(task_id)

    # Permission rule
    if profile.role != "MANAGER" and task["assigned_to"] != request.user.username:
        messages.error(request, "You do not have permission to edit this task.")
        return redirect("dashboard")

    # Load comments
    from comments.dynamodb_comments import get_comments_for_task
    from comments.forms import CommentForm

    comments = get_comments_for_task(task_id)

    # Convert due_date ISO string to datetime
    try:
        due_dt = datetime.fromisoformat(task["due_date"])
    except:
        due_dt = datetime.utcnow()

    # POST REQUEST = SAVE UPDATE
    if request.method == "POST":
        form = TaskForm(request.POST, user_role=profile.role)

        if form.is_valid():
            cleaned = form.cleaned_data

            # EMPLOYEE: can only update status
            if profile.role == "EMPLOYEE":
                update_task(task_id, {
                    "title": task["title"],
                    "description": task["description"],
                    "assigned_to": task["assigned_to"],
                    "due_date": due_dt,
                    "status": cleaned["status"],
                })
                messages.success(request, "Task status updated!")
                return redirect("dashboard")

            # MANAGER: full update
            update_task(task_id, cleaned)
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
    delete_task(task_id)
    messages.error(request, "Task deleted!")
    return redirect("dashboard")
