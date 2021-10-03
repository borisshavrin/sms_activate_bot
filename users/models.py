from django.db import models


class Users(models.Model):
    user_id_tg = models.CharField(verbose_name='ID пользователя tg', max_length=128, unique=True)
    api_key = models.CharField(verbose_name='API-ключ', max_length=128, blank=True)
