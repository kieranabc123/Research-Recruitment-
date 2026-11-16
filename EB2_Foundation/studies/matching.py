from datetime import date


def study_reasons(study):
    reasons = []

    deadline = study.get("application_deadline")
    if deadline and deadline < date.today():
        reasons.append("application_deadline")
        # print("This study is not available")
    if study["status"] != "open":
        reasons.append("status")
        # print("This study is not available")
    is_open = len(reasons) == 0
    return is_open, reasons


# print(study_reasons(study))


def check_eligibility(participant, study):
    failed = []

    if (
        study["allowed_age_bands"]
        and participant["age_band"] not in study["allowed_age_bands"]
    ):
        failed.append("age_band")

    if (
        study["allowed_health_conditions"]
        and participant["health_condition"] not in study["allowed_health_conditions"]
    ):
        failed.append("health_condition")
        # print("Unfortunately, you do not meet the health requirements")

    if (
        study["allowed_education_levels"]
        and participant["education_level"] not in study["allowed_education_levels"]
    ):
        failed.append("education_level")

    elegible = len(failed) == 0
    return elegible, failed
