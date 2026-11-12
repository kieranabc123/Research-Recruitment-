import logging

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail

from .models import ParticipantProfile, User

logger = logging.getLogger("accounts")


# Admin site: approve or reject researchers from the Action menu in the Users list
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "approved", "rejected", "is_active")
    list_filter = ("role", "approved", "rejected", "is_active")
    readonly_fields = ("terms_accepted_at",)
    search_fields = ("username", "email")
    actions = ["approve_researchers", "reject_researchers"]

    fieldsets = UserAdmin.fieldsets + (
        ("Study matching", {"fields": ("role", "approved", "rejected", "terms_accepted_at")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (("Study matching", {"fields": ("role", "approved")}),)

    @admin.action(description="Approve selected researchers")
    def approve_researchers(self, request, queryset):
        count = self._decide(request, queryset, approved=True)
        self.message_user(request, f"{count} researcher(s) approved.")

    @admin.action(description="Reject selected researchers")
    def reject_researchers(self, request, queryset):
        count = self._decide(request, queryset, approved=False)
        self.message_user(request, f"{count} researcher(s) rejected.")

    # one at a time (not update()), so each decision is saved in the admin history and the log
    def _decide(self, request, queryset, approved):
        word = "approved" if approved else "rejected"
        count = 0
        for user in queryset.filter(role=User.Role.RESEARCHER):
            user.approved = approved
            user.rejected = not approved
            user.save(update_fields=["approved", "rejected"])
            self.log_change(request, user, f"Researcher {word}")
            logger.info("researcher %s: %r by %r", word, user.username, request.user.username)
            if user.email:
                send_mail(
                    subject=f"Your researcher account was {word}",
                    message=f"An admin has {word} your researcher account.",
                    from_email=None,
                    recipient_list=[user.email],
                )
            count += 1
        return count


@admin.register(ParticipantProfile)
class ParticipantProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age_band", "education_level", "health_condition", "sensitive_consent")
    list_filter = ("age_band", "education_level", "health_condition")
