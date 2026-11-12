import re
from datetime import timedelta

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ProfileForm
from .models import ParticipantProfile, User
from .permissions import role_required

PASSWORD = "a-Good-pass-123"

REGISTER_DATA = {
    "username": "newperson",
    "email": "new@example.com",
    "role": "participant",
    "password1": PASSWORD,
    "password2": PASSWORD,
    "accept_terms": "on",
}


# Signing up
class RegisterTests(TestCase):
    def test_participant_is_approved_and_gets_a_profile(self):
        self.client.post(reverse("accounts:register"), REGISTER_DATA)
        user = User.objects.get(username="newperson")
        self.assertEqual(user.role, "participant")
        self.assertTrue(user.approved)
        self.assertTrue(ParticipantProfile.objects.filter(user=user).exists())

    def test_researcher_starts_unapproved(self):
        self.client.post(reverse("accounts:register"), {**REGISTER_DATA, "role": "researcher"})
        user = User.objects.get(username="newperson")
        self.assertTrue(user.is_researcher)
        self.assertFalse(user.approved)

    def test_nobody_can_register_as_admin(self):
        response = self.client.post(reverse("accounts:register"), {**REGISTER_DATA, "role": "admin"})
        self.assertEqual(response.status_code, 200)  # the form comes back with an error
        self.assertFalse(User.objects.filter(username="newperson").exists())

    def test_terms_must_be_accepted(self):
        data = {k: v for k, v in REGISTER_DATA.items() if k != "accept_terms"}
        self.client.post(reverse("accounts:register"), data)
        self.assertFalse(User.objects.filter(username="newperson").exists())

    def test_the_time_the_terms_were_accepted_is_saved(self):
        self.client.post(reverse("accounts:register"), REGISTER_DATA)
        self.assertIsNotNone(User.objects.get(username="newperson").terms_accepted_at)

    def test_an_email_can_only_be_used_once(self):
        User.objects.create_user("first", "Used@Example.com", PASSWORD)
        response = self.client.post(
            reverse("accounts:register"), {**REGISTER_DATA, "email": "used@example.com"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newperson").exists())

    def test_superuser_is_an_approved_admin(self):
        user = User.objects.create_superuser("boss", "boss@example.com", PASSWORD)
        self.assertEqual(user.role, "admin")
        self.assertTrue(user.approved)


# Every participant gets a profile
class ProfileCreationTests(TestCase):
    def test_participant_made_outside_the_form_gets_a_profile(self):
        user = User.objects.create_user("viaadmin", "a@example.com", PASSWORD)
        self.assertTrue(ParticipantProfile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.age_band, "")

    def test_researchers_and_admins_get_no_profile(self):
        researcher = User.objects.create_user("res", "r@example.com", PASSWORD, role="researcher")
        admin = User.objects.create_superuser("boss", "b@example.com", PASSWORD)
        self.assertFalse(ParticipantProfile.objects.filter(user__in=[researcher, admin]).exists())

    def test_saving_twice_keeps_one_profile(self):
        user = User.objects.create_user("pat", "p@example.com", PASSWORD)
        user.save()
        self.assertEqual(ParticipantProfile.objects.filter(user=user).count(), 1)


# Admin approving researchers
class ApprovalTests(TestCase):
    def test_admin_can_approve_a_researcher(self):
        admin = User.objects.create_superuser("boss", "boss@example.com", PASSWORD)
        researcher = User.objects.create_user("res", "res@example.com", PASSWORD, role="researcher")
        self.assertFalse(researcher.approved)

        self.client.force_login(admin)
        self.client.post(
            reverse("admin:accounts_user_changelist"),
            {"action": "approve_researchers", "_selected_action": [researcher.pk]},
        )
        researcher.refresh_from_db()
        self.assertTrue(researcher.approved)

    def test_admin_can_reject_a_researcher_and_they_are_emailed(self):
        admin = User.objects.create_superuser("boss", "boss@example.com", PASSWORD)
        researcher = User.objects.create_user(
            "res", "res@example.com", PASSWORD, role="researcher", approved=True
        )
        self.client.force_login(admin)
        self.client.post(
            reverse("admin:accounts_user_changelist"),
            {"action": "reject_researchers", "_selected_action": [researcher.pk]},
        )
        researcher.refresh_from_db()
        self.assertFalse(researcher.approved)
        self.assertTrue(researcher.rejected)
        self.assertEqual([m.to for m in mail.outbox], [["res@example.com"]])
        self.assertIn("rejected", mail.outbox[0].subject)

    def test_approving_clears_a_rejection_and_emails_the_researcher(self):
        admin = User.objects.create_superuser("boss", "boss@example.com", PASSWORD)
        researcher = User.objects.create_user(
            "res", "res@example.com", PASSWORD, role="researcher", rejected=True
        )
        self.client.force_login(admin)
        self.client.post(
            reverse("admin:accounts_user_changelist"),
            {"action": "approve_researchers", "_selected_action": [researcher.pk]},
        )
        researcher.refresh_from_db()
        self.assertTrue(researcher.approved)
        self.assertFalse(researcher.rejected)
        self.assertIn("approved", mail.outbox[0].subject)

    def test_approving_leaves_participants_alone(self):
        admin = User.objects.create_superuser("boss", "boss@example.com", PASSWORD)
        participant = User.objects.create_user("pat", "pat@example.com", PASSWORD)
        self.client.force_login(admin)
        self.client.post(
            reverse("admin:accounts_user_changelist"),
            {"action": "approve_researchers", "_selected_action": [participant.pk]},
        )
        participant.refresh_from_db()
        self.assertEqual(participant.role, "participant")

    def test_participant_cannot_use_the_admin_site(self):
        participant = User.objects.create_user("pat", "pat@example.com", PASSWORD)
        self.client.force_login(participant)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)  # sent to the admin login


# The @role_required check
class RoleRequiredTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.participant = User.objects.create_user("pat", "p@example.com", PASSWORD)
        self.approved = User.objects.create_user(
            "ra", "ra@example.com", PASSWORD, role="researcher", approved=True
        )
        self.unapproved = User.objects.create_user("ru", "ru@example.com", PASSWORD, role="researcher")

        @role_required("participant")
        def participants_only(request):
            return "ok"

        @role_required("researcher", approved=True)
        def approved_researchers_only(request):
            return "ok"

        self.participants_only = participants_only
        self.approved_researchers_only = approved_researchers_only

    def request_as(self, user):
        request = self.factory.get("/anything/")
        request.user = user
        return request

    def test_right_role_gets_through(self):
        self.assertEqual(self.participants_only(self.request_as(self.participant)), "ok")
        self.assertEqual(self.approved_researchers_only(self.request_as(self.approved)), "ok")

    def test_wrong_role_is_blocked(self):
        with self.assertRaises(PermissionDenied):
            self.participants_only(self.request_as(self.approved))
        with self.assertRaises(PermissionDenied):
            self.approved_researchers_only(self.request_as(self.participant))

    def test_unapproved_researcher_is_blocked(self):
        with self.assertRaises(PermissionDenied):
            self.approved_researchers_only(self.request_as(self.unapproved))

    def test_logged_out_person_goes_to_login(self):
        response = self.participants_only(self.request_as(AnonymousUser()))
        self.assertEqual(response.status_code, 302)


# The pages
class PageTests(TestCase):
    def test_home_page_loads(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_dashboard_needs_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_participant_sees_the_dashboard(self):
        user = User.objects.create_user("pat", "p@example.com", PASSWORD)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("accounts:dashboard")).status_code, 200)

    def test_login_works(self):
        User.objects.create_user("pat", "p@example.com", PASSWORD)
        response = self.client.post(reverse("accounts:login"), {"username": "pat", "password": PASSWORD})
        self.assertRedirects(response, reverse("accounts:dashboard"))


