import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ParticipantProfile

logger = logging.getLogger("accounts")


# Activity log: one line in logs/activity.log for each login, failed login, logout and
# profile save, never with passwords or profile answers.
@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    logger.info("login: %r (%s)", user.username, user.role)


@receiver(user_login_failed)
def log_failed_login(sender, credentials, **kwargs):
    logger.warning("failed login for username %r", credentials.get("username", ""))


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user:
        logger.info("logout: %r", user.username)


@receiver(post_save, sender=ParticipantProfile)
def log_profile_save(sender, instance, created, **kwargs):
    logger.info("profile %s for %r", "created" if created else "changed", instance.user.username)
