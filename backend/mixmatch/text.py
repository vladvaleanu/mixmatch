"""Ajutoare pentru text."""

import unicodedata


def sort_key(text: str) -> str:
    """Cheia de sortare alfabetică fără diacritice și majuscule: „Încălzire” lângă „incalzire”."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))
