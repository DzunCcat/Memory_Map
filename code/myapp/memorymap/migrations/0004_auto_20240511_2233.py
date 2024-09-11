# Generated by Django 3.2.25 on 2024-05-11 13:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('memorymap', '0003_alter_media_post'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='user',
            field=models.ForeignKey(default='1', on_delete=django.db.models.deletion.CASCADE, related_name='media_user', to='accounts.user'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='media',
            name='post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='media_post', to='memorymap.post'),
        ),
    ]
