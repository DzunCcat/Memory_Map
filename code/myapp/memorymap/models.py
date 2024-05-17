# from django.db import models
# from django.urls import reverse

# class Category(models.Model):
#     name = models.CharField(max_length=255)
#     author = models.ForeignKey(
#         'auth.settings.AUTH_USER_MODEL',
#         on_delete=models.CASCADE,
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.name

# class Article(models.Model):
#     title = models.CharField(max_length=255)
#     content = models.TextField(max_length=2000)
#     image = models.ImageField(null=True,blank=True,upload_to='article_images/')

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     author = models.ForeignKey(
#         'auth.settings.AUTH_USER_MODEL',
#         on_delete=models.CASCADE
#     )

#     category = models.ForeignKey(
#         Category,
#         on_delete=models.PROTECT,
#     )
    
#     latitude = models.FloatField(null=True, blank=True)
#     longitude = models.FloatField(null=True, blank=True)

#     def __str__(self):
#         return self.title
    
#     def get_absolute_url(self):
#         return reverse('memorymap:detail', kwargs={'pk': self.pk})


from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth import get_user_model
from django.dispatch import receiver

import uuid
import logging


logger = logging.getLogger('memorymap')


User = get_user_model()

@deconstructible
class ThumbnailPath(object):
    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = f'{uuid.uuid4()}.{ext}'
        return f'media/thumbnails/{filename}'
    
# Post Model
class Post(models.Model):
    CONTENT_TYPES = (
        ('tweet', _('Tweet')),
        ('article', _('Article')),
    )

    VISIBILITY_CHOICES = (
        ('public', _('Public')),
        ('private', _('Private')),
        ('custom', _('Custom')),
    )
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=1000)
    content_type = models.CharField(max_length=100, choices=CONTENT_TYPES)
    title = models.CharField(max_length=255, blank=True, null=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)   
    # form setting: content_types = article  add thumbnail 
    thumbnail = models.ImageField(upload_to=ThumbnailPath(), blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)  # UUIDフィールドを追加


    def clean(self):
        if self.content_type == 'tweet':
            if self.title:
                raise ValidationError(_('Tweet posts cannot have a title.'))
            if self.thumbnail:
                raise ValidationError(_('Tweet posts cannot have a thumbnail.'))
        elif self.content_type == 'article':
            if not self.title:
                raise ValidationError(_('Article posts must have a title.'))
            if not self.thumbnail:
                raise ValidationError(_('Article posts must have a thumbnail.'))

    class Meta:
        indexes = [
            models.Index(fields=['created_at', 'author']),
        ]
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        if self.content_type == 'article' and self.title:
            return self.title
        elif self.content_type == 'tweet':
            return f"{self.content[:30]}..."
        else:
            return _('Post not found.')

    #post_detail should be set in view.

    def get_absolute_url(self):
        return reverse('memorymap:post_detail', kwargs={'username': self.author.username, 'uuid': self.uuid})
    
    def delete(self, *args, **kwargs):
        media_files = self.media_post.all()
        for media in media_files:
            media.file.delete()
        media_files.delete()
        
        super().delete(*args, **kwargs)

class PostAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    last_access_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'post')

@receiver(models.signals.post_delete, sender=Post)
def delete_media_when_post_deleted(sender, instance, **kwargs):
    media_files = instance.media_post.all()
    # 関連するMediaファイルを削除
    for media in media_files:
        media.file.delete()

    media_files.delete()
    

    # Add indentation to the code block inside the Post class
    # Add your code here

# Hashtag Model
class Hashtag(models.Model):
    tag = models.CharField(max_length=100, unique=True)

# PostHashtag Model
class PostHashtag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_hashtags')
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='hashtags')

    class Meta:
        unique_together = ('post', 'hashtag')

# Like Model
class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

def validate_file_extension(value):
    import os
    from django.core.files.images import get_image_dimensions
    ext = os.path.splitext(value.name)[1].lower()  # ファイル拡張子を取得
    valid_extensions = {
        'text': ['.txt', '.doc', '.docx', '.pdf'],
        'image': ['.jpg', '.jpeg', '.png'],
        'gif': ['.gif'],
        'video': ['.mp4', '.mov', '.avi'],
        'audio': ['.mp3', '.wav', '.m4a'],
    }
    # メディアタイプに応じてバリデーション
    if not any(ext in valid_extensions[media_type] for media_type in valid_extensions):
        raise ValidationError(_('Unsupported file extension.'))
    # 画像の場合、さらにチェックを行う
    if ext in valid_extensions['image'] or ext in valid_extensions['gif']:
        w, h = get_image_dimensions(value)
        if not w or not h:
            raise ValidationError(_('The image file is corrupted.'))
        
@deconstructible
class MediaPath(object):
    def __call__(self, instance, filename):
        ext = filename.lower().split('.')[-1]
        filename = f'{uuid.uuid4()}.{ext}'
        return f'media/{instance.media_type}/{filename}'

# Media Model
class Media(models.Model):
    MEDIA_TYPES = (
        ('text', _('Text')),
        ('image', _('Image')),
        ('gif', _('GIF')),
        ('video', _('Video')),
        ('audio', _('Audio')),
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_post', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='media_user')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to=MediaPath(), validators=[validate_file_extension])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Media')
        verbose_name_plural = _('Media')


# Repost Model
class Repost(models.Model):
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='original_posts')
    reposted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reposts')
    created_at = models.DateTimeField(auto_now_add=True)

# Comment Model
class Comment(MPTTModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['created_at']

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

# Tag Model
class Tag(models.Model):
    name = models.CharField(max_length=100)

# UserPostTag Model
class UserPostTag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_post_tags')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='user_post_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='post_tags')

# Followers Model
class Follower(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    

    class Meta:
        unique_together = ('follower', 'followed')

# Notification Model
class Notification(models.Model):
    # Define the types of notifications that can occur (like, comment, follow)
    TYPE_CHOICES = (
        ('like', _('Like')),
        ('comment', _('Comment')),
        ('follow', _('Follow')),
    )
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} {self.notification_type} {self.post}"

# DirectMessage Model
class DirectMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"
