
from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"

    def ready(self):
        # FLAW 5 - A09:2021
        # Security Logging and Monitoring Failures

        # VULNERABLE CODE:
        # Authentication security signals are not registered.
        # Failed logins are not recorded by the application's
        # dedicated security monitoring mechanism.

        # FIX: Register the security event handlers.
        from . import security_signals

        #pass
