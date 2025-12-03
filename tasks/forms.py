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

        # EMPLOYEE = disable all fields except status
        if user_role == "EMPLOYEE":
            self.fields["title"].disabled = True
            self.fields["description"].disabled = True
            self.fields["assigned_to"].disabled = True
            self.fields["due_date"].disabled = True
            # Only status remains editable
