from django import forms

STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("IN_PROGRESS", "In Progress"),
    ("COMPLETED", "Completed"),
]

class TaskForm(forms.Form):
    title = forms.CharField(max_length=200, required=True)
    description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True
    )
    assigned_to = forms.CharField(max_length=100, required=True)
    status = forms.ChoiceField(choices=STATUS_CHOICES)
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        required=True
    )

    def __init__(self, *args, user_role=None, **kwargs):
        super().__init__(*args, **kwargs)

        # EMPLOYEE — only edit "status"
        if user_role == "EMPLOYEE":
            # Hide fields instead of disabling (disabled fields do NOT POST)
            for field in ["title", "description", "assigned_to", "due_date"]:
                self.fields[field].widget = forms.HiddenInput()
            
            # status must be editable
            self.fields["status"].disabled = False
