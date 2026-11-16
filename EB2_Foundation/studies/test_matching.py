from datetime import date

from matching import check_eligibility, study_reasons

## These are the studies (values match the choices on ParticipantProfile and Study)
base_study = {
    "allowed_age_bands": ["25-34", "35-44", "45-54", "55-64"],
    "status": "open",
    "allowed_health_conditions": ["no"],
    "application_deadline": date(2027, 1, 13),
    "allowed_education_levels": ["college", "undergraduate", "postgraduate"],
}
accepting_health = {**base_study, "allowed_health_conditions": ["yes", "no"]}

# empty lists mean anyone can take part
open_to_all = {
    **base_study,
    "allowed_age_bands": [],
    "allowed_health_conditions": [],
    "allowed_education_levels": [],
}

## These are the participants
too_young = {
    "age_band": "18-24",
    "health_condition": "no",
    "education_level": "undergraduate",
}
too_old = {
    "age_band": "65+",
    "health_condition": "no",
    "education_level": "undergraduate",
}
unhealthy = {
    "age_band": "35-44",
    "health_condition": "yes",
    "education_level": "undergraduate",
}
health_accept = {
    "age_band": "35-44",
    "health_condition": "yes",
    "education_level": "undergraduate",
}
health_prefer_not = {
    "age_band": "35-44",
    "health_condition": "prefer_not",
    "education_level": "undergraduate",
}
edu = {"age_band": "35-44", "health_condition": "no", "education_level": "secondary"}
unfit_app_2 = {
    "age_band": "18-24",
    "health_condition": "no",
    "education_level": "secondary",
}
eligible = {
    "age_band": "35-44",
    "health_condition": "no",
    "education_level": "undergraduate",
}  # passes everything

print(check_eligibility(too_young, base_study))  # expect (False, ['age_band'])
print(check_eligibility(eligible, base_study))  # expect (True, [])
print(check_eligibility(too_old, base_study))  # expect (False, ['age_band'])
print(check_eligibility(unhealthy, base_study))  # expect (False, ['health_condition'])
print(check_eligibility(health_accept, accepting_health))  # expect (True, [])
print(
    check_eligibility(health_prefer_not, base_study)
)  # expect (False, ['health_condition'])
print(check_eligibility(edu, base_study))  # expect (False, ['education_level'])
print(
    check_eligibility(unfit_app_2, base_study)
)  # expect (False, ['age_band', 'education_level'])
print(check_eligibility(unfit_app_2, open_to_all))  # expect (True, [])

draft_study = {**base_study, "status": "draft"}
closed_study = {**base_study, "status": "closed"}
past_deadline_study = {**base_study, "application_deadline": date(2025, 1, 1)}
deadline_today_study = {**base_study, "application_deadline": date.today()}
no_deadline_study = {**base_study, "application_deadline": None}

print(study_reasons(base_study))  # expect (True, [])
print(study_reasons(draft_study))  # expect (False, ['status'])
print(study_reasons(closed_study))  # expect (False, ['status'])
print(study_reasons(past_deadline_study))  # expect (False, ['application_deadline'])
print(study_reasons(deadline_today_study))  # expect (True, []), last day to apply
print(study_reasons(no_deadline_study))  # expect (True, []), no deadline set
