from django.contrib import admin

from .models import Application, Message


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "course", "status", "created_at")
    list_filter = ("status", "course")
    search_fields = ("full_name", "email", "user__username")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("application", "sender", "created_at")
