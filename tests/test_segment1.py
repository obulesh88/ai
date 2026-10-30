import unittest

from ai.model_manager import ModelManager
from ai.ollama_client import (
    ModelNotFoundError,
    OllamaClient,
    OllamaConnectionError,
    OllamaTimeoutError,
)
from config import Config
from core.assistant import Assistant
from core.conversation import Conversation
from tests.fake_ollama import start_server


def make_config(host, model="llama:latest"):
    return Config(host, model, 5.0, 20, "sys")


class ClientTests(unittest.TestCase):
    def test_list_models_and_stream(self):
        server, url, _ = start_server(("a:latest", "b:1"))
        self.addCleanup(server.shutdown)
        c = OllamaClient(url, 5)
        self.assertEqual(c.list_models(), ["a:latest", "b:1"])
        self.assertEqual(list(c.chat_stream("a:latest", [])), ["reply", "0"])
        self.assertTrue(c.is_available())

    def test_unknown_model(self):
        server, url, _ = start_server()
        self.addCleanup(server.shutdown)
        with self.assertRaises(ModelNotFoundError):
            OllamaClient(url, 5).chat("nope", [])

    def test_connection_error(self):
        c = OllamaClient("http://127.0.0.1:1", 2)
        with self.assertRaises(OllamaConnectionError):
            c.list_models()
        self.assertFalse(c.is_available())

    def test_timeout(self):
        server, url, _ = start_server(delay=1.5)
        self.addCleanup(server.shutdown)
        with self.assertRaises(OllamaTimeoutError):
            OllamaClient(url, 0.3).chat("llama:latest", [])


class ModelManagerTests(unittest.TestCase):
    def setUp(self):
        self.server, self.url, _ = start_server(("x:latest", "y:2"))
        self.addCleanup(self.server.shutdown)
        self.client = OllamaClient(self.url, 5)

    def test_select_and_latest_alias(self):
        m = ModelManager(self.client, "zzz")
        self.assertEqual(m.select("x"), "x:latest")
        with self.assertRaises(ModelNotFoundError):
            m.select("missing")

    def test_auto_select_fallback(self):
        self.assertEqual(ModelManager(self.client, "y:2").auto_select(), "y:2")
        self.assertEqual(ModelManager(self.client, "zzz").auto_select(), "x:latest")

    def test_no_models(self):
        server, url, _ = start_server(())
        self.addCleanup(server.shutdown)
        with self.assertRaises(ModelNotFoundError):
            ModelManager(OllamaClient(url, 5), "q").auto_select()


class AssistantTests(unittest.TestCase):
    def test_context_is_kept(self):
        server, url, state = start_server()
        self.addCleanup(server.shutdown)
        a = Assistant(make_config(url))
        self.assertEqual("".join(a.ask("hi")), "reply1")
        self.assertEqual("".join(a.ask("again")), "reply2")
        sent = state["requests"][-1]["messages"]
        self.assertEqual([m["role"] for m in sent], ["system", "user", "assistant", "user"])

    def test_failed_ask_does_not_pollute_history(self):
        a = Assistant(make_config("http://127.0.0.1:1"))
        a.models.current = "llama:latest"
        with self.assertRaises(OllamaConnectionError):
            list(a.ask("hi"))
        self.assertEqual(a.conversation.messages, [])

    def test_conversation_limit(self):
        c = Conversation(4)
        for i in range(10):
            c.add("user", str(i))
        self.assertEqual(len(c.messages), 4)
        self.assertEqual(c.messages[-1]["content"], "9")


if __name__ == "__main__":
    unittest.main()
