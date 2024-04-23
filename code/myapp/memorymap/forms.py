from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User,Post,Comment

# custom user creation form
class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('profile_picture', 'bio',)

# post form
# class PostForm(forms.ModelForm):
#     class Meta:
#         model = Post
#         fields = ['title', 'thumbnail', 'content', 'content_type', 'visibility']
#         widgets = {
#             'content_type': forms.Select(choices=Post.CONTENT_TYPES),
#             'visibility': forms.Select(choices=Post.VISIBILITY_CHOICES),
#         }

class PostForm(forms.ModelForm):
    media = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False, label='Media Files')

    class Meta:
        model = Post
        fields = ['title', 'thumbnail', 'content', 'content_type', 'visibility', 'media']
        widgets = {
            'content_type': forms.Select(choices=Post.CONTENT_TYPES),
            'visibility': forms.Select(choices=Post.VISIBILITY_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['media'].help_text = "Select multiple files"


    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get("content_type")
        thumbnail = cleaned_data.get("thumbnail")
        if content_type == 'article' and not thumbnail:
            self.add_error('thumbnail', 'Thumbnail is required for articles.')

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']