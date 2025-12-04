from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from .forms import CommentForm
from .models import Comment
from tasks.models import Task

from .dynamodb_comments import add_comment as ddb_add_comment


@login_required
def add_comment_view(request, task_id):

    if request.method != "POST":
        return redirect("task_edit", task_id=task_id)

    form = CommentForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Comment cannot be empty.")
        return redirect("task_edit", task_id=task_id)

    text = form.cleaned_data["text"]

    # LOCAL DATABASE MODE
    if settings.DB_MODE == "local":
        task = get_object_or_404(Task, id=task_id)
        Comment.objects.create(
            task=task,
            author=request.user.username,
            text=text
        )

    # CLOUD MODE (DynamoDB)
    else:
        ddb_add_comment(task_id, request.user.username, text)

    messages.success(request, "Comment added!")
    return redirect("task_edit", task_id=task_id)
