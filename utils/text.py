def clean(value):
    """A request field as stripped text. Anything that is not text (a number, a list, null) counts as empty."""
    return value.strip() if isinstance(value, str) else ''
