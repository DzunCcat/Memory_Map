from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

# custom user creation form
class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('profile_picture', 'bio',)