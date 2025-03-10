# Kreuzberg

Kreuzberg is a Python library for text extraction from documents. It provides a unified async interface for extracting text from PDFs, images, office documents, and more.

## Why Kreuzberg?

- **Simple and Hassle-Free**: Clean API that just works, without complex configuration
- **Local Processing**: No external API calls or cloud dependencies required
- **Resource Efficient**: Lightweight processing without GPU requirements
- **Small Package Size**: Has few curated dependencies and a minimal footprint
- **Format Support**: Comprehensive support for documents, images, and text formats
- **Modern Python**: Built with async/await, type hints, and functional first approach
- **Permissive OSS**: Kreuzberg and its dependencies have a permissive OSS license

Kreuzberg was built for RAG (Retrieval Augmented Generation) applications, focusing on local processing with minimal dependencies. Its designed for modern async applications, serverless functions, and dockerized applications.

## Installation

### 1. Install the Python Package

```shell
pip install kreuzberg
```

### 2. Install System Dependencies

Kreuzberg requires two system level dependencies:

- [Pandoc](https://pandoc.org/installing.html) - For document format conversion. Minimum required version is Pandoc 2.
- [Tesseract OCR](https://tesseract-ocr.github.io/) - For image and PDF OCR. Minimum required version is Tesseract 5.

You can install these with:

#### Linux (Ubuntu)

```shell
sudo apt-get install pandoc tesseract-ocr
```

#### MacOS

```shell
brew install tesseract pandoc
```

#### Windows

```shell
choco install -y tesseract pandoc
```

Notes:

- in most distributions the tesseract-ocr package is split into multiple packages, you may need to install any language models you need aside from English separately.
- please consult the official documentation for these libraries for the most up-to-date installation instructions for your platform.

## Architecture

Kreuzberg integrates:

- **PDF Processing**:
  - `pdfium2` for searchable PDFs
  - Tesseract OCR for scanned content
- **Document Conversion**:
  - Pandoc for many document and markup formats
  - `python-pptx` for PowerPoint files
  - `html-to-markdown` for HTML content
  - `calamine` for Excel spreadsheets (with multi-sheet support)
- **Text Processing**:
  - Smart encoding detection
  - Markdown and plain text handling

### Supported Formats

#### Document Formats

- PDF (`.pdf`, both searchable and scanned)
- Microsoft Word (`.docx`)
- PowerPoint presentations (`.pptx`)
- OpenDocument Text (`.odt`)
- Rich Text Format (`.rtf`)
- EPUB (`.epub`)
- DocBook XML (`.dbk`, `.xml`)
- FictionBook (`.fb2`)
- LaTeX (`.tex`, `.latex`)
- Typst (`.typ`)

#### Markup and Text Formats

- HTML (`.html`, `.htm`)
- Plain text (`.txt`) and Markdown (`.md`, `.markdown`)
- reStructuredText (`.rst`)
- Org-mode (`.org`)
- DokuWiki (`.txt`)
- Pod (`.pod`)
- Troff/Man (`.1`, `.2`, etc.)

#### Data and Research Formats

- Spreadsheets (`.xlsx`, `.xls`, `.xlsm`, `.xlsb`, `.xlam`, `.xla`, `.ods`)
- CSV (`.csv`) and TSV (`.tsv`) files
- OPML files (`.opml`)
- Jupyter Notebooks (`.ipynb`)
- BibTeX (`.bib`) and BibLaTeX (`.bib`)
- CSL-JSON (`.json`)
- EndNote and JATS XML (`.xml`)
- RIS (`.ris`)

#### Image Formats

- JPEG (`.jpg`, `.jpeg`, `.pjpeg`)
- PNG (`.png`)
- TIFF (`.tiff`, `.tif`)
- BMP (`.bmp`)
- GIF (`.gif`)
- JPEG 2000 family (`.jp2`, `.jpm`, `.jpx`, `.mj2`)
- WebP (`.webp`)
- Portable anymap formats (`.pbm`, `.pgm`, `.ppm`, `.pnm`)

## Usage

Kreuzberg provides both async and sync APIs for text extraction, including batch processing. The library exports the following main functions:

- Single Item Processing:

  - `extract_file()`: Async function to extract text from a file (accepts string path or `pathlib.Path`)
  - `extract_bytes()`: Async function to extract text from bytes (accepts a byte string)
  - `extract_file_sync()`: Synchronous version of `extract_file()`
  - `extract_bytes_sync()`: Synchronous version of `extract_bytes()`

- Batch Processing:

  - `batch_extract_file()`: Async function to extract text from multiple files concurrently
  - `batch_extract_bytes()`: Async function to extract text from multiple byte contents concurrently
  - `batch_extract_file_sync()`: Synchronous version of `batch_extract_file()`
  - `batch_extract_bytes_sync()`: Synchronous version of `batch_extract_bytes()`

### Configuration Parameters

All extraction functions accept the following optional parameters for configuring OCR and performance:

#### OCR Configuration

- `force_ocr` (default: `False`): Forces OCR processing even for searchable PDFs.

- `language` (default: `eng`): Specifies the language model for Tesseract OCR. This affects text recognition accuracy for documents in different languages. Examples:

  - `eng` for English
  - `deu` for German
  - `fra` for French
  - `spa` for Spanish
  - `ita` for Italian
  - `jpn` for Japanese
  - `kor` for Korean
  - `chi_sim` for Simplified Chinese
  - `chi_tra` for Traditional Chinese
  - `rus` for Russian
  - `ara` for Arabic
  - `hin` for Hindi
  - `eng+deu` for English and German (multi-language)

  Notes:

  - The order of languages affects processing time and accuracy. The first language is treated as the primary language.
  - For PaddleOCR, the supported language codes are different: `ch` (Chinese), `en` (English), `french`, `german`, `japan`, and `korean`.
  - Installing additional language models may be required. For Tesseract, install language packs for your OS (e.g., `tesseract-ocr-deu` for German on Ubuntu).

- `psm` (Page Segmentation Mode, default: `PSM.AUTO`): Controls how Tesseract analyzes page layout. Options include:

  - `PSM.AUTO` (Default): Automatic page segmentation with orientation detection
  - `PSM.SINGLE_BLOCK`: Treat the image as a single text block
  - `PSM.SINGLE_LINE`: Treat the image as a single text line
  - `PSM.SINGLE_WORD`: Treat the image as a single word
  - `PSM.SINGLE_CHAR`: Treat the image as a single character
  - `PSM.SPARSE_TEXT`: Find as much text as possible without assuming a particular structure
  - `PSM.SPARSE_TEXT_OSD`: Like SPARSE_TEXT but with orientation and script detection

  When to use different PSM modes:

  - Use `PSM.SINGLE_BLOCK` for documents with simple layouts or when you want to preserve paragraph structure
  - Use `PSM.SINGLE_LINE` for receipts, labels, or single-line text
  - Use `PSM.SPARSE_TEXT` for documents with scattered text elements like forms or tables

Consult the [Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/) for more information on both options.

#### Processing Configuration

- `max_processes` (default: CPU count): Maximum number of concurrent processes for Tesseract.

### Quick Start

```python
from pathlib import Path
from kreuzberg import extract_file, PSMMode
from kreuzberg import ExtractionResult


# Basic file extraction
async def extract_document():
    # Extract from a PDF file with default settings
    pdf_result: ExtractionResult = await extract_file("document.pdf")
    print(f"Content: {pdf_result.content}")

    # Extract from an image with German language model
    img_result = await extract_file(
        "scan.png",
        language="deu",  # German language model
        psm=PSMMode.SINGLE_BLOCK,  # Treat as single block of text
        max_processes=4  # Limit concurrent processes
    )
    print(f"Image text: {img_result.content}")

    # Extract from a multi-language document (English + Spanish)
    multi_lang_result = await extract_file(
        "multilingual.pdf",
        language="eng+spa",  # English and Spanish language models
        force_ocr=True  # Force OCR even if searchable text exists
    )
    print(f"Multilingual content: {multi_lang_result.content}")

    # Extract from Word document with metadata
    docx_result = await extract_file(Path("document.docx"))
    if docx_result.metadata:
        print(f"Title: {docx_result.metadata.get('title')}")
        print(f"Author: {docx_result.metadata.get('creator')}")
```

### Extracting Bytes

```python
from kreuzberg import extract_bytes
from kreuzberg import ExtractionResult


async def process_upload(file_content: bytes, mime_type: str) -> ExtractionResult:
    """Process uploaded file content with known MIME type."""
    return await extract_bytes(
        file_content,
        mime_type=mime_type,
    )


# Example usage with different file types
async def handle_uploads(docx_bytes: bytes, pdf_bytes: bytes, image_bytes: bytes):
    # Process PDF upload
    pdf_result = await process_upload(pdf_bytes, mime_type="application/pdf")
    print(f"PDF content: {pdf_result.content}")
    print(f"PDF metadata: {pdf_result.metadata}")

    # Process image upload (will use OCR)
    img_result = await process_upload(image_bytes, mime_type="image/jpeg")
    print(f"Image text: {img_result.content}")

    # Process Word document upload
    docx_result = await process_upload(
        docx_bytes,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    print(f"Word content: {docx_result.content}")
```

### Batch Processing

Kreuzberg supports efficient batch processing of multiple files or byte contents:

```python
from pathlib import Path
from kreuzberg import batch_extract_file, batch_extract_bytes, batch_extract_file_sync


# Process multiple files concurrently
async def process_documents(file_paths: list[Path]) -> None:
    # Extract from multiple files
    results = await batch_extract_file(file_paths)
    for path, result in zip(file_paths, results):
        print(f"File {path}: {result.content[:100]}...")


# Process multiple uploaded files concurrently
async def process_uploads(contents: list[tuple[bytes, str]]) -> None:
    # Each item is a tuple of (content, mime_type)
    results = await batch_extract_bytes(contents)
    for (_, mime_type), result in zip(contents, results):
        print(f"Upload {mime_type}: {result.content[:100]}...")


# Synchronous batch processing is also available
def process_documents_sync(file_paths: list[Path]) -> None:
    results = batch_extract_file_sync(file_paths)
    for path, result in zip(file_paths, results):
        print(f"File {path}: {result.content[:100]}...")
```

Features:

- Ordered results
- Concurrent processing
- Error handling per item
- Async and sync interfaces
- Same options as single extraction

### PDF Processing

Kreuzberg employs a smart approach to PDF text extraction:

1. **Searchable Text Detection**: First attempts to extract text directly from searchable PDFs using `pdfium2`.

1. **Text Validation**: Extracted text is validated for corruption by checking for:

   - Control and non-printable characters
   - Unicode replacement characters (�)
   - Zero-width spaces and other invisible characters
   - Empty or whitespace-only content

1. **Automatic OCR Fallback**: If the extracted text appears corrupted or if the PDF is image-based, automatically falls back to OCR using Tesseract.

This approach works well for searchable PDFs and standard text documents. For complex OCR (e.g., handwriting, photographs), use a specialized tool.

### PDF Processing Options

You can control PDF processing behavior using optional parameters:

```python
from kreuzberg import extract_file, PSMMode


async def process_pdf():
  # Default behavior: auto-detect and use OCR if needed
  # By default, max_processes=1 for safe operation
  result = await extract_file("document.pdf")
  print(result.content)

  # Force OCR even for searchable PDFs
  result = await extract_file("document.pdf", force_ocr=True)
  print(result.content)

  # Control OCR concurrency for large documents
  # Warning: High concurrency values can cause system resource exhaustion
  # Start with a low value and increase based on your system's capabilities
  result = await extract_file(
    "large_document.pdf",
    max_processes=4  # Process up to 4 pages concurrently
  )
  print(result.content)

  # Process a scanned PDF (automatically uses OCR)
  result = await extract_file("scanned.pdf")
  print(result.content)

  # Process a PDF with custom OCR settings
  result = await extract_file(
    "invoice.pdf",
    language="eng",  # English language model
    psm=PSMMode.SPARSE_TEXT,  # Better for forms and invoices
    force_ocr=True  # Force OCR processing
  )
  print(result.content)

  # Process a PDF with multiple languages
  result = await extract_file(
    "international_document.pdf",
    language="eng+fra+deu",  # English, French, and German
    max_processes=2  # Balance between speed and resource usage
  )
  print(result.content)
```

### ExtractionResult Object

All extraction functions return an `ExtractionResult` or a list thereof (for batch functions). The `ExtractionResult` object is a `NamedTuple`:

- `content`: The extracted text (str)
- `mime_type`: Output format ("text/plain" or "text/markdown" for Pandoc conversions)
- `metadata`: A metadata dictionary. Currently this dictionary is only populated when extracting documents using pandoc.

```python
from kreuzberg import extract_file, ExtractionResult, Metadata

async def process_document(path: str) -> tuple[str, str, Metadata]:
    # Access as a named tuple
    result: ExtractionResult = await extract_file(path)
    print(f"Content: {result.content}")
    print(f"Format: {result.mime_type}")

    # Or unpack as a tuple
    content, mime_type, metadata = await extract_file(path)
    return content, mime_type, metadata
```

### Error Handling

Kreuzberg provides comprehensive error handling through several exception types, all inheriting from `KreuzbergError`. Each exception includes helpful context information for debugging.

```python
from kreuzberg import (
    extract_file,
    ValidationError,
    ParsingError,
    OCRError,
    MissingDependencyError
)

async def safe_extract(path: str) -> str:
    try:
        result = await extract_file(path)
        return result.content

    except ValidationError as e:
        # Input validation issues
        # - Unsupported or undetectable MIME types
        # - Missing files
        # - Invalid input parameters
        print(f"Validation failed: {e}")

    except OCRError as e:
        # OCR-specific issues
        # - Tesseract processing failures
        # - Image conversion problems
        print(f"OCR failed: {e}")

    except MissingDependencyError as e:
        # System dependency issues
        # - Missing Tesseract OCR
        # - Missing Pandoc
        # - Incompatible versions
        print(f"Dependency missing: {e}")

    except ParsingError as e:
        # General processing errors
        # - PDF parsing failures
        # - Format conversion issues
        # - Encoding problems
        print(f"Processing failed: {e}")

    return ""
```

All exceptions include:

- Error message
- Context in the `context` attribute
- String representation
- Exception chaining

## OCR Best Practices

Kreuzberg provides flexible OCR capabilities through Tesseract and PaddleOCR. Here are some best practices for optimal results:

### Language Selection

- **Match document language**: Always specify the correct language model for your documents. Using the wrong language model significantly reduces accuracy.
- **Multi-language documents**: For documents with multiple languages, list them in order of prevalence (e.g., `eng+deu` for primarily English with some German).
- **Language model installation**: Ensure you have the required language models installed for Tesseract. Most distributions only include English by default.

### Page Segmentation Mode (PSM)

- **Default setting**: For most documents, the default `PSM.AUTO` works well.
- **Specific document types**:
  - Use `PSM.SINGLE_BLOCK` for simple layouts with continuous text
  - Use `PSM.SINGLE_LINE` for receipts or single lines of text
  - Use `PSM.SPARSE_TEXT` for forms, tables, or scattered text elements
  - Use `PSM.SINGLE_WORD` or `PSM.SINGLE_CHAR` only for specialized applications

### Performance Optimization

- **Concurrency**: Set `max_processes` based on your system's capabilities. Start with a low value (2-4) and increase if needed.
- **Memory usage**: OCR can be memory-intensive. For large documents, consider processing in batches.
- **Image quality**: Better results come from higher quality images. Consider preprocessing images (contrast enhancement, deskewing) before OCR.

### Troubleshooting

- **Poor OCR results**: Try different PSM modes or language combinations.
- **Slow processing**: Reduce the number of languages or limit `max_processes`.
- **Missing text**: Try `force_ocr=True` for PDFs with embedded but poorly recognized text.

## Contribution

This library is open to contribution. Feel free to open issues or submit PRs. Its better to discuss issues before
submitting PRs to avoid disappointment.

### Local Development

1. Clone the repo

1. Install the system dependencies

1. Install the full dependencies with `uv sync`

1. Install the pre-commit hooks with:

   ```shell
   pre-commit install && pre-commit install --hook-type commit-msg
   ```

1. Make your changes and submit a PR

## License

This library uses the MIT license.
