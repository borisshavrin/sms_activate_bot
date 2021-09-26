from django.db import models


class Services(models.Model):
    name = models.CharField(verbose_name='ID пользователя tg', max_length=128, unique=True)
    code = models.CharField(verbose_name='API-ключ', max_length=128, unique=True)
    price = models.DecimalField(verbose_name='Цена', max_length=64)
