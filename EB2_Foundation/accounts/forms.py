import logging

from django import forms
from django.conf import settings
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import ParticipantProfile, User

logger = logging.getLogger("accounts")


class StyleFieldsMixin:
    def _style_fields(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


# Log in: after MAX_FAILED_LOGINS wrong passwords in a row, that username is locked out
# for LOCKOUT_MINUTES. A correct login clears the count.
class LoginForm(StyleFieldsMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def _failed_logins_key(self):
        username = self.data.get("username", "").strip().lower()
        ip = self.request.META.get("REMOTE_ADDR", "") if self.request else ""
        return f"failed-logins:{ip}:{username}"

    def clean(self):
        key = self._failed_logins_key()
        if cache.get(key, 0) >= settings.MAX_FAILED_LOGINS:
            logger.warning("login blocked after too many failed attempts: %r", self.data.get("username", ""))
            raise forms.ValidationError(
                f"Too many failed log in attempts. Try again in {settings.LOCKOUT_MINUTES} minutes.",
                code="locked_out",
            )
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            cache.set(key, cache.get(key, 0) + 1, settings.LOCKOUT_MINUTES * 60)
            raise
        cache.delete(key)
        return cleaned


# the three password forms below only add the Bootstrap classes
class ResetRequestForm(StyleFieldsMixin, PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class NewPasswordForm(StyleFieldsMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class ChangePasswordForm(StyleFieldsMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


# Sign up: nobody can register as an admin, the terms box has to be ticked and each
# email can only be used once, so a password reset only goes to one account.
class RegisterForm(StyleFieldsMixin, UserCreationForm):
    ROLE_CHOICES = [
        (User.Role.PARTICIPANT, "Participant (I want to take part in studies)"),
        (User.Role.RESEARCHER, "Researcher (I want to recruit for a study)"),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    email = forms.EmailField()
    accept_terms = forms.BooleanField()

    class Meta:
        model = User
        fields = ("username", "email", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["accept_terms"].label = format_html(
            'I accept the <a href="{}" target="_blank">terms and conditions</a>.', reverse("terms")
        )
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.terms_accepted_at = timezone.now()
        if commit:
            user.save()
        return user


# Profile form: a yes or no on health needs the consent box ticked, and we save when
# it was ticked. Prefer not to say needs no consent.
class ProfileForm(StyleFieldsMixin, forms.ModelForm):
    sensitive_consent = forms.BooleanField(
        required=False,
        label="I agree to you storing my answer about my health.",
    )

    class Meta:
        model = ParticipantProfile
        fields = ("age_band", "education_level", "health_condition", "sensitive_consent")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
        for name in ("age_band", "education_level", "health_condition"):
            self.fields[name].required = True

    def clean(self):
        cleaned = super().clean()
        answered_health = cleaned.get("health_condition") in (
            ParticipantProfile.Health.YES,
            ParticipantProfile.Health.NO,
        )
        if answered_health and not cleaned.get("sensitive_consent"):
            self.add_error(
                "sensitive_consent",
                "Tick this box to save your health answer, or choose 'Prefer not to say'.",
            )
        return cleaned

    def save(self, commit=True):
        profile = super().save(commit=False)
        if not profile.sensitive_consent:
            profile.sensitive_consent_at = None
        elif profile.sensitive_consent_at is None:
            profile.sensitive_consent_at = timezone.now()
        if commit:
            profile.save()
        return profile
