from asgiref.sync import sync_to_async
from django.db import models


class Users(models.Model):
    user_id_tg = models.CharField(
        verbose_name='ID пользователя tg',
        max_length=128,
        unique=True,
    )

    api_key = models.BinaryField(
        verbose_name='API-ключ',
        max_length=128,
        blank=True,
    )

    @staticmethod
    @sync_to_async
    def create_user(user_id, text):
        user = Users.objects.create(user_id_tg=user_id, api_key=text)
        user.save()

    @sync_to_async
    def update_api_key(self, api_key):
        self.api_key = api_key
        self.save()

    @staticmethod
    @sync_to_async
    def get_user(user_id):
        user = Users.objects.get(user_id_tg=user_id)
        return user
