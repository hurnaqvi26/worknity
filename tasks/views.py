from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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


# Dashboard stays same
@login_required
def dashboard_view(request):
    profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)

    tasks = get_all_tasks()

    return render(request, "tasks/dashboard.html", {
        "profile": profile,
        "tasks": tasks
    })


# Create new task (Manager only)
@role_required(["MANAGER"])
def task_create_view(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():

            data = form.cleaned_data
            data["created_by"] = request.user.username

            create_task(data)
            messages.success(request, "Task created successfully!")  # notification
            return redirect("dashboard")
    else:
        form = TaskForm()

    return render(request, "tasks/task_form.html", {"form": form, "action": "Create"})


# Edit task (Manager or assigned employee)
@login_required
def task_edit_view(request, task_id):
    profile = EmployeeProfile.objects.get(user=request.user)
    task = get_task(task_id)

    # Permission: Only manager or assigned employee
    if profile.role != "MANAGER" and task["assigned_to"] != request.user.username:
        messages.error(request, "You do not have permission to edit this task.")
        return redirect("dashboard")

    # Import comment logic
    from comments.dynamodb_comments import get_comments_for_task
    from comments.forms import CommentForm

    comments = get_comments_for_task(task_id)

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            update_task(task_id, form.cleaned_data)
            messages.info(request, "Task updated successfully!")
            return redirect("dashboard")
    else:
        form = TaskForm(initial={
            "title": task["title"],
            "description": task["description"],
            "assigned_to": task["assigned_to"],
            "status": task["status"],
            "due_date": task["due_date"],
        })

    return render(request, "tasks/task_form.html", {
        "form": form,
        "action": "Update",
        "comments": comments,
        "comment_form": CommentForm(),
        "task_id": task_id,
    })

# Delete task (Admin only)
@role_required(["ADMIN"])
def task_delete_view(request, task_id):
    delete_task(task_id)
    messages.error(request, "Task deleted!")  # red alert
    return redirect("dashboard")


