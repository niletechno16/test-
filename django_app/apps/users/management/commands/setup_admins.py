import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.users.models import UserProfile


class Command(BaseCommand):
    help = 'إنشاء حسابات الـ developer والـ owner من الـ environment'

    def handle(self, *args, **kwargs):

        developer_id = os.getenv('DEVELOPER_ID')
        owner_id     = os.getenv('OWNER_ID')

        if not developer_id or not owner_id:
            self.stdout.write('❌ DEVELOPER_ID أو OWNER_ID مش موجودين في الـ environment — تم الإلغاء')
            return

        admins = [
            {'id': developer_id.strip(), 'role': 'developer'},
            {'id': owner_id.strip(),     'role': 'owner'},
        ]

        for a in admins:
            uid = a['id']
            if UserProfile.objects.filter(agent_id=uid).exists():
                self.stdout.write(f'⚠️  ID {uid} موجود بالفعل — تم تخطيه')
                continue

            user = User.objects.create_user(
                username=uid,
                password=uid,
            )
            UserProfile.objects.create(
                user=user,
                agent_id=uid,
                role=a['role'],
                is_first_login=True,
            )
            self.stdout.write(f'✅ تم إنشاء {a["role"]} — ID: {uid}')

        self.stdout.write('🎉 خلص!')
