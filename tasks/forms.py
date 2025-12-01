from django import forms
from accounts.models import EmployeeProfile

STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("IN_PROGRESS", "In progress"),
    ("COMPLETED", "Completed"),
]


class TaskForm(forms.Form):
    title = forms.CharField(max_length=200)
    description = forms.CharField(
        widget=forms.Textarea, required=False
    )
    assigned_to = forms.CharField()  # username of employee
    status = forms.ChoiceField(choices=STATUS_CHOICES)
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
