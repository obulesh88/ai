"""Text-to-speech and speech-to-text with optional free/offline engines.

No audio is ever recorded or sent anywhere unless you explicitly start listening.
"""
from typing import Callable, Optional


class SpeechError(Exception):
    pass


class Pyttsx3Speaker:
    """Offline TTS using pyttsx3 (Windows SAPI5). Install: pip install pyttsx3"""

    def __init__(self, rate: int = 175):
        try:
            import pyttsx3
        except ImportError as e:
            raise SpeechError("pyttsx3 is not installed; run: pip install pyttsx3") from e
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)

    def speak(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()


class PrintSpeaker:
    """Text-only fallback when no TTS engine is available."""

    def speak(self, text: str) -> None:
        print(f"[voice] {text}")


def make_speaker(allow_audio: bool = True):
    if not allow_audio:
        return PrintSpeaker()
    try:
        return Pyttsx3Speaker()
    except SpeechError:
        return PrintSpeaker()


class Recognizer:
    """Microphone STT. Prefers free offline engines (Vosk, PocketSphinx)."""

    def __init__(self, offline_only: bool = True, language: str = "en-US"):
        try:
            import speech_recognition as sr
        except ImportError as e:
            raise SpeechError("speech_recognition is not installed; run: pip install SpeechRecognition") from e
        self._sr = sr
        self.offline_only = offline_only
        self.language = language
        self._mic = sr.Microphone()

    def listen_once(self, timeout: float = 5.0, phrase_limit: float = 8.0) -> str:
        rec = self._sr.Recognizer()
        with self._mic as source:
            rec.adjust_for_ambient_noise(source, duration=0.4)
            audio = rec.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        return self.transcribe(audio, rec)

    def transcribe(self, audio, rec=None) -> str:
        rec = rec or self._sr.Recognizer()
        errors = []
        engines = [("sphinx", lambda: rec.recognize_sphinx(audio, language=self.language))]
        try:
            import vosk  # noqa: F401  (presence check only)
            engines.append(("vosk", lambda: rec.recognize_vosk(audio)))
        except ImportError:
            pass
        if not self.offline_only:
            engines.append(("google", lambda: rec.recognize_google(audio, language=self.language)))
        for name, fn in engines:
            try:
                text = fn()
                return text.strip() if isinstance(text, str) else ""
            except Exception as e:
                errors.append(f"{name}: {e}")
        raise SpeechError("Could not transcribe audio. " + " | ".join(errors))
