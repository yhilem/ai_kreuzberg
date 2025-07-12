# Kreuzberg

Kreuzberg is a complete Open Source Document Intelligence framework. Its Built by engineers for production workloads -
its not a data science / research orientated tool, but rather a pragmatic swiss-army knife that is meant to deliver.
Yes, Python, when coupled with robust technologies such as `pdfium`, `tesseract` and `pandoc` can do quite a lot.
Kreuzberg was also created (primarily) in Kreuzberg - the famous and beautiful neighborhood of Berlin.

## Why Kreuzberg?

At the danger of over-selling, there are actually quite a lot of reasons why use Kreuzberg. You can read them below.
BUT - this is not necessarily a mutually exclusive solution. For example.
many text extraction pipelines can integrate a library such as Kreuzberg with some kind of heuristics on when to use it
and when use something else.

### 🚀 Performance

- [benchmarked as the fastest framework](https://goldziher.github.io/python-text-extraction-libs-benchmarks/) - 2-3x
    faster than the nearest alternatives
- Minimal footprint: 71MB install vs 1GB+ for competitors
- Lowest memory usage (~530MB average) optimized for production workloads
- Edge and serverless ready - deploy anywhere without heavy dependencies

### 🛠️ Engineering Quality

- Built by software engineers with modern Python best practices
- 95%+ test coverage with comprehensive test suite
- Thoroughly benchmarked and profiled for real-world performance
- Only framework offering true async/await support alongside sync APIs
- Robust error handling and detailed logging

### 🎯 Developer Experience

- Works out of the box with sane defaults, scales with your needs
- Native MCP server for AI tool integration (Claude Desktop, Cursor)
- Full type safety with excellent IDE support (completions)
- Comprehensive documentation including full API reference

### 🌍 Deployment Options

- Docker images for all architectures (AMD64, ARM64)
- Cloud native - AWS Lambda, Google Cloud Functions, Azure Functions
- CPU-only processing - no GPU requirements, lower energy consumption
- 100% local processing - no external API dependencies
- Multiple deployment modes: CLI, REST API, MCP server

### 🎯 Complete Solution

- Universal format support: PDFs, images, Office docs, HTML, spreadsheets, presentations
- Multiple OCR engines: Tesseract, EasyOCR, PaddleOCR with intelligent fallbacks
- Advanced features: Table extraction, metadata extraction, content chunking for RAG
- Production tools: REST API, CLI tools, batch processing, custom extractors
- Fully extensible: Add your own extractors

## Perfect for Modern Applications

Kreuzberg was architected for **RAG (Retrieval Augmented Generation)** applications, **serverless functions**, and \*
*cloud-native deployments*\*. Whether you're building AI applications, processing pipelines, or document management
systems, Kreuzberg delivers unmatched performance with minimal complexity.
