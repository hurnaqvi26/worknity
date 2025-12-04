from django import forms

class CommentForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Add a comment..."}),
        label=""
    )