# Forgot password and change password
class PasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("pat", "pat@example.com", PASSWORD)

    def test_reset_link_lets_you_choose_a_new_password(self):
        self.client.post(reverse("accounts:password_reset"), {"email": "pat@example.com"})
        self.assertEqual(len(mail.outbox), 1)

        link = re.search(r"http://testserver(\S+)", mail.outbox[0].body).group(1)
        response = self.client.get(link, follow=True)  # Django swaps the link for a form address
        new_password = "another-Good-pass-9"
        self.client.post(
            response.redirect_chain[-1][0], {"new_password1": new_password, "new_password2": new_password}
        )

        self.assertTrue(self.client.login(username="pat", password=new_password))

    def test_unknown_email_sends_nothing_and_says_nothing(self):
        response = self.client.post(reverse("accounts:password_reset"), {"email": "nobody@example.com"})
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_logged_in_user_can_change_their_password(self):
        self.client.force_login(self.user)
        new_password = "another-Good-pass-9"
        self.client.post(
            reverse("accounts:password_change"),
            {"old_password": PASSWORD, "new_password1": new_password, "new_password2": new_password},
        )
        self.assertTrue(self.client.login(username="pat", password=new_password))

    def test_change_password_needs_login(self):
        response = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(response.status_code, 302)


# The activity log
class ActivityLogTests(TestCase):
    def test_login_is_logged(self):
        User.objects.create_user("pat", "pat@example.com", PASSWORD)
        with self.assertLogs("accounts", level="INFO") as logs:
            self.client.post(reverse("accounts:login"), {"username": "pat", "password": PASSWORD})
        self.assertIn("login: 'pat'", logs.output[0])

    def test_failed_login_is_logged_without_the_password(self):
        User.objects.create_user("pat", "pat@example.com", PASSWORD)
        with self.assertLogs("accounts", level="WARNING") as logs:
            self.client.post(reverse("accounts:login"), {"username": "pat", "password": "wrong-pass-1"})
        self.assertIn("failed login for username 'pat'", logs.output[0])
        self.assertNotIn("wrong-pass-1", logs.output[0])

    def test_approval_is_logged_and_added_to_the_admin_history(self):
        admin = User.objects.create_superuser("boss", "boss@example.com", PASSWORD)
        researcher = User.objects.create_user("res", "res@example.com", PASSWORD, role="researcher")
        self.client.force_login(admin)
        with self.assertLogs("accounts", level="INFO") as logs:
            self.client.post(
                reverse("admin:accounts_user_changelist"),
                {"action": "approve_researchers", "_selected_action": [researcher.pk]},
            )
        self.assertTrue(any("researcher approved: 'res' by 'boss'" in line for line in logs.output))
        self.assertTrue(
            LogEntry.objects.filter(
                object_id=str(researcher.pk), change_message="Researcher approved"
            ).exists()
        )


