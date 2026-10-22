"""Manage local Ollama and optional vLLM OCR backends."""
import os
import socket
import subprocess
import sys
import time

import requests
from huggingface_hub import snapshot_download

from ocr_core import validate_port


class BackendManager:
    def __init__(self, model_path="glm-ocr", port=11434, backend_type="ollama"):
        self.model_path = model_path
        self.port = validate_port(port)
        if backend_type not in ("ollama", "vllm"):
            raise ValueError("Backend must be ollama or vllm.")
        self.backend_type = backend_type
        self.process = None

    def is_port_in_use(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            return sock.connect_ex(("127.0.0.1", self.port)) == 0

    def is_backend_ready(self):
        """A listening port is not proof that the expected API is available."""
        endpoint = "/api/tags" if self.backend_type == "ollama" else "/v1/models"
        try:
            response = requests.get("http://127.0.0.1:" + str(self.port) + endpoint, timeout=2)
            if response.status_code != 200:
                return False
            data = response.json()
            key = "models" if self.backend_type == "ollama" else "data"
            return isinstance(data, dict) and isinstance(data.get(key), list)
        except (requests.RequestException, ValueError):
            return False

    def check_model_exists(self):
        if os.path.exists(self.model_path):
            return True
        # Ollama manages model files and names independently of this application.
        return self.backend_type == "ollama"

    def download_model(self):
        if self.backend_type == "ollama":
            return
        local_dir = os.path.abspath(os.path.join(os.getcwd(), "models", self.model_path.replace("/", "_")))
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
            snapshot_download(repo_id=self.model_path, local_dir=local_dir)
        self.model_path = local_dir

    def start_backend(self):
        if self.is_port_in_use():
            if self.is_backend_ready():
                print("Backend already running on port", self.port)
                return True
            print("Port is occupied by an unexpected or unavailable service:", self.port)
            return False

        if self.backend_type == "ollama":
            print("Ollama is not running. Start the Ollama application before processing.")
            return False

        if not self.check_model_exists():
            self.download_model()

        cmd = [
            sys.executable, "-m", "vllm.entrypoints.openai.api_server",
            "--model", self.model_path, "--port", str(self.port),
            "--gpu-memory-utilization", "0.8", "--max-model-len", "2048",
        ]
        # vLLM can execute code from the model repository. Opt in explicitly.
        if os.environ.get("OPENOCR_TRUST_REMOTE_CODE") == "1":
            cmd.append("--trust-remote-code")

        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Inherit logs instead of piping without consuming (which can deadlock).
        self.process = subprocess.Popen(cmd, startupinfo=startupinfo)
        for _ in range(60):
            if self.process.poll() is not None:
                print("vLLM process exited before API readiness.")
                return False
            if self.is_backend_ready():
                return True
            time.sleep(2)
        print("Timed out waiting for vLLM API readiness.")
        self.stop_backend()
        return False

    def stop_backend(self):
        if self.process is None:
            return
        process, self.process = self.process, None
        if process.poll() is not None:
            return
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)],
                               capture_output=True, timeout=15, check=False)
            else:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            print("Unable to stop backend:", exc)
