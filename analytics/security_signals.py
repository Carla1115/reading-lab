
import logging

from django.contrib.auth.signals import user_login_failed
from django.core.cache import cache
from django.dispatch import receiver
from django.utils.crypto import salted_hmac


security_logger = logging.getLogger("reading_lab.security")


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """
    Record failed authentication attempts without
    storing passwords or other sensitive credentials.
    """

    username = str(credentials.get("username", "")).lower()

    # Use a pseudonymous account identifier in the logs.
    account_id = salted_hmac(
        "reading-lab-security-events",
        username
    ).hexdigest()[:16]

    security_logger.warning(
        "LOGIN_FAILED account=%s",
        account_id
    )

    # Count repeated failures for basic monitoring.
    cache_key = f"security_failures_{account_id}"

    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, timeout=300)

    if attempts == 5:
        security_logger.error(
            "SUSPICIOUS_LOGIN_ACTIVITY account=%s failures=%s",
            account_id,
            attempts
        )
