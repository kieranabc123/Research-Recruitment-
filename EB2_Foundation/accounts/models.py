from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# User model: a role (participant, researcher or admin) and an approved flag. Researchers
# stay unapproved until an admin approves them.
class User(AbstractUser):
    class Role(models.TextChoices):
        PARTICIPANT = "participant", "Participant"
        RESEARCHER = "researcher", "Researcher"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)
    approved = models.BooleanField(
        default=False,
        help_text="Researchers can only post studies once an admin has approved them.",
    )
    rejected = models.BooleanField(default=False, help_text="An admin has turned this researcher down.")
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # superusers made with createsuperuser are always approved admins
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.approved = True
        elif self.role == self.Role.PARTICIPANT:
            self.approved = True
        super().save(*args, **kwargs)

        # every participant gets a profile, however the account was made
        if self.role == self.Role.PARTICIPANT:
            ParticipantProfile.objects.get_or_create(user=self)

    @property
    def is_researcher(self):
        return self.role == self.Role.RESEARCHER


# Participant profile: stored as bands (like 18-24) and not exact values, so we hold
# less personal data.
class ParticipantProfile(models.Model):
    class AgeBand(models.TextChoices):
        A18_24 = "18-24", "18-24"
        A25_34 = "25-34", "25-34"
        A35_44 = "35-44", "35-44"
        A45_54 = "45-54", "45-54"
        A55_64 = "55-64", "55-64"
        A65_PLUS = "65+", "65 or over"

    class Education(models.TextChoices):
        SECONDARY = "secondary", "School (up to GCSE)"
        COLLEGE = "college", "College or A levels"
        UNDERGRADUATE = "undergraduate", "Undergraduate degree"
        POSTGRADUATE = "postgraduate", "Postgraduate degree"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class Health(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        limit_choices_to={"role": "participant"},
    )
    age_band = models.CharField(max_length=10, choices=AgeBand.choices, blank=True)
    education_level = models.CharField(max_length=20, choices=Education.choices, blank=True)
    health_condition = models.CharField(
        max_length=20,
        choices=Health.choices,
        blank=True,
        verbose_name="Do you have a long-term health condition?",
    )

    # health is sensitive data, so we keep a separate consent and when it was given
    sensitive_consent = models.BooleanField(default=False)
    sensitive_consent_at = models.DateTimeField(null=True, blank=True)

    # when the participant last changed their profile, for the edit cooldown
    last_edited_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_complete(self):
        return bool(self.age_band and self.education_level and self.health_condition)

    @property
    def next_edit_at(self):
        if self.last_edited_at is None:
            return None
        return self.last_edited_at + timedelta(minutes=settings.PROFILE_EDIT_COOLDOWN_MINUTES)

    @property
    def can_edit_now(self):
        return self.next_edit_at is None or timezone.now() >= self.next_edit_at

    def __str__(self):
        return f"Profile of {self.user.username}"
