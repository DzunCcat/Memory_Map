from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Update user slugs'

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            user.save()  # これによりslugフィールドが再生成されます
        self.stdout.write(self.style.SUCCESS('User slugs updated successfully.'))