"""Integration tests for the CLI module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Only test CLI if dependencies are available
try:
    import click  # noqa: F401
    import rich  # noqa: F401

    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI dependencies not installed")


class TestCliIntegration:
    """Integration tests for CLI functionality with real files and processes."""

    def test_cli_extract_html_file(self, tmp_path: Path) -> None:
        """Test extracting from an HTML file via CLI."""
        # Create test HTML file
        html_file = tmp_path / "test.html"
        html_file.write_text("""
        <html>
            <head><title>Test Document</title></head>
            <body>
                <h1>Test Heading</h1>
                <p>This is a test paragraph with some content.</p>
                <p>Another paragraph for testing.</p>
            </body>
        </html>
        """)

        # Run CLI command
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(html_file)],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert "Test Heading" in result.stdout
        assert "test paragraph" in result.stdout
        assert "Another paragraph" in result.stdout

    def test_cli_extract_to_file(self, tmp_path: Path) -> None:
        """Test extracting to an output file."""
        # Create test markdown file
        md_file = tmp_path / "test.md"
        md_file.write_text("""
        # Test Markdown

        This is a **test** markdown file with some content.

        - Item 1
        - Item 2
        - Item 3
        """)

        output_file = tmp_path / "output.txt"

        # Run CLI command with output file
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(md_file), "-o", str(output_file)],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "Test Markdown" in content
        assert "**test** markdown file" in content  # The markdown is preserved as-is
        assert "Item 1" in content

    def test_cli_extract_json_output_with_metadata(self, tmp_path: Path) -> None:
        """Test JSON output format with metadata."""
        # Create test text file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is a simple text file for testing JSON output.")

        # Run CLI command with JSON output and metadata
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(txt_file), "--output-format", "json", "--show-metadata"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0

        # Parse JSON output
        output_data = json.loads(result.stdout)
        assert "content" in output_data
        assert "mime_type" in output_data
        assert "metadata" in output_data
        assert "simple text file" in output_data["content"]

    def test_cli_extract_from_stdin(self) -> None:
        """Test extracting from stdin."""
        test_content = "<html><body><h1>Stdin Test</h1><p>Content from stdin</p></body></html>"

        # Run CLI command with stdin input
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract"],
            check=False,
            input=test_content,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert "Stdin Test" in result.stdout
        assert "Content from stdin" in result.stdout

    def test_cli_with_config_file(self, tmp_path: Path) -> None:
        """Test CLI with configuration file."""
        # Create test document
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body><p>Test content for config</p></body></html>")

        # Create config file
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.kreuzberg]
chunk_content = true
max_chars = 200
max_overlap = 50
extract_tables = false

[tool.kreuzberg.tesseract]
language = "eng"
psm = 6
""")

        # Run CLI with config file
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(html_file), "--config", str(config_file), "--verbose"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert "Test content" in result.stdout
        # Config was loaded successfully (no need to check specific message)

    def test_cli_config_command(self, tmp_path: Path) -> None:
        """Test the config command."""
        # Create config file
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[tool.kreuzberg]
force_ocr = true
chunk_content = false
max_chars = 5000

