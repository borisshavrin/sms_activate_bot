from asgiref.sync import sync_to_async
from django.db import models

from services.models import Services
from users.models import Users


class Activations(models.Model):
    id_activation = models.CharField(
        verbose_name='ID активации',
        max_length=128,
        unique=True,
    )

    user = models.ForeignKey(
        Users,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )

    service = models.ForeignKey(
        Services,
        verbose_name='Сервис',
        on_delete=models.CASCADE,
    )

    created = models.DateTimeField(
        verbose_name='Создан',
        auto_now_add=True,
    )

    number = models.IntegerField(
        verbose_name='Номер',
        blank=True,
        default=0,
    )

    sms = models.IntegerField(
        verbose_name='Смс-код',
        blank=True,
        default=0,
    )

    class Meta:
        ordering = ('-created',)            # сортировка по умолчанию от более новых к старым заказам


    @staticmethod
    @sync_to_async
    def create_activation(id_activation, user, service, number, sms):
        activation = Activations.objects.create(
                id_activation=id_activation,
                user=user,
                service=service,
                number=number,
                sms=sms
        )
        activation.save()
