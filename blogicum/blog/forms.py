from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):
    """Форма создания и редактирования публикации."""

    class Meta:
        model = Post
        exclude = ['author']
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['pub_date'].initial = self.instance.pub_date.strftime(
                '%Y-%m-%dT%H:%M'
            )


class CommentForm(forms.ModelForm):
    """Форма создания комментария."""

    class Meta:
        model = Comment
        fields = ['text']


class UserEditForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
