from django.contrib import admin

from services.models import Services


class ServicesAdmin(admin.ModelAdmin):
    list_display = ('code', 'callback_name', 'name', 'price')


admin.site.register(Services)
