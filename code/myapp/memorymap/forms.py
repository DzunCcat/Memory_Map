from django import forms
from .models import User,Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'thumbnail', 'content', 'content_type', 'visibility','parent']
        widgets = {
            'content_type': forms.Select(choices=Post.CONTENT_TYPES),
            'visibility': forms.Select(choices=Post.VISIBILITY_CHOICES),
            'parent': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['thumbnail'].required = False

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get("content_type")
        title = cleaned_data.get("title")
        thumbnail = cleaned_data.get("thumbnail")

        if content_type == 'article':
            if not title:
                self.add_error('title', 'タイトルは記事の場合必須です。')
            if not thumbnail:
                self.add_error('thumbnail', 'サムネイルは記事の場合必須です。')
        elif content_type == 'tweet':
            cleaned_data['title'] = None
            cleaned_data['thumbnail'] = None

        return cleaned_data
    
#postにcomment機能を持たせたため不要
# class CommentForm(forms.ModelForm):
#     class Meta:
#         model = Comment
#         fields = ['content']