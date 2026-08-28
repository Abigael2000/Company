import time

MIN_FORM_SECONDS = 2  # a real human can't fill a form faster than this


def is_spam(form) -> bool:
    """Returns True if a form submission looks automated.

    Two checks, both invisible to real visitors:
    1. Honeypot — a field hidden with CSS that only a bot would fill in.
    2. Time-trap — the form records when it loaded; submissions that come
       back too fast to have been typed by a person are rejected.
    """
    if form.get("website"):
        return True

    loaded_at = form.get("form_loaded_at")
    if loaded_at:
        try:
            if time.time() - float(loaded_at) < MIN_FORM_SECONDS:
                return True
        except ValueError:
            pass

    return False
