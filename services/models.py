from asgiref.sync import sync_to_async
from django.db import models


class Services(models.Model):
    code = models.CharField(
        verbose_name='Код сервиса',
        max_length=128,
        unique=True,
    )

    callback_name = models.CharField(
        verbose_name='Имя callback',
        max_length=128,
        unique=True,
    )

    name = models.CharField(
        verbose_name='Наименование',
        max_length=128,
        unique=True,
    )

    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=4,
        decimal_places=2,
    )

    class Meta:
        ordering = ['name']

    @staticmethod
    @sync_to_async
    def get_service_by_callback(callback_name):
        service = Services.objects.get(callback_name=callback_name)
        return service

    @staticmethod
    @sync_to_async
    def get_service_by_code(code):
        service = Services.objects.get(code=code)
        return service

    @staticmethod
    def get_callback_name_list():
        services_queryset = Services.objects.all()
        services_callback_name_list = [service.callback_name for service in services_queryset]
        return services_callback_name_list
