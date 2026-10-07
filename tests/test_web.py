import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from devrelay.web import Handler, RUNS, LOCK


class WebTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        with LOCK:
            RUNS.clear()

    def post(self, body):
        request = urllib.request.Request(self.base + "/api/runs", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
        return urllib.request.urlopen(request)

    def test_serves_ui_and_rejects_short_idea(self):
        with urllib.request.urlopen(self.base) as response:
            self.assertIn(b"DevRelay Crew", response.read())
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.post({"idea": "short", "api_key": "test-key-value"})
        self.assertEqual(error.exception.code, 400)

    def test_job_result_does_not_return_key(self):
        def fake_run(idea, key, model, emit):
            emit({"type": "task", "message": "Research done"})
            return {"summary": "demo"}

        with patch("devrelay.web.run_crew", side_effect=fake_run):
            with self.post({"idea": "Create a URL-safe slug function", "api_key": "test-secret-key"}) as response:
                run_id = json.load(response)["id"]
            for _ in range(50):
                with urllib.request.urlopen(self.base + "/api/runs/" + run_id) as response:
                    run = json.load(response)
                if run["status"] == "complete":
                    break
                time.sleep(0.01)
        self.assertEqual(run["status"], "complete")
        self.assertEqual(run["result"]["summary"], "demo")
        self.assertNotIn("test-secret-key", json.dumps(run))


if __name__ == "__main__":
    unittest.main()
