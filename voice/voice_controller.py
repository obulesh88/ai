"""Ties microphone, wake word, STT and TTS together with explicit permission."""
import threading
from typing import Callable, Optional

from security.permissions import PermissionDenied
from voice.wake_word import extract_command


class VoiceController:
    def __init__(self, recognizer_factory: Callable, speaker, approvals,
                 require_wake_word: bool = True):
        self.recognizer_factory = recognizer_factory
        self.speaker = speaker
        self.approvals = approvals
        self.require_wake_word = require_wake_word
        self.listening = False
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.on_command: Optional[Callable[[str], None]] = None
        self.last_error: Optional[str] = None

    def handle_transcript(self, text: str) -> Optional[str]:
        """Returns the command to run, or None if there is no usable command."""
        if not self.require_wake_word:
            return text.strip() or None
        command = extract_command(text)
        return command or None

    def start(self) -> bool:
        """Requests microphone permission, then listens in a background thread."""
        if self.listening:
            return True
        self.approvals.require("microphone", "Listen to the microphone for voice commands")
        self.listening = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self.listening = False
        self._stop.set()

    def _loop(self) -> None:
        try:
            recognizer = self.recognizer_factory()
        except Exception as e:
            self.last_error = str(e)
            self.listening = False
            return
        while not self._stop.is_set() and self.listening:
            try:
                text = recognizer.listen_once()
            except Exception as e:
                self.last_error = str(e)
                continue
            command = self.handle_transcript(text or "")
            if command and self.on_command:
                self.on_command(command)

    def speak(self, text: str) -> None:
        self.speaker.speak(text)
