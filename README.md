# OpenOCR

### [Open the Live Application →](https://abusuraihsakhri.github.io/Open_OCR/)

OpenOCR extracts text from images and PDF documents. It offers two distinct applications:

- **Desktop:** a Python/CustomTkinter application using a local Ollama or vLLM server with GLM-OCR. It supports multi-file images, multi-page PDFs, Markdown, valid JSON, and in-memory session history.
- **Browser:** a static web application in [docs/](docs/) that uses Tesseract.js (WebAssembly) and PDF.js. It supports images and PDFs, multiple languages, batch processing, and Markdown/JSON downloads. **This is not GLM-OCR running in the browser.**

A GitHub Pages deployment workflow is included. The browser site becomes public once GitHub Pages is enabled for the repository and deployment succeeds.

## Desktop quick start

Prerequisites: Python 3.12 or newer, [Ollama](https://ollama.com/), and an installed GLM-OCR model. For the optional vLLM backend, install vLLM separately in a compatible GPU/Python environment.

1. Start Ollama, then run: **ollama pull glm-ocr**.
2. On Windows, run **run_openocr.bat**. On Linux/macOS with a graphical Tk environment, run **./run_openocr.sh**.
3. Select or drag PNG/JPEG images or PDF documents.
4. Click **Process Document**. Copy the recognized Markdown text or save it to a file. The JSON tab contains a valid array of page records.

Manual installation from the repository directory:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python src/main.py

The default Ollama port is 11434. The Settings tab allows changing the model, port, backend and appearance. The optional vLLM workflow no longer enables arbitrary model repository code by default. Only after reviewing and trusting a repository that requires it, set **OPENOCR_TRUST_REMOTE_CODE=1**.

## Browser quick start

The standalone web application is located at [docs/index.html](docs/index.html). For local development:

    python3 -m http.server 8000 --directory docs

Then visit http://127.0.0.1:8000/ and select or drop files, choose a recognition language, and click **Recognize text**. Export the result as Markdown or JSON. The browser version supports English, German, French, Spanish and English/German OCR. Limits: 20 files per batch, 25 MiB per file and 50 pages per PDF.

## Privacy and dependencies

- Desktop requests go to the configured local Ollama/vLLM service. Documents are not intentionally sent to a hosted application API. Installing packages and models may require internet access.
- Browser recognition and PDF rendering operate on-device, with no application backend or account. The browser downloads third-party Tesseract.js and PDF.js scripts, WebAssembly resources, and language data; these scripts run within the browser and should be treated as external dependencies. Outputs are held in memory, not stored in a cloud history.
- No external API key is required. For confidential documents, use a trusted device and network.

## Development, tests and compatibility

- Desktop stack: Python, CustomTkinter, Pillow, PyMuPDF, Requests, tkinterdnd2, Ollama or optional vLLM.
- Web stack: HTML, CSS, JavaScript, Tesseract.js 5.1.1, PDF.js 3.11.174. No server-side Python runs on GitHub Pages.
- Python regression tests: **python -m unittest discover -s tests -p 'test_*.py' -v**
- JavaScript unit tests: **node --test tests/*.test.mjs**
- CI also runs compilation checks and a Playwright Chromium UI smoke test.
- The web version targets browsers supporting WebAssembly, Web Workers, and local file input. Chromium is the automated browser test target; full cross-browser testing has not been performed.

## License

No repository license file has been published. The GLM-OCR model and external libraries are subject to their own licenses.

Developed by Dr. Abu Suraih Sakhri.
