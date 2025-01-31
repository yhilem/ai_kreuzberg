# Kreuzberg

Kreuzberg is a library for simplified text extraction from PDF files. It's meant to offer simple, hassle free text extraction.

Why?

I am building, like many do now, a RAG focused service. I have text extraction needs.

There are quite a lot of commercial options out there, and several open-source + paid options.

I wanted something that I can control, easily run locally and cheaply use. Hence, this library.

## Installation

1. Begin by installing the python package:

   ```shell

   pip install kreuzberg

   ```

2. Install the system dependencies:

- [pandoc](https://pandoc.org/installing.html) (non-pdf text extraction, GPL v2.0 licensed but used as CLI only)
- [tesseract-ocr](https://tesseract-ocr.github.io/) (for image/PDF OCR, Apache License)

## License

This library uses the MIT license.
