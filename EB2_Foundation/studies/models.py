from django.conf import settings
from django.db import models


# Study model: the allowed_ lists hold the bands the study accepts (values come from the
# choices on ParticipantProfile). An empty list means anyone can take part.
class Study(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    class Category(models.TextChoices):
        SOCIAL_SCIENCES = "social_sciences", "Social sciences"
        HEALTH = "health", "Health"
        PSYCHOLOGY = "psychology", "Psychology"
        OTHER = "other", "Other"

    researcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="studies",
        limit_choices_to={"role": "researcher"},
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    time_commitment_minutes = models.PositiveIntegerField(help_text="How long taking part takes, in minutes.")
    reward = models.CharField(max_length=200, blank=True, help_text="For example: £5 voucher, or no reward.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, blank=True)

    # when the study runs and the last day people can apply
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)

    # the consent form a participant reads before applying
    consent_text = models.TextField(blank=True)

    allowed_age_bands = models.JSONField(default=list, blank=True)
    allowed_education_levels = models.JSONField(default=list, blank=True)
    allowed_health_conditions = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "studies"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# Application model: a participant applying to a study and the researcher's decision.
# consented_at is set when they agree to the consent form.
class Application(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
        limit_choices_to={"role": "participant"},
    )
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)
    consented_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["participant", "study"], name="one_application_per_study"),
        ]
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.participant} -> {self.study} ({self.status})"


# Study session: one date and time a study meets, reminders go out before each one
class StudySession(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="sessions")
    starts_at = models.DateTimeField()

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.study} on {self.starts_at:%d %b %Y %H:%M}"
