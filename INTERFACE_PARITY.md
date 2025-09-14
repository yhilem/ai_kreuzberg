# Interface Parity Tasks

## CLI Missing Features

1. Add `--extract-entities` flag to CLI extract command
2. Add `--extract-keywords` flag to CLI extract command
3. Add `--auto-detect-language` flag to CLI extract command
4. Add `--keyword-count` option to CLI extract command

## MCP Missing Features

5. Add Tesseract PSM mode parameter to MCP extract_document
6. Add Tesseract output format parameter to MCP extract_document
7. Add Tesseract table detection parameter to MCP extract_document
8. Add batch_extract_document tool to MCP server
9. Add batch_extract_bytes tool to MCP server

## Implementation Order

- Python engineer: Implement CLI flags (tasks 1-4)
- Python engineer: Implement MCP advanced OCR params (tasks 5-7)
- Python engineer: Implement MCP batch tools (tasks 8-9)
- Code reviewer: Review all changes
- Python engineer: Fix any issues from review
