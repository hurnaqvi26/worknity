from django import forms

class CommentForm(forms.Form):
    content = forms.CharField(
        label="Add a comment",
        widget=forms.Textarea(attrs={"rows": 3})
    )
