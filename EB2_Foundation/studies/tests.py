from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import User

from .models import Application, Study, StudySession

PASSWORD = "x-Good-pass-1"


# Shared setup: a researcher and a participant. make_study() makes an open study unless
# told otherwise.
class StudyTestCase(TestCase):
    def setUp(self):
        self.researcher = User.objects.create_user(
            "res", "r@example.com", PASSWORD, role="researcher", approved=True
        )
        self.participant = User.objects.create_user("pat", "p@example.com", PASSWORD)

    def make_study(self, **changes):
        data = {
            "researcher": self.researcher,
            "title": "A study",
            "description": "Some text",
            "time_commitment_minutes": 10,
            "status": Study.Status.OPEN,
        }
        return Study.objects.create(**{**data, **changes})


# Applications
class ApplicationTests(StudyTestCase):
    def test_one_application_per_study(self):
        study = self.make_study()
        Application.objects.create(participant=self.participant, study=study)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Application.objects.create(participant=self.participant, study=study)

    def test_new_application_is_pending(self):
        application = Application.objects.create(participant=self.participant, study=self.make_study())
        self.assertEqual(application.status, Application.Status.PENDING)


# Study defaults
class StudyDefaultTests(StudyTestCase):
    def test_new_study_is_a_draft_that_accepts_anyone(self):
        study = self.make_study(status=Study.Status.DRAFT)
        self.assertEqual(study.allowed_age_bands, [])
        self.assertEqual(study.allowed_education_levels, [])
        self.assertEqual(study.allowed_health_conditions, [])
        self.assertIsNone(study.application_deadline)

    def test_a_study_belongs_to_a_researcher(self):
        study = self.make_study()
        self.assertEqual(study.researcher, self.researcher)
        self.assertIn(study, self.researcher.studies.all())


# Study sessions
class StudySessionTests(StudyTestCase):
    def test_sessions_come_back_in_date_order(self):
        study = self.make_study()
        later = StudySession.objects.create(study=study, starts_at=timezone.now() + timedelta(days=7))
        sooner = StudySession.objects.create(study=study, starts_at=timezone.now() + timedelta(days=1))
        self.assertEqual(list(study.sessions.all()), [sooner, later])

    def test_deleting_a_study_deletes_its_sessions(self):
        study = self.make_study()
        StudySession.objects.create(study=study, starts_at=timezone.now())
        study.delete()
        self.assertEqual(StudySession.objects.count(), 0)
