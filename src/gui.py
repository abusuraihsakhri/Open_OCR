import os
import json
import threading
import requests
import base64
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pyperclip
import re
import io
from PIL import Image
from ocr_core import image_as_png, response_text, validate_port, valid_json_output

# For PDF conversion
try:
    import fitz # PyMuPDF
except ImportError:
    fitz = None

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    TkinterDnD = None
    DND_FILES = None

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

if TkinterDnD is not None:
    class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class Tk(ctk.CTk):
        pass

class OpenOCRApp(Tk):
    def __init__(self, start_backend_callback=None):
        super().__init__()
        
        self.title("OpenOCR")
        self.geometry("900x700")
        
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.history = []
        self.json_results = []
        self._processing_failed = False
        self._error_message = None
        self.processing = False
        self.start_backend_callback = start_backend_callback
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header Container
        self.header_container = ctk.CTkFrame(self, fg_color="transparent")
        self.header_container.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="ew")
        
        # Main Title
        self.header = ctk.CTkLabel(
            self.header_container, text="OpenOCR - Local & Private", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.header.pack()

        # Developer Attribution
        self.dev_label = ctk.CTkLabel(
            self.header_container, text="Developed by Dr. Abu Suraih Sakhri ", 
            font=ctk.CTkFont(size=14, weight="bold", slant="italic"),
            text_color="#1f538d"
        )
        self.dev_label.pack(pady=(2, 5))

        # Short Description
        self.desc_label = ctk.CTkLabel(
            self.header_container, 
            text="High-performance, local OCR for images and PDFs. Your data never leaves your machine.",
            font=ctk.CTkFont(size=18, weight="normal"),
            text_color="#444444"
        )
        self.desc_label.pack(pady=(5, 15))
        
        # Main Tabview with larger headings and icons
        self.tabview = ctk.CTkTabview(self)
        self.tabview.configure(segmented_button_selected_color="#1f538d")
        self.tabview.grid(row=1, column=0, padx=25, pady=15, sticky="nsew")
        
        # Increase the size of the segmented button font
        self.tabview._segmented_button.configure(font=ctk.CTkFont(size=18, weight="bold"))
        
        self.tab_main = self.tabview.add("📁 Main Process")
        self.tab_settings = self.tabview.add("⚙️ Settings")
        self.tab_history = self.tabview.add("📜 History")
        
        self.setup_main_tab()
        self.setup_settings_tab()
        self.setup_history_tab()

    def setup_main_tab(self):
        self.tab_main.grid_rowconfigure(2, weight=1)
        self.tab_main.grid_columnconfigure(0, weight=1)
        
        # Drop / Select Area - Modernized
        self.drop_frame = ctk.CTkFrame(
            self.tab_main, 
            fg_color="#f5f5f5", 
            border_width=3, 
            border_color="#1f538d",
            corner_radius=15
        )
        self.drop_frame.grid(row=0, column=0, padx=25, pady=20, sticky="ew")
        
        self.lbl_drop = ctk.CTkLabel(
            self.drop_frame, text="📄 Drag & Drop Image/PDF here\nor click to browse", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1f538d"
        )
        self.lbl_drop.pack(pady=45, padx=30)
        self.drop_frame.bind("<Button-1>", self.browse_file)
        self.lbl_drop.bind("<Button-1>", self.browse_file)
        
        if TkinterDnD is not None:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)
            self.lbl_drop.drop_target_register(DND_FILES)
            self.lbl_drop.dnd_bind('<<Drop>>', self.handle_drop)
        
        self.current_files = []
        
        # Progress Bar and Status
        self.progress_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # Status Indicator (Green/Yellow/Red dot)
        self.status_indicator = ctk.CTkLabel(
            self.progress_frame, text="●", 
            text_color="#faae42", # Default yellow
            font=ctk.CTkFont(size=24)
        )
        self.status_indicator.pack(side="left", padx=(0, 5))

        self.status_label = ctk.CTkLabel(self.progress_frame, text="Initializing...", font=ctk.CTkFont(size=16, weight="bold"))
        self.status_label.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, 
            mode="indeterminate",
            height=15,
            progress_color="#2fa572",
            fg_color="#dbdbdb",
            corner_radius=10
        )
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(25, 0))
        self.progress_bar.set(0)
        
        # Output Tabs
        self.output_tabs = ctk.CTkTabview(self.tab_main)
        self.output_tabs.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        self.tab_md = self.output_tabs.add("Markdown Output")
        self.tab_json = self.output_tabs.add("JSON Output")
        
        # Larger fonts for output
        text_font = ctk.CTkFont(family="Consolas", size=15)
        self.text_md = ctk.CTkTextbox(self.tab_md, wrap="word", font=text_font)
        self.text_md.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.text_json = ctk.CTkTextbox(self.tab_json, wrap="word", font=text_font)
        self.text_json.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Action Buttons
        self.actions_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        self.actions_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        button_font = ctk.CTkFont(size=14, weight="bold")
        
        self.btn_process = ctk.CTkButton(
            self.actions_frame, text="Process Document", 
            command=self.process_document,
            font=button_font,
            height=45,
            fg_color="#1f538d",
            hover_color="#163e6a"
        )
        self.btn_process.pack(side="left", padx=5)
        
        self.btn_copy = ctk.CTkButton(
            self.actions_frame, text="Copy to Clipboard", 
            command=self.copy_clipboard,
            font=button_font,
            height=45
        )
        self.btn_copy.pack(side="left", padx=5)
        
        self.btn_save = ctk.CTkButton(
            self.actions_frame, text="Save as .md", 
            command=self.save_md,
            font=button_font,
            height=45
        )
        self.btn_save.pack(side="left", padx=5)
        
        self.btn_clear = ctk.CTkButton(
            self.actions_frame, text="Clear All", 
            fg_color="transparent", 
            border_width=2, 
            command=self.clear_main,
            font=button_font,
            height=45,
            text_color="#1f538d"
        )
        self.btn_clear.pack(side="right", padx=5)

    def setup_settings_tab(self):
        # We will hold settings in variables
        self.model_path_var = ctk.StringVar(value="glm-ocr")
        self.api_port_var = ctk.StringVar(value="11434")
        self.backend_type_var = ctk.StringVar(value="ollama")
        
        ctk.CTkLabel(self.tab_settings, text="Backend Type:").grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.opt_backend = ctk.CTkOptionMenu(
            self.tab_settings, values=["vllm", "ollama"], 
            variable=self.backend_type_var
        )
        self.opt_backend.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.tab_settings, text="Model Path/Repo:").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.ent_model = ctk.CTkEntry(self.tab_settings, textvariable=self.model_path_var, width=300)
        self.ent_model.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.tab_settings, text="API Port:").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.ent_port = ctk.CTkEntry(self.tab_settings, textvariable=self.api_port_var, width=100)
        self.ent_port.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        
        self.btn_restart_backend = ctk.CTkButton(
            self.tab_settings, text="Apply & Restart Backend", 
            command=self.restart_backend,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            fg_color="#1f538d"
        )
        self.btn_restart_backend.grid(row=3, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        # Appearance Mode Switch
        ctk.CTkLabel(self.tab_settings, text="Appearance Mode:").grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.appearance_switch = ctk.CTkOptionMenu(
            self.tab_settings, values=["Light", "Dark", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_switch.set("Light")
        self.appearance_switch.grid(row=4, column=1, padx=20, pady=10, sticky="ew")

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)

        
    def setup_history_tab(self):
        self.tab_history.grid_rowconfigure(0, weight=1)
        self.tab_history.grid_columnconfigure(0, weight=1)
        
        self.history_scroll = ctk.CTkScrollableFrame(self.tab_history)
        self.history_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.history_labels = []

    def handle_drop(self, event):
        if event.data and not self.processing:
            # Tcl's parser handles both paths with spaces and brace-quoted paths.
            paths = self.tk.splitlist(event.data)
            extensions = {'.png', '.jpg', '.jpeg', '.pdf'}
            valid_paths = [p for p in paths if os.path.isfile(p) and os.path.splitext(p)[1].lower() in extensions]
            if valid_paths:
                self.current_files = valid_paths
                if len(valid_paths) == 1:
                    self.lbl_drop.configure(text=os.path.basename(valid_paths[0]))
                else:
                    self.lbl_drop.configure(text=f"{len(valid_paths)} files selected")

    def browse_file(self, event=None):
        if self.processing:
            return
        filenames = filedialog.askopenfilenames(
            title="Select Image or PDF",
            filetypes=(("Images & PDFs", "*.png *.jpg *.jpeg *.pdf"), ("All Files", "*.*"))
        )
        if filenames:
            self.current_files = list(filenames)
            if len(self.current_files) == 1:
                self.lbl_drop.configure(text=os.path.basename(self.current_files[0]))
            else:
                self.lbl_drop.configure(text=f"{len(self.current_files)} files selected")

    def process_document(self):
        if self.processing:
            return
        if not self.current_files:
            messagebox.showerror("Error", "Please select valid files first.")
            return
        try:
            port = validate_port(self.api_port_var.get())
            model = self.model_path_var.get().strip()
            backend = self.backend_type_var.get()
            if not model:
                raise ValueError("Model name or path cannot be empty.")
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        selected_files = list(self.current_files)
        self.text_md.delete("1.0", "end")
        self.text_json.delete("1.0", "end")
        self.json_results = []
        self._processing_failed = False
        self._error_message = None
        self.processing = True
        self.set_status("Processing...", "yellow")
        self.progress_bar.start()
        self.btn_process.configure(state="disabled")
        self.btn_clear.configure(state="disabled")

        threading.Thread(
            target=self._process_thread,
            args=(selected_files, port, model, backend),
            daemon=True,
        ).start()

    def _process_thread(self, selected_files, port, model, backend):
        full_md = ""
        try:
            total_files = len(selected_files)
            for file_idx, file_path in enumerate(selected_files):
                filename = os.path.basename(file_path)
                ext = os.path.splitext(file_path)[1].lower()
                
                self.after(0, lambda f=filename, i=file_idx+1: self.set_status(f"Reading {i}/{total_files}: {f}", "yellow"))
                
                pages_data = [] # (label, img_bytes)
                
                if ext == ".pdf":
                    if fitz:
                        doc = fitz.open(file_path)
                        for page_num in range(len(doc)):
                            self.after(0, lambda f=filename, p=page_num+1, t=len(doc): 
                                       self.set_status(f"Processing {f} - Page {p}/{t}", "yellow"))
                            page = doc.load_page(page_num)
                            pix = page.get_pixmap()
                            img_data = pix.tobytes("png")
                            pages_data.append((f"Page {page_num + 1}", img_data))
                        doc.close()
                    else:
                        self.after(0, lambda: messagebox.showerror("Error", "PyMuPDF not installed for PDF support."))
                        break
                else:
                    with Image.open(file_path) as img:
                        pages_data.append((filename, image_as_png(img)))

                for label, img_data in pages_data:
                    b64_img = base64.b64encode(img_data).decode('utf-8')
                    
                    if backend == "ollama":
                        url = f"http://127.0.0.1:{port}/api/generate"
                        payload = {
                            "model": model,
                            "prompt": "Extract text and structured data from this document accurately.",
                            "images": [b64_img],
                            "stream": False
                        }
                    else:
                        url = f"http://127.0.0.1:{port}/v1/chat/completions"
                        payload = {
                            "model": model,
                            "messages": [{"role": "user", "content": [
                                {"type": "text", "text": "Extract text and structured data from this document."},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                            ]}],
                            "max_tokens": 4096
                        }
                    
                    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=120)
                    
                    if response.status_code == 200:
                        data = response.json()
                        result_text = response_text(data, backend)
                        
                        # Format output
                        page_header = f"\n## {label}\n\n"
                        full_md += page_header + result_text + "\n\n---\n"
                        # Use a real JSON array for multi-file / multi-page output.
                        self.after(0, self.append_to_output, page_header + result_text + "\n\n---\n",
                                   {"source": filename, "page": label, "content": data})
                    else:
                        error_msg = f"\n## Error processing {label}\nStatus: {response.status_code}\n"
                        full_md += error_msg
                        self._processing_failed = True
                        self.after(0, self.append_to_output, error_msg,
                                   {"source": filename, "page": label, "error": response.status_code})

            # Add to history at the end
            if full_md:
                final_filename = os.path.basename(selected_files[0]) + (f" (+{len(selected_files)-1} more)" if len(selected_files)>1 else "")
                self.history.append({"file": final_filename, "result": full_md[:100] + "..."})
                self.after(0, self.refresh_history)

        except Exception as e:
            self._processing_failed = True
            self._error_message = str(e)
            self.after(0, lambda message=str(e): self.set_status("Error: " + message, "red"))
            self.after(0, lambda message=str(e): messagebox.showerror("Process Error", message))
            
        finally:
            self.after(0, self.finish_processing)

    def append_to_output(self, md_chunk, json_chunk):
        self.text_md.insert("end", md_chunk)
        if json_chunk is not None:
            self.json_results.append(json_chunk)
        self.text_json.delete("1.0", "end")
        self.text_json.insert("1.0", valid_json_output(self.json_results))
        self.text_md.see("end")
        self.text_json.see("end")

    def update_output(self, md_text, json_text):
        # Fallback for simple status updates if needed
        self.text_md.delete("1.0", "end")
        self.text_md.insert("1.0", md_text)
        self.text_json.delete("1.0", "end")
        self.text_json.insert("1.0", json_text)

    def finish_processing(self):
        self.processing = False
        self.progress_bar.stop()
        self.btn_process.configure(state="normal")
        self.btn_clear.configure(state="normal")
        if self._processing_failed:
            self.set_status("Error: " + self._error_message if self._error_message
                            else "Completed with errors; see output.", "red")
        else:
            self.set_status("Ready. Document processed.", "green")

    def copy_clipboard(self):
        content = self.text_md.get("1.0", "end-1c")
        if content.strip():
            try:
                pyperclip.copy(content)
            except pyperclip.PyperclipException as exc:
                messagebox.showerror("Clipboard unavailable", str(exc))
                return
            self.set_status("Copied to clipboard!", "green")
            self.after(2000, lambda: self.set_status("Ready.", "green"))

    def save_md(self):
        content = self.text_md.get("1.0", "end-1c")
        if content.strip():
            filepath = filedialog.asksaveasfilename(
                title="Save Markdown",
                defaultextension=".md",
                filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")]
            )
            if filepath:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.set_status("File saved!", "green")
                self.after(2000, lambda: self.set_status("Ready.", "green"))

    def set_status(self, text, indicator_color="gray"):
        color_map = {
            "green": "#2fa572",
            "yellow": "#faae42",
            "red": "#ea4335",
            "gray": "gray"
        }
        self.status_label.configure(text=text)
        self.status_indicator.configure(text_color=color_map.get(indicator_color, "gray"))

    def clear_main(self):
        if self.processing:
            return
        self.json_results = []
        self.current_files = []
        self.lbl_drop.configure(text="📄 Drag & Drop Image/PDF here\nor click to browse")
        self.text_md.delete("1.0", "end")
        self.text_json.delete("1.0", "end")
        self.set_status("Ready.", "green")

    def refresh_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
            
        for idx, item in enumerate(reversed(self.history)):
            frame = ctk.CTkFrame(self.history_scroll)
            frame.pack(fill="x", pady=5)
            lbl = ctk.CTkLabel(frame, text=f"File: {item['file']}\n{item['result']}", justify="left", anchor="w")
            lbl.pack(fill="x", padx=10, pady=5)

    def restart_backend(self):
        if self.start_backend_callback:
            # We pass the settings to the callback
            try:
                port = validate_port(self.api_port_var.get())
            except ValueError as exc:
                messagebox.showerror("Invalid port", str(exc))
                return
            model = self.model_path_var.get()
            btype = self.backend_type_var.get()
            
            self.status_label.configure(text="Restarting backend...")
            threading.Thread(target=self._restart_thread, args=(model, port, btype), daemon=True).start()

    def _restart_thread(self, model, port, btype):
        try:
            success = self.start_backend_callback(model, port, btype)
        except Exception as exc:
            self.after(0, lambda message=str(exc): messagebox.showerror("Backend error", message))
            success = False
        if success:
            self.after(0, lambda: self.status_label.configure(text="Backend running."))
            self.after(0, lambda: messagebox.showinfo("Success", "Backend restarted successfully."))
        else:
            self.after(0, lambda: self.status_label.configure(text="Error starting backend."))
            self.after(0, lambda: messagebox.showerror("Error", "Failed to clear or start the backend."))

if __name__ == "__main__":
    app = OpenOCRApp()
    app.mainloop()
