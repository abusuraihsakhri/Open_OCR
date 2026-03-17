import os
import subprocess
import socket
import time
from huggingface_hub import snapshot_download

class BackendManager:
    def __init__(self, model_path="glm-ocr", port=11434, backend_type="ollama"):
        self.model_path = model_path
        self.port = port
        self.backend_type = backend_type
        self.process = None

    def is_port_in_use(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', self.port)) == 0

    def check_model_exists(self):
        # If it's a local path and exists
        if os.path.exists(self.model_path):
            return True
        # If using Ollama, checking is different, assume true or handle elsewhere
        if self.backend_type == "ollama":
            return True
        return False

    def download_model(self):
        if self.backend_type == "ollama":
            return

        # If it's a HuggingFace repo ID
        local_dir = os.path.abspath(os.path.join(os.getcwd(), "models", self.model_path.replace("/", "_")))
        if not os.path.exists(local_dir):
            print(f"Downloading model {self.model_path} to {local_dir}...")
            os.makedirs(local_dir, exist_ok=True)
            snapshot_download(repo_id=self.model_path, local_dir=local_dir)
        
        self.model_path = local_dir

    def start_backend(self):
        if self.is_port_in_use():
            print(f"Backend already running on port {self.port}.")
            return True

        if not self.check_model_exists():
            self.download_model()

        print("Starting backend subprocess...")
        
        if self.backend_type == "ollama":
            # For Ollama, we expect the user to have the Ollama app running.
            # We don't try to start 'ollama serve' as a subprocess because it's usually
            # managed as a tray app or system service on Windows.
            # However, we can check if it's running via port.
            if self.is_port_in_use():
                print("Ollama is already running.")
                return True
            else:
                print("Ollama is NOT running. Please open the Ollama application.")
                # We won't start it ourselves to avoid permission/path issues
                return False
        else:
            # vLLM launch optimized for 6GB GPU
            cmd = [
                "python", "-m", "vllm.entrypoints.openai.api_server", 
                "--model", self.model_path, 
                "--port", str(self.port),
                "--gpu-memory-utilization", "0.8",  # Leave space for Windows/GUI
                "--max-model-len", "2048",         # Cap context to save VRAM
                "--trust-remote-code"               # Necessary for GLM architectures
            ]
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo
            )

        # Wait a bit for the server to spin up
        for _ in range(60): # Wait up to 60 seconds
            if self.is_port_in_use():
                return True
            time.sleep(2)
            
        print("Timeout waiting for backend to start.")
        return False

    def stop_backend(self):
        if self.process:
            print("Stopping backend subprocess...")
            try:
                if os.name == 'nt':
                    # On Windows, taskkill is more reliable for children
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True)
                else:
                    self.process.terminate()
            except Exception as e:
                print(f"Error stopping process: {e}")
            self.process.wait()
            self.process = None
