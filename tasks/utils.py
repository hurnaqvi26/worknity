# tasks/utils.py
from datetime import datetime, timezone
from django.shortcuts import get_object_or_404
from django.conf import settings

from tasks.models import Task
from comments.models import Comment
from comments.dynamodb_comments import get_comments_for_task as ddb_get_comments

# Cloud task getter
if settings.DB_MODE == "cloud":
    from tasks.dynamodb_tasks import get_task as ddb_get_task
    from tasks.dynamodb_tasks import update_task as ddb_update_task


# ----------------------------------------------------------------------
# Load task (local or cloud)
# ----------------------------------------------------------------------
def load_task(task_id):
    """Return (task_dict, task_obj_or_None)."""
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
        return task, task_obj

    return ddb_get_task(task_id), None


# ----------------------------------------------------------------------
# Load comments (local or cloud)
# ----------------------------------------------------------------------
def load_comments(task_obj, task_id):
    if settings.DB_MODE == "local":
        return [
            {
                "username": c.author,
                "content": c.text,
                "created_at": c.timestamp,
            }
            for c in Comment.objects.filter(task=task_obj).order_by("-timestamp")
        ]
    return ddb_get_comments(task_id)


# ----------------------------------------------------------------------
# Parse due date consistently
# ----------------------------------------------------------------------
def parse_due_date(task_dict, task_obj):
    if settings.DB_MODE == "local":
        return task_obj.due_date

    try:
        return datetime.fromisoformat(task_dict["due_date"])
    except Exception:
        return datetime.now(timezone.utc)


# ----------------------------------------------------------------------
# Permission rule
# ----------------------------------------------------------------------
def user_has_permission(profile, task_dict, user):
    return profile.role == "MANAGER" or task_dict["assigned_to"] == user.username


# ----------------------------------------------------------------------
# Update logic depending on role
# ----------------------------------------------------------------------
def update_employee_task(task_obj, task_id, cleaned, due_dt):
    """Employees can only update status & due_date."""
    if settings.DB_MODE == "local":
        task_obj.status = cleaned["status"]
        task_obj.due_date = cleaned["due_date"]
        task_obj.save()
    else:
        ddb_update_task(task_id, {
            "status": cleaned["status"],
            "due_date": due_dt,
        })


def update_manager_task(task_obj, task_id, cleaned):
    """Managers update all fields."""
    if settings.DB_MODE == "local":
        task_obj.title = cleaned["title"]
        task_obj.description = cleaned["description"]
        task_obj.assigned_to = cleaned["assigned_to"]
        task_obj.status = cleaned["status"]
        task_obj.due_date = cleaned["due_date"]
        task_obj.save()
    else:
        ddb_update_task(task_id, cleaned)
