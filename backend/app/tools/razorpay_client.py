import logging
from functools import lru_cache

import razorpay

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def get_razorpay_client() -> razorpay.Client | None:
    """Return a singleton Razorpay SDK client, or None when running with dummy credentials."""
    if (
        not settings.razorpay_key_id
        or settings.razorpay_key_id.startswith("rzp_test_dummy")
        or not settings.razorpay_key_secret
        or settings.razorpay_key_secret == "dummy_secret"
    ):
        logger.warning(
            "Razorpay credentials not configured — SDK client disabled. "
            "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env to enable live calls."
        )
        return None

    try:
        client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )
        client.set_app_details({"title": "AI Revenue Recovery Agent", "version": "1.0"})
        logger.info(
            f"Razorpay SDK client initialised (key={settings.razorpay_key_id[:12]}...)"
        )
        return client
    except Exception as exc:
        logger.error(f"Failed to initialise Razorpay SDK client: {exc}")
        return None
