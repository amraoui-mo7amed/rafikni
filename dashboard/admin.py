from django.contrib import admin
from .models import (
    EmailConfiguration,
    ChildMedicalCase,
    AdultMedicalCase,
    ElderlyMedicalCase,
)


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "email_host", "email_host_user", "is_active")
    list_editable = ("is_active",)


@admin.register(ChildMedicalCase)
class ChildMedicalCaseAdmin(admin.ModelAdmin):
    list_display = ("user", "aphasie", "intellectual_disability")
    list_filter = ("aphasie", "intellectual_disability")
    search_fields = ("user__username", "user__email", "disorders", "syndromes")


@admin.register(AdultMedicalCase)
class AdultMedicalCaseAdmin(admin.ModelAdmin):
    list_display = ("user", "aphasie")
    list_filter = ("aphasie",)
    search_fields = ("user__username", "user__email")


@admin.register(ElderlyMedicalCase)
class ElderlyMedicalCaseAdmin(admin.ModelAdmin):
    list_display = ("user", "aphasie", "alzheimer", "parkinson")
    list_filter = ("aphasie", "alzheimer", "parkinson")
    search_fields = ("user__username", "user__email")