# Profile form and page
class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("pat", "p@example.com", PASSWORD)
        self.profile = self.user.profile
        self.answers = {"age_band": "18-24", "education_level": "college", "health_condition": "prefer_not"}

    def test_health_answer_needs_consent(self):
        form = ProfileForm({**self.answers, "health_condition": "yes"}, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn("sensitive_consent", form.errors)

    def test_health_answer_with_consent_saves_the_time(self):
        data = {**self.answers, "health_condition": "yes", "sensitive_consent": "on"}
        form = ProfileForm(data, instance=self.profile)
        self.assertTrue(form.is_valid())
        self.assertIsNotNone(form.save().sensitive_consent_at)

    def test_prefer_not_to_say_needs_no_consent(self):
        form = ProfileForm(self.answers, instance=self.profile)
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.save().sensitive_consent_at)

    def test_every_answer_is_required(self):
        form = ProfileForm({"age_band": "18-24"}, instance=self.profile)
        self.assertFalse(form.is_valid())

    def test_participant_can_save_their_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:profile"), self.answers)
        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_complete)
        self.assertIsNotNone(self.profile.last_edited_at)

    def test_second_edit_inside_the_cooldown_is_ignored(self):
        self.client.force_login(self.user)
        self.client.post(reverse("accounts:profile"), self.answers)
        response = self.client.post(reverse("accounts:profile"), {**self.answers, "age_band": "65+"})
        self.assertEqual(response.status_code, 200)  # the locked page, not a redirect
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.age_band, "18-24")

    def test_edit_is_allowed_again_after_the_cooldown(self):
        self.client.force_login(self.user)
        self.client.post(reverse("accounts:profile"), self.answers)
        self.profile.refresh_from_db()
        self.profile.last_edited_at = timezone.now() - timedelta(minutes=11)
        self.profile.save()
        self.client.post(reverse("accounts:profile"), {**self.answers, "age_band": "65+"})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.age_band, "65+")

    def test_first_edit_is_never_blocked(self):
        self.assertIsNone(self.profile.next_edit_at)
        self.assertTrue(self.profile.can_edit_now)

    def test_researcher_cannot_open_the_profile_page(self):
        researcher = User.objects.create_user(
            "ra", "ra@example.com", PASSWORD, role="researcher", approved=True
        )
        self.client.force_login(researcher)
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 403)


# Rejected researchers
class RejectionDashboardTests(TestCase):
    def dashboard_for(self, **flags):
        researcher = User.objects.create_user("res", "res@example.com", PASSWORD, role="researcher", **flags)
        self.client.force_login(researcher)
        return self.client.get(reverse("accounts:dashboard")).content.decode()

    def test_rejected_researcher_is_told(self):
        self.assertIn("Your account was not approved.", self.dashboard_for(rejected=True))

    def test_waiting_researcher_is_told_to_wait(self):
        self.assertIn("waiting for admin approval", self.dashboard_for())

    def test_approved_researcher_is_told(self):
        self.assertIn("Your account is approved.", self.dashboard_for(approved=True))


# Too many wrong passwords
class LoginLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user("locky", "locky@example.com", PASSWORD)
        self.url = reverse("accounts:login")

    def tearDown(self):
        cache.clear()

    def wrong_password(self, times):
        for _ in range(times):
            self.client.post(self.url, {"username": "locky", "password": "wrong-pass-1"})

    def test_correct_password_is_refused_after_five_wrong_ones(self):
        self.wrong_password(5)
        response = self.client.post(self.url, {"username": "locky", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Too many failed log in attempts", response.content.decode())

    def test_four_wrong_passwords_do_not_lock_the_account(self):
        self.wrong_password(4)
        response = self.client.post(self.url, {"username": "locky", "password": PASSWORD})
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_a_correct_login_clears_the_count(self):
        self.wrong_password(4)
        self.client.post(self.url, {"username": "locky", "password": PASSWORD})
        self.client.logout()
        self.wrong_password(4)
        response = self.client.post(self.url, {"username": "locky", "password": PASSWORD})
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_the_lockout_is_logged(self):
        self.wrong_password(5)
        with self.assertLogs("accounts", level="WARNING") as logs:
            self.client.post(self.url, {"username": "locky", "password": PASSWORD})
        self.assertTrue(any("login blocked" in line for line in logs.output))
