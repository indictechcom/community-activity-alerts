"""
Validation for annotation fields (description and relevant link).

Keep the rules and messages in sync with the frontend:
frontend/src/utils/annotationValidation.js
"""

import re
from urllib.parse import urlsplit

# ---------------------------------------------------------------------------
# Description
# ---------------------------------------------------------------------------

DESCRIPTION_MIN_CHARS = 10
DESCRIPTION_MAX_WORDS = 50

DESCRIPTION_REQUIRED_MESSAGE = "Description is required."
DESCRIPTION_TOO_SHORT_MESSAGE = f"Description must be at least {DESCRIPTION_MIN_CHARS} characters."
DESCRIPTION_TOO_LONG_MESSAGE = f"Description must be {DESCRIPTION_MAX_WORDS} words or fewer."
DESCRIPTION_INVALID_MESSAGE = "Description must be text."


def validate_description(raw):
    if raw is None:
        return None, DESCRIPTION_REQUIRED_MESSAGE
    if not isinstance(raw, str):
        return None, DESCRIPTION_INVALID_MESSAGE

    value = raw.strip()
    if not value:
        return None, DESCRIPTION_REQUIRED_MESSAGE
    if len(value) < DESCRIPTION_MIN_CHARS:
        return None, DESCRIPTION_TOO_SHORT_MESSAGE
    if len(value.split()) > DESCRIPTION_MAX_WORDS:
        return None, DESCRIPTION_TOO_LONG_MESSAGE
    return value, None


# ---------------------------------------------------------------------------
# Relevant link
# ---------------------------------------------------------------------------

WIKIMEDIA_DOMAINS = (
    "wikipedia.org",
    "wiktionary.org",
    "wikibooks.org",
    "wikinews.org",
    "wikiquote.org",
    "wikisource.org",
    "wikiversity.org",
    "wikivoyage.org",
    "wikimedia.org",
    "wikidata.org",
    "mediawiki.org",
    "wikifunctions.org",
)

INVALID_URL_MESSAGE = (
    "Please enter a valid URL starting with https:// "
    "(e.g. https://en.wikipedia.org/wiki/Example)."
)
NON_WIKIMEDIA_MESSAGE = (
    "Only links to Wikimedia wikis are allowed "
    "(e.g. Wikipedia, Meta-Wiki, Commons, Wikidata)."
)

# Whitespace or control characters anywhere inside the URL
_DISALLOWED_URL_CHARS = re.compile(r"[\s\x00-\x1f\x7f]")


def is_wikimedia_hostname(hostname):
    hostname = hostname.lower().rstrip(".")
    return any(hostname == domain or hostname.endswith("." + domain) for domain in WIKIMEDIA_DOMAINS)


def validate_relevant_link(raw):
    if raw is None:
        return None, None
    if not isinstance(raw, str):
        return None, INVALID_URL_MESSAGE

    value = raw.strip()
    if not value:
        return None, None
    if _DISALLOWED_URL_CHARS.search(value):
        return None, INVALID_URL_MESSAGE

    try:
        parts = urlsplit(value)
        hostname = parts.hostname
        parts.port  # raises ValueError for an invalid port
    except ValueError:
        return None, INVALID_URL_MESSAGE

    if parts.scheme.lower() != "https" or not hostname:
        return None, INVALID_URL_MESSAGE

    # Reject embedded credentials (https://user:pass@host) as a precaution.
    if parts.username is not None or parts.password is not None:
        return None, NON_WIKIMEDIA_MESSAGE

    if not is_wikimedia_hostname(hostname):
        return None, NON_WIKIMEDIA_MESSAGE

    return value, None
