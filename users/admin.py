from django.contrib import admin

from .models import Users


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('user_id_tg', 'api_key')
