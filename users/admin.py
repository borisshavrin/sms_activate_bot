from django.contrib import admin

from activations.models import Activations
from .models import Users


class ActivationsInline(admin.TabularInline):
    model = Activations


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('user_id_tg', 'api_key')
    inlines = [
        ActivationsInline,
    ]
