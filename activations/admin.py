from django.contrib import admin

from activations.models import Activations


@admin.register(Activations)
class ActivationsAdmin(admin.ModelAdmin):
    list_display = ('id_activation', 'user', 'service', 'created', 'number', 'sms')
