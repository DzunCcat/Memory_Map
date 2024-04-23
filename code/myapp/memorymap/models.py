# from django.db import models
# from django.urls import reverse

# class Category(models.Model):
#     name = models.CharField(max_length=255)
#     author = models.ForeignKey(
#         'auth.User',
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
#         'auth.User',
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


from django.db import models,IntegrityError
from django.contrib.auth.models import AbstractUser,Group, Permission
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from mptt.models import MPTTModel, TreeForeignKey

import re
import uuid
import logging


logger = logging.getLogger('memorymap')

# User Model
class User(AbstractUser):

    groups = models.ManyToManyField(
        Group,
        related_name="memorymap_user_groups",  # memorymapアプリのUserモデル専用の逆参照名
        help_text="The groups this user belongs to."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="memorymap_user_permissions",  # memorymapアプリのUserモデル専用の逆参照名
        help_text="Specific permissions for this user."
    )
    # Djangoのデフォルトユーザーモデルを拡張
    # 必要に応じて追加のフィールドをここに定義
    profile_picture = models.ImageField(upload_to='profile_pics/',default='profile_pics/default.jpg', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    slug = models.SlugField(null=True, blank=True, unique=True)  # Slugフィールドの定義

    def save(self, *args, **kwargs):
        try:
            if not self.slug:
                base_slug = slugify(self.username)
                new_slug = base_slug
                counter = 1
                max_attempts = 10
            while User.objects.filter(slug=new_slug).exists():
                if counter >= max_attempts:
                    raise ValidationError(_('Unable to generate a unique slug.'))
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = new_slug
            super(User, self).save(*args, **kwargs)
        except IntegrityError as e:
            # エラーログを出力し、カスタムエラーを発生
            logger.error(f"Error saving user: {e}")
            raise ValidationError("Database error, unable to save the user.")

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
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=1000)
    content_type = models.CharField(max_length=100, choices=CONTENT_TYPES)
    title = models.CharField(max_length=255, blank=True, null=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)   
    # form setting: content_types = article  add thumbnail 
    thumbnail = models.ImageField(blank=True, null=True)
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
        return reverse('post_detail', kwargs={'user_id': self.author.id, 'content_type': self.content_type, 'uuid': self.uuid})

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_posts')
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
        'video': ['.mp4', '.mov', '.avi']
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
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to=MediaPath(), validators=[validate_file_extension])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Media')
        verbose_name_plural = _('Media')


# Repost Model
class Repost(models.Model):
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='original_posts')
    reposted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reposts')
    created_at = models.DateTimeField(auto_now_add=True)

# Comment Model
class Comment(MPTTModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

# Tag Model
class Tag(models.Model):
    name = models.CharField(max_length=100)

# UserPostTag Model
class UserPostTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_post_tags')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='user_post_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='post_tags')

# Followers Model
class Follower(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    

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
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} {self.notification_type} {self.post}"

# DirectMessage Model
class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"
