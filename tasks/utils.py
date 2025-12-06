# tasks/utils.py
from datetime import datetime, timezone
from django.shortcuts import get_object_or_404
from django.conf import settings

from tasks.models import Task
from comments.models import Comment
from comments.dynamodb_comments import get_comments_for_task as ddb_get_comments


def load_task(task_id):
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

    # Cloud mode
    return ddb_get_task(task_id), None

def load_comments(task_obj, task_id):
    """Return comment dictionaries for local or cloud mode."""
    if settings.DB_MODE == "local":
        qs = Comment.objects.filter(task=task_obj).order_by("-timestamp")
        return [
            {
                "username": c.author,
                "content": c.text,
                "created_at": c.timestamp,
            }
            for c in qs
        ]
    else:
        return ddb_get_comments(task_id)


def parse_due_date(task_dict, task_obj):
    """Return datetime for local or cloud mode."""
    if settings.DB_MODE == "local":
        return task_obj.due_date
    try:
        return datetime.fromisoformat(task_dict["due_date"])
    except Exception:
        return datetime.now(timezone.utc)


def user_has_permission(profile, task_dict, request_user):
    """Check if user is allowed to edit the task."""
    return profile.role == "MANAGER" or task_dict["assigned_to"] == request_user.username
