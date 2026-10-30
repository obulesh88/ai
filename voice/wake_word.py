"""Wake-word detection for 'Hey Hema'."""
import re

WAKE_PHRASES = ("hey hema", "hey, hema", "ok hema", "hi hema")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


def has_wake_word(text: str) -> bool:
    flat = " " + normalize(text) + " "
    return any(" " + normalize(p) + " " in flat for p in WAKE_PHRASES)


def extract_command(text: str) -> str:
    """Return the text after the wake phrase, or '' if there is no wake phrase."""
    flat = " " + normalize(text) + " "
    for phrase in WAKE_PHRASES:
        marker = " " + normalize(phrase) + " "
        idx = flat.find(marker)
        if idx >= 0:
            return flat[idx + len(marker):].strip()
    return ""
