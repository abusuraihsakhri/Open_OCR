# OpenOCR 🚀

**OpenOCR** is a state-of-the-art, single-click desktop application designed for high-performance, local, and private Optical Character Recognition (OCR). This tool bundles the powerful **GLM-OCR** model within a modern, user-friendly interface, ensuring your documents are processed entirely on your local hardware.

---

### Developed by: **Dr. Abu Suraih Sakhri**

---

## ✨ Features

- 🔒 **Privacy-First**: No external API calls. All document processing happens locally on your machine.
- 📁 **Universal Drag & Drop**: Seamlessly process images (PNG, JPG) and PDFs by dragging them directly into the app.
- 🤖 **Local AI Engine**: Built-in process management for **Ollama** and **vLLM**, optimized for NVIDIA GPUs (6GB+ VRAM).
- 🎨 **Modern UI**: A sleek, premium interface built with **CustomTkinter**, featuring real-time Light/Dark mode toggling.
- 📝 **Markdown & JSON Output**: View extracted text in structured Markdown or raw JSON formats.
- 📋 **Integrated History**: Keep track of your previous OCR results in the session history tab.
- ⚡ **One-Click Execution**: Automated environment setup and dependency installation via the unified launcher.

---

## 🛠️ Technology Stack

- **Frontend**: CustomTkinter (Python Desktop GUI)
- **OCR Model**: zai-org/GLM-OCR (0.9B VLM)
- **Inference Engines**: Ollama (Primary) / vLLM (Secondary)
- **Local Database**: Session History Management
- **Packaging**: PyInstaller compatible

---

## 🚀 Getting Started

### Prerequisites

1. **Python**: Ensure you have [Python 3.12+](https://www.python.org/downloads/) installed.
2. **Ollama**: Download and install [Ollama](https://ollama.com/) (Recommended for Windows).
3. **Hardware**: An NVIDIA GPU with at least **6GB VRAM** is recommended for smooth performance.

### Quick Launch (Windows)

1. **Pull the Model**: Open your terminal and run:
   ```bash
   ollama pull glm-ocr
   ```
2. **Run the App**: Double-click **`run_openocr.bat`**.
   - *On the first run, the launcher will automatically create a virtual environment and install all necessary Python dependencies (CustomTkinter, Pillow, etc.).*

---

## ⚙️ Configuration

OpenOCR adaptive backend logic allows you to customize the performance:
- **Appearance**: Toggle between Light, Dark, or System themes in the **Settings** tab.
- **Port Management**: Defaulted to `11434` for Ollama. If you use a custom port, you can update it in Settings.
- **GPU Optimization**: The app automatically caps VRAM utilization at 80% to ensure system stability.

---

## 📦 Distribution & Packaging

To bundle OpenOCR into a standalone executable (`.exe`):

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "OpenOCR" --add-data "src;src" "src/main.py"
```

*Note: Ensure `tkinterdnd2` and `customtkinter` libraries are correctly referenced in your build configuration.*

---

## 📜 License

This project is developed for private and professional use. The underlying GLM-OCR model is subject to its original repository's licensing terms.

---
*Developed with ❤️ by Dr. Abu Suraih Sakhri*
