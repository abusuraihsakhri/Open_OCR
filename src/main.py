import sys
import os
import threading

# Ensure imports work whether run via `python src/main.py` or otherwise
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import BackendManager
from gui import OpenOCRApp

manager = None

def restart_backend(model_path, port, backend_type):
    global manager
    if manager:
        manager.stop_backend()
    
    manager = BackendManager(model_path=model_path, port=port, backend_type=backend_type)
    return manager.start_backend()

def main():
    global manager
    
    # Initialize UI
    app = OpenOCRApp(start_backend_callback=restart_backend)
    
    # Check what the user has in settings
    model = app.model_path_var.get()
    try:
        port = int(app.api_port_var.get())
    except ValueError:
        port = 11434
    btype = app.backend_type_var.get()
    
    manager = BackendManager(model_path=model, port=port, backend_type=btype)
    
    # Tkinter widget access must remain on the main thread.
    app.set_status("Checking local OCR backend...", "yellow")
    app.progress_bar.start()
    app.btn_process.configure(state="disabled")

    def init_backend():
        try:
            success = manager.start_backend()
            error = None
        except Exception as exc:
            success = False
            error = str(exc)

        def finalize():
            app.progress_bar.stop()
            if success:
                app.set_status("Ready. Backend running.", "green")
                app.btn_process.configure(state="normal")
            else:
                detail = error or "Start Ollama (and pull the model) or check your vLLM settings."
                app.set_status("Backend unavailable. " + detail, "red")

        app.after(0, finalize)

    threading.Thread(target=init_backend, daemon=True).start()

    # App main loop
    app.mainloop()

    # Clean up when closed
    if manager:
        print("Shutting down backend...")
        manager.stop_backend()
        print("Backend shut down.")
        
    sys.exit(0)

if __name__ == "__main__":
    main()
