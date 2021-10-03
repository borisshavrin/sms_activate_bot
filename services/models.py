from django.db import models


class Services(models.Model):
    code = models.CharField(verbose_name='Код сервиса', max_length=128, unique=True)
    callback_name = models.CharField(verbose_name='Имя callback', max_length=128, unique=True)
    name = models.CharField(verbose_name='Наименование', max_length=128, unique=True)
    price = models.DecimalField(verbose_name='Цена', max_digits=4, decimal_places=2)
