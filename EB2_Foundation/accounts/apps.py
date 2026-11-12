from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"

    # connects the activity log (see signals.py)
    def ready(self):
        from . import signals  # noqa: F401
