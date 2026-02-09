from django.contrib import admin
from .models import EmailConfiguration


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "email_host", "email_host_user", "is_active")
    list_editable = ("is_active",)
