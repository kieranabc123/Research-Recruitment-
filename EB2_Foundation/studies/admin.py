from django.contrib import admin

from .models import Application, Study, StudySession


# Admin site: a study's sessions (the dates reminders go out for) are added on its own page
class StudySessionInline(admin.TabularInline):
    model = StudySession
    extra = 1


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ("title", "researcher", "status", "category", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "researcher__username")
    inlines = [StudySessionInline]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("participant", "study", "status", "applied_at", "consented_at")
    list_filter = ("status",)
