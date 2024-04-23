from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User,Post

# custom user creation form
class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('profile_picture', 'bio',)

# post form
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'thumbnail', 'content', 'content_type', 'visibility']
        widgets = {
            'content_type': forms.Select(choices=Post.CONTENT_TYPES),
            'visibility': forms.Select(choices=Post.VISIBILITY_CHOICES),
        }