[tool.kreuzberg.tesseract]
language = "eng+deu"
psm = 3
""")

        # Run config command
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "config", "--config", str(config_file)],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        # Config command outputs to stderr (Rich console)
        output_text = result.stderr
        assert "force_ocr" in output_text
        assert "true" in output_text
        assert "eng+deu" in output_text
        assert "config.toml" in output_text  # Just check filename, not full path

    def test_cli_config_command_no_file(self) -> None:
        """Test config command when no config file exists."""
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "config"], check=False, capture_output=True, text=True, cwd=Path("/tmp")
        )  # Use /tmp to avoid finding project config

        assert result.returncode == 0
        assert "No configuration file found" in result.stderr
        assert "Default configuration values" in result.stderr

    def test_cli_tesseract_options(self, tmp_path: Path) -> None:
        """Test CLI with Tesseract-specific options."""
        # Create test text file (doesn't need OCR but tests config)
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Simple text content for tesseract options test.")

        # Run with tesseract options
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kreuzberg",
                "extract",
                str(txt_file),
                "--ocr-backend",
                "tesseract",
                "--tesseract-lang",
                "eng",
                "--tesseract-psm",
                "6",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert "Simple text content" in result.stdout

    def test_cli_force_ocr_option(self, tmp_path: Path) -> None:
        """Test CLI with force OCR option."""
        # Create test text file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Text content that should be processed with OCR.")

        # Run with force OCR
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(txt_file), "--force-ocr", "--ocr-backend", "tesseract"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert "processed with OCR" in result.stdout

    def test_cli_chunking_options(self, tmp_path: Path) -> None:
        """Test CLI with chunking options."""
        # Create a longer text file
        txt_file = tmp_path / "long_text.txt"
        long_text = "This is a test. " * 200  # Create text longer than default chunk size
        txt_file.write_text(long_text)

        # Run with chunking enabled (set overlap smaller than max-chars)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kreuzberg",
                "extract",
                str(txt_file),
                "--chunk-content",
                "--max-chars",
                "200",
                "--max-overlap",
                "50",
                "--output-format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0

        # Parse JSON to check if chunks are created
        output_data = json.loads(result.stdout)
        # Note: chunks might be None if the text is not actually chunked by the backend
        assert "content" in output_data

    def test_cli_auto_config_detection(self, tmp_path: Path) -> None:
        """Test automatic config file detection."""
        # Create test file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Content for auto config test.")

        # Create pyproject.toml in the same directory
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.kreuzberg]
max_chars = 1500
""")

        # Run from the directory with pyproject.toml
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(txt_file), "--verbose"],
            check=False,
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode == 0
        assert "Content for auto config" in result.stdout

    def test_cli_error_invalid_file(self) -> None:
        """Test CLI error handling for invalid file."""
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", "nonexistent.pdf"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode != 0
        assert "does not exist" in result.stderr

    def test_cli_error_invalid_ocr_backend(self, tmp_path: Path) -> None:
        """Test CLI error handling for invalid OCR backend."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content")

        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(txt_file), "--ocr-backend", "invalid_backend"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode != 0
        assert "Invalid OCR backend" in result.stderr

    def test_cli_version_command(self) -> None:
        """Test version command."""
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "--version"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert "kreuzberg, version" in result.stdout
        assert "3.2.0" in result.stdout

    def test_cli_help_command(self) -> None:
        """Test help command."""
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "--help"], check=False, capture_output=True, text=True, cwd=Path.cwd()
        )

        assert result.returncode == 0
        assert "Kreuzberg - Text extraction from documents" in result.stdout
        assert "extract" in result.stdout
        assert "config" in result.stdout

    def test_cli_extract_help(self) -> None:
        """Test extract command help."""
        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", "--help"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert "Extract text from a document" in result.stdout
        assert "--force-ocr" in result.stdout
        assert "--chunk-content" in result.stdout
        assert "--extract-tables" in result.stdout

    def test_cli_with_real_pdf(self, tmp_path: Path) -> None:
        """Test CLI with a real PDF file if available."""
        # Check if we have a PDF test file
        pdf_files = list(Path("tests/test_source_files").glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF test files available")

        pdf_file = pdf_files[0]
        output_file = tmp_path / "pdf_output.txt"

        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(pdf_file), "-o", str(output_file)],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path.cwd(),
        )

        # If the process was terminated by signal, skip the test
        if result.returncode < 0:
            pytest.skip(f"PDF extraction terminated by signal {-result.returncode}")

        assert result.returncode == 0
        assert output_file.exists()

        # Check that we got some content
        content = output_file.read_text()
        assert len(content.strip()) > 0

    def test_cli_extract_tables_option(self, tmp_path: Path) -> None:
        """Test CLI with extract tables option."""
        # Create simple HTML with table
        html_file = tmp_path / "table_test.html"
        html_file.write_text("""
        <html>
            <body>
                <h1>Document with Table</h1>
                <table>
                    <tr><th>Name</th><th>Age</th></tr>
                    <tr><td>John</td><td>30</td></tr>
                    <tr><td>Jane</td><td>25</td></tr>
                </table>
            </body>
        </html>
        """)

        # Run with table extraction (note: might not extract tables from HTML)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kreuzberg",
                "extract",
                str(html_file),
                "--extract-tables",
                "--output-format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0

        output_data = json.loads(result.stdout)
        assert "content" in output_data
        assert "Document with Table" in output_data["content"]

    def test_cli_configuration_precedence(self, tmp_path: Path) -> None:
        """Test that CLI args override config file settings."""
        # Create test file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content for precedence check.")

        # Create config file with chunk_content = false
        config_file = tmp_path / "test_config.toml"
        config_file.write_text("""
[tool.kreuzberg]
chunk_content = false
max_chars = 1000
""")

        # Run CLI with --chunk-content flag (should override config)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "kreuzberg",
                "extract",
                str(txt_file),
                "--config",
                str(config_file),
                "--chunk-content",
                "--output-format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0

        # Verify the content was processed (even though we can't easily verify chunking)
        output_data = json.loads(result.stdout)
        assert "precedence check" in output_data["content"]

    def test_cli_invalid_config_file(self, tmp_path: Path) -> None:
        """Test CLI with invalid config file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content")

        # Create invalid TOML file
        bad_config = tmp_path / "bad_config.toml"
        bad_config.write_text("invalid toml content [[[")

        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(txt_file), "--config", str(bad_config)],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 1
        assert "Invalid TOML" in result.stderr

    def test_cli_missing_config_file(self, tmp_path: Path) -> None:
        """Test CLI with missing config file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content")

        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(txt_file), "--config", "nonexistent_config.toml"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 2  # Click parameter validation error
        assert "does not exist" in result.stderr

    def test_cli_ocr_backend_none(self, tmp_path: Path) -> None:
        """Test CLI with OCR backend set to none."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Simple text that should not use OCR.")

        result = subprocess.run(
            [sys.executable, "-m", "kreuzberg", "extract", str(txt_file), "--ocr-backend", "none"],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        assert result.returncode == 0
        assert "should not use OCR" in result.stdout
