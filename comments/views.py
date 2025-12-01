from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from .forms import CommentForm
from .dynamodb_comments import create_comment

from django.contrib import messages

@login_required
def add_comment_view(request, task_id):
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            create_comment(
                task_id=task_id,
                username=request.user.username,
                content=form.cleaned_data["content"]
            )
            messages.success(request, "Comment added!")  # notification
    return redirect("task_edit", task_id=task_id)