import random

from django.core.management.base import BaseCommand
from faker import Faker

from accounts.models import ParticipantProfile, User

# Every demo account uses this password. Demo only, never use it on a real site.
DEMO_PASSWORD = "DemoPass!234"


# Demo data: safe to run more than once
class Command(BaseCommand):
    help = "Create demo accounts (development only)"

    def handle(self, *args, **options):
        fake = Faker("en_GB")
        Faker.seed(42)
        rng = random.Random(42)

        if not User.objects.filter(username="demo_admin").exists():
            User.objects.create_superuser("demo_admin", "admin@example.com", DEMO_PASSWORD)

        # researchers: one approved and one still waiting
        self._researcher("demo_researcher", "researcher@example.com", approved=True)
        self._researcher("demo_pending_researcher", "pending@example.com", approved=False)

        # participants: one fixed one, then five with random fake profiles
        self._participant("demo_participant", "participant@example.com", "18-24", "undergraduate", "no")
        for i in range(1, 6):
            self._participant(
                f"participant{i}",
                fake.email(),
                rng.choice(ParticipantProfile.AgeBand.values),
                rng.choice(ParticipantProfile.Education.values),
                rng.choice(ParticipantProfile.Health.values),
            )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"All demo accounts use the password: {DEMO_PASSWORD}")
        self.stdout.write(
            "Usernames: demo_admin, demo_researcher, demo_pending_researcher, "
            "demo_participant, participant1-5"
        )

    def _researcher(self, username, email, approved):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "role": User.Role.RESEARCHER, "approved": approved},
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    def _participant(self, username, email, age, education, health):
        user, _ = User.objects.get_or_create(
            username=username, defaults={"email": email, "role": User.Role.PARTICIPANT}
        )
        user.set_password(DEMO_PASSWORD)
        user.save()

        # the profile is made when the user is saved, so just fill it in
        profile = user.profile
        profile.age_band = age
        profile.education_level = education
        profile.health_condition = health
        profile.save()
