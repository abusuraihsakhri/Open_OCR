"""Backend readiness regression tests; no local OCR server required."""
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from backend import BackendManager


class BackendTests(unittest.TestCase):
    def test_detects_expected_ollama_api(self):
        manager = BackendManager()
        response = Mock(status_code=200)
        response.json.return_value = {"models": []}
        with patch("backend.requests.get", return_value=response) as get:
            self.assertTrue(manager.is_backend_ready())
        self.assertIn("/api/tags", get.call_args.args[0])

    def test_other_http_server_does_not_count_as_ollama(self):
        manager = BackendManager()
        with patch.object(manager, "is_port_in_use", return_value=True), \
             patch.object(manager, "is_backend_ready", return_value=False):
            self.assertFalse(manager.start_backend())

    def test_vllm_api_is_checked_for_model_list(self):
        manager = BackendManager(port=8000, backend_type="vllm")
        response = Mock(status_code=200)
        response.json.return_value = {"data": []}
        with patch("backend.requests.get", return_value=response) as get:
            self.assertTrue(manager.is_backend_ready())
        self.assertIn("/v1/models", get.call_args.args[0])

    def test_vllm_does_not_trust_remote_code_by_default(self):
        manager = BackendManager(port=8000, backend_type="vllm")
        process = Mock()
        process.poll.return_value = None
        with patch.object(manager, "is_port_in_use", return_value=False), \
             patch.object(manager, "check_model_exists", return_value=True), \
             patch.object(manager, "is_backend_ready", return_value=True), \
             patch("backend.subprocess.Popen", return_value=process) as launch, \
             patch.dict(os.environ, {"OPENOCR_TRUST_REMOTE_CODE": "0"}):
            self.assertTrue(manager.start_backend())
            self.assertNotIn("--trust-remote-code", launch.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
