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
    
    # We can start the backend in a thread so GUI shows up immediately with a "Loading" status
    def init_backend():
        app.set_status("Checking local model / Starting backend...", "yellow")
        app.progress_bar.start()
        app.btn_process.configure(state="disabled")
        
        # Check if the model is downloaded
        if not manager.check_model_exists():
            app.set_status("Downloading GLM-OCR weights... this will take a while.", "yellow")
        
        # This will block until started or timed out
        success = manager.start_backend()
        
        app.progress_bar.stop()
        if success:
            app.set_status("Ready. Backend running.", "green")
            app.btn_process.configure(state="normal")
        else:
            app.set_status("Error starting backend. Check console logs.", "red")

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
