from django import forms

from accounts.models import ParticipantProfile

from .models import Study


def _profile_choices(field_name):
    """Read the options straight from the participant profile, so the two always match."""
    field = ParticipantProfile._meta.get_field(field_name)
    return [(value, label) for value, label in field.choices if value != ""]


class StudyForm(forms.ModelForm):
    allowed_age_bands = forms.MultipleChoiceField(
        label="Age bands that can take part (leave empty for anyone)",
        choices=_profile_choices("age_band"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    allowed_education_levels = forms.MultipleChoiceField(
        label="Education levels that can take part (leave empty for anyone)",
        choices=_profile_choices("education_level"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    allowed_health_conditions = forms.MultipleChoiceField(
        label="Health answers that can take part (leave empty for anyone)",
        choices=_profile_choices("health_condition"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Study
        fields = [
            "title",
            "description",
            "time_commitment_minutes",
            "reward",
            "status",
            "category",
            "max_participants",
            "start_date",
            "end_date",
            "application_deadline",
            "consent_text",
            "allowed_age_bands",
            "allowed_education_levels",
            "allowed_health_conditions",
        ]
        widgets = {
            "start_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "end_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "application_deadline": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }
