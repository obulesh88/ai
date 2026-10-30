"""Minimal Ollama HTTP client using only the standard library."""
import json
import socket
import urllib.error
import urllib.request
from typing import Dict, Iterator, List


class OllamaError(Exception):
    """Base error for Ollama problems."""


class OllamaConnectionError(OllamaError):
    """Ollama is not reachable."""


class OllamaTimeoutError(OllamaError):
    """Ollama did not answer in time."""


class ModelNotFoundError(OllamaError):
    """Requested model is not installed."""


class OllamaClient:
    def __init__(self, host: str = "http://127.0.0.1:11434", timeout: float = 120.0):
        self.host = host.rstrip("/")
        self.timeout = timeout

    def _open(self, path: str, payload: dict = None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            self.host + path, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            return urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 404:
                raise ModelNotFoundError(body or "model not found") from e
            raise OllamaError(f"HTTP {e.code}: {body}") from e
        except (socket.timeout, TimeoutError) as e:
            raise OllamaTimeoutError(f"Timed out after {self.timeout}s") from e
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                raise OllamaTimeoutError(f"Timed out after {self.timeout}s") from e
            raise OllamaConnectionError(f"Cannot reach Ollama at {self.host}: {e.reason}") from e

    def is_available(self) -> bool:
        try:
            self.list_models()
            return True
        except OllamaError:
            return False

    def list_models(self) -> List[str]:
        with self._open("/api/tags") as resp:
            try:
                data = json.loads(resp.read().decode("utf-8"))
            except (ValueError, socket.timeout) as e:
                raise OllamaError(f"Invalid response from Ollama: {e}") from e
        return [m["name"] for m in data.get("models", []) if "name" in m]

    def chat_stream(self, model: str, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Yield response text chunks as they stream in."""
        resp = self._open("/api/chat", {"model": model, "messages": messages, "stream": True})
        with resp:
            try:
                for raw in resp:
                    raw = raw.strip()
                    if not raw:
                        continue
                    obj = json.loads(raw.decode("utf-8"))
                    if "error" in obj:
                        err = str(obj["error"])
                        if "not found" in err.lower():
                            raise ModelNotFoundError(err)
                        raise OllamaError(err)
                    chunk = obj.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if obj.get("done"):
                        return
            except (socket.timeout, TimeoutError) as e:
                raise OllamaTimeoutError(f"Timed out after {self.timeout}s") from e
            except ValueError as e:
                raise OllamaError(f"Invalid streamed response: {e}") from e

    def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        return "".join(self.chat_stream(model, messages))
