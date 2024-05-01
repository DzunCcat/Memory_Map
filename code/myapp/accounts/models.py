from django.contrib.auth.models import AbstractUser
from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group, Permission
from autoslug import AutoSlugField

import logging

logger = logging.getLogger('accounts')

class User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name="memorymap_user_groups",
        help_text="The groups this user belongs to."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="memorymap_user_permissions",
        help_text="Specific permissions for this user."
    )
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    slug = AutoSlugField(populate_from='username', unique=True, always_update=True, allow_unicode=True)

    def save(self, *args, **kwargs):
        try:
            super(User, self).save(*args, **kwargs)

        except IntegrityError as e:
            logger.error(f"Error saving user: {e}")
            raise ValidationError("Database error, unable to save the user.")