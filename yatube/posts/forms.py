from django import forms
from django.forms.widgets import Textarea

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': Textarea(attrs={'class': 'form-control'})}
