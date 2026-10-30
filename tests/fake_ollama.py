"""A tiny fake Ollama server for tests."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


def start_server(models=("llama:latest",), delay=0.0):
    state = {"requests": []}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path == "/api/tags":
                body = json.dumps({"models": [{"name": m} for m in models]}).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/version":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"version": "0.0.0-fake"}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n))
            state["requests"].append(req)
            time.sleep(delay)
            if req["model"] not in models:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "model not found"}).encode())
                return
            self.send_response(200)
            self.end_headers()
            n_user = len([m for m in req["messages"] if m["role"] == "user"])
            for word in ("reply", str(n_user)):
                line = {"message": {"role": "assistant", "content": word}, "done": False}
                self.wfile.write((json.dumps(line) + "\n").encode())
            self.wfile.write((json.dumps({"done": True}) + "\n").encode())

    server = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}", state
