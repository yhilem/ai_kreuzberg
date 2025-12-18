# PDFium WASM Integration Guide

This guide explains how to use PDF extraction with kreuzberg-wasm, including the required PDFium initialization.

## Overview

Kreuzberg uses the high-performance PDFium library (from Google Chrome) for PDF processing. In WebAssembly environments, PDFium runs as a separate WASM module that must be initialized before PDF extraction can work.

## Quick Start

### 1. Install kreuzberg-wasm

```bash
npm install @kreuzberg/wasm
```

### 2. Basic PDF Extraction

```javascript
import init, { initialize_pdfium_render, extract_from_bytes } from '@kreuzberg/wasm';
import pdfiumModule from '@kreuzberg/wasm/pdfium.js';

async function extractPDF(pdfBytes) {
    // Step 1: Initialize kreuzberg WASM
    const wasm = await init();

    // Step 2: Load PDFium WASM module
    const pdfium = await pdfiumModule();

    // Step 3: Bind kreuzberg to PDFium (required before PDF operations)
    const success = initialize_pdfium_render(pdfium, wasm, false);
    if (!success) {
        throw new Error('Failed to initialize PDFium');
    }

    // Step 4: Extract text from PDF
    const result = await extract_from_bytes(pdfBytes, {
        extract_metadata: true,
        extract_images: false
    });

    return result;
}

// Usage
const pdfFile = document.querySelector('#file-input').files[0];
const bytes = new Uint8Array(await pdfFile.arrayBuffer());
const result = await extractPDF(bytes);
console.log(result.text);
```

## Initialization Details

### initialize_pdfium_render Function

```typescript
function initialize_pdfium_render(
    pdfium_wasm_module: any,    // Loaded PDFium Emscripten module
    local_wasm_module: any,      // Kreuzberg WASM module instance
    debug: boolean               // Enable debug logging
): boolean;                      // Returns true on success
```

**Parameters:**
- `pdfium_wasm_module`: The loaded PDFium WASM module (obtained from `pdfiumModule()`)
- `local_wasm_module`: The kreuzberg WASM instance (returned from `init()`)
- `debug`: Set to `true` for detailed console logging during initialization

**Returns:**
- `true` if initialization succeeded
- `false` if initialization failed

### When to Initialize

PDFium must be initialized:
- **Before** any PDF extraction operations
- **After** loading both kreuzberg and PDFium WASM modules
- **Once per page load** (initialization is global and persists)

You can initialize PDFium once at application startup and use it throughout your app's lifetime.

## Error Handling

### "PdfiumWASMModuleNotConfigured" Error

This error indicates that `initialize_pdfium_render()` was not called (or failed) before attempting PDF extraction.

**Solution:**
```javascript
try {
    const result = await extract_from_bytes(pdfBytes, config);
} catch (error) {
    if (error.message.includes('PdfiumWASMModuleNotConfigured')) {
        console.error('PDFium was not initialized. Call initialize_pdfium_render() first.');
        // Re-initialize PDFium
        await initializePdfiumIfNeeded();
    }
}
```

### Initialization Failure

If `initialize_pdfium_render()` returns `false`:

```javascript
const success = initialize_pdfium_render(pdfium, wasm, true); // Enable debug
if (!success) {
    console.error('PDFium initialization failed. Check console for details.');
    // Common causes:
    // 1. PDFium WASM module not loaded correctly
    // 2. WASM modules incompatible
    // 3. Memory allocation failure
}
```

## File Locations

### PDFium WASM Files

When building from source, PDFium files are located at:
```
target/wasm32-unknown-unknown/release/build/kreuzberg-*/out/pdfium/release/node/
├── pdfium.js          # Emscripten loader
├── pdfium.wasm        # PDFium library (~3.8MB)
└── index.html         # Test page
```

### Publishing Package

When publishing an npm package, include PDFium files:

```json
{
  "files": [
    "pkg/*.js",
    "pkg/*.wasm",
    "pkg/*.d.ts",
    "pkg/pdfium.js",
    "pkg/pdfium.wasm"
  ]
}
```

Copy PDFium files to your package:
```bash
cp target/wasm32-unknown-unknown/release/build/kreuzberg-*/out/pdfium/release/node/pdfium.* pkg/
```

## Advanced Usage

### Lazy Initialization

Initialize PDFium only when needed:

```javascript
let pdfiumInitialized = false;

async function ensurePdfiumInitialized() {
    if (pdfiumInitialized) return;

    const wasm = await init();
    const pdfium = await pdfiumModule();
    const success = initialize_pdfium_render(pdfium, wasm, false);

    if (!success) {
        throw new Error('Failed to initialize PDFium');
    }

    pdfiumInitialized = true;
}

async function extractPDF(bytes) {
    await ensurePdfiumInitialized();
    return extract_from_bytes(bytes, { extract_metadata: true });
}
```

### Debug Mode

Enable debug logging to troubleshoot initialization issues:

```javascript
const success = initialize_pdfium_render(pdfium, wasm, true); // Debug enabled

// Console will show detailed logs:
// - PDFium module loading
// - Function binding
// - Memory allocation
// - Initialization status
```

### Web Worker Support

PDFium can be initialized in a Web Worker:

```javascript
// worker.js
import init, { initialize_pdfium_render, extract_from_bytes } from '@kreuzberg/wasm';
import pdfiumModule from '@kreuzberg/wasm/pdfium.js';

let initialized = false;

self.onmessage = async (event) => {
    if (!initialized) {
        const wasm = await init();
        const pdfium = await pdfiumModule();
        initialize_pdfium_render(pdfium, wasm, false);
        initialized = true;
    }

    const result = await extract_from_bytes(event.data.bytes, event.data.config);
    self.postMessage(result);
};
```

## Browser Compatibility

### Supported Browsers

- Chrome 91+ ✓
- Firefox 90+ ✓
- Safari 16.4+ ✓
- Edge 91+ ✓

### Memory Requirements

- Minimum: 50MB RAM for small PDFs
- Recommended: 200MB+ for large PDFs
- PDFium WASM has non-growable heap (fixed size)

For large PDFs (100+ pages), consider:
- Server-side processing
- Page-by-page extraction
- Streaming when available

## Troubleshooting

### Module Not Found Errors

**Error:** `Cannot find module '@kreuzberg/wasm/pdfium.js'`

**Solution:**
1. Verify pdfium.js is in your package/public directory
2. Update import path to match your file structure
3. Check that pdfium.js and pdfium.wasm are served together

### WASM Instantiation Failures

**Error:** `WebAssembly.instantiate failed`

**Causes:**
- Insufficient memory
- CORS issues (WASM files must be same-origin)
- Large PDF file size

**Solution:**
```javascript
// Serve WASM files with correct MIME type
// Server configuration example (nginx):
types {
    application/wasm wasm;
}
```

### Performance Issues

For slow extraction:
1. Use release builds (development builds are much slower)
2. Enable WASM SIMD if browser supports it
3. Process PDFs in Web Workers to avoid blocking UI
4. Consider pagination for large documents

## Example Projects

See complete examples:
- `examples/pdf-extraction.html` - Browser-based PDF viewer
- `examples/worker-extraction.js` - Web Worker implementation
- `tests/pdf_extraction.rs` - Rust WASM tests

## License

The PDFium library is licensed under BSD-3-Clause by Google.
Kreuzberg is dual-licensed under MIT OR Apache-2.0.
