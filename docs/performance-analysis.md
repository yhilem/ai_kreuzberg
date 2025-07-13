# Performance Analysis

## Overview

This page presents comprehensive performance analysis of Kreuzberg based on standardized benchmarking across 18 file formats. The data demonstrates Kreuzberg's position as the fastest Python CPU-based text extraction framework.

> **Live Benchmarks**: View real-time performance comparisons at [benchmarks.kreuzberg.dev](https://benchmarks.kreuzberg.dev/)
> **Methodology**: Full benchmark methodology and source code available at [github.com/Goldziher/python-text-extraction-libs-benchmarks](https://github.com/Goldziher/python-text-extraction-libs-benchmarks)

## Executive Summary

Kreuzberg achieves industry-leading performance metrics:

- **Speed**: Fastest Python CPU-based text extraction framework
- **Memory**: Lowest memory footprint at ~360MB average
- **Installation**: Minimal 71MB package size
- **Reliability**: 100% success rate across all tested formats

## Technical Performance Metrics

### Processing Speed

#### Throughput by File Size Category

| Category              | Kreuzberg Sync | Kreuzberg Async | Technical Notes                   |
| --------------------- | -------------- | --------------- | --------------------------------- |
| **Tiny (\<100KB)**    | 31.78 files/s  | 23.94 files/s   | Sync faster due to lower overhead |
| **Small (100KB-1MB)** | 8.91 files/s   | 9.31 files/s    | Async benefits from concurrency   |
| **Medium (1-10MB)**   | 2.42 files/s   | 3.16 files/s    | Async leverages multiprocessing   |

#### Processing Architecture

- **Synchronous Mode**: Direct execution path with minimal overhead, optimal for single-file operations
- **Asynchronous Mode**: Event-loop based with intelligent task scheduling, ideal for concurrent workloads
- **Multiprocessing**: Automatic CPU core utilization for compute-intensive operations (OCR, PDF parsing)
- **Memory Management**: Streaming architecture prevents memory bloat on large files

### Memory Efficiency

| Mode                | Memory Usage | Characteristics                                       |
| ------------------- | ------------ | ----------------------------------------------------- |
| **Kreuzberg Sync**  | 359.8 MB     | Baseline - minimal overhead, efficient GC             |
| **Kreuzberg Async** | 395.2 MB     | +10% due to event loop and concurrent task management |

**Memory optimization strategies:**

- Lazy loading of document components
- Streaming text extraction for large files
- Automatic garbage collection after each extraction
- Process pool recycling for long-running operations

### Installation Footprint

**Kreuzberg specifications:**

- **Package size**: 71 MB
- **Dependencies**: 43 packages
- **Core components**: PDFium, python-docx, python-pptx, pypandoc
- **Optional extras**: EasyOCR, PaddleOCR, GMFT (table extraction)

**Size optimization achieved through:**

- Selective dependency installation
- No bundled ML models
- Efficient binary packaging
- Modular architecture with optional components

### Reliability Metrics

**Kreuzberg achieves 100% success rate across all tested formats:**

- Zero timeouts or failures in benchmark suite
- Robust error handling with graceful degradation
- Comprehensive format support (18 file types)
- Consistent performance across file sizes

### Supported File Formats

**Comprehensive format coverage across 6 categories:**

| Category   | Formats                | Features                    |
| ---------- | ---------------------- | --------------------------- |
| Documents  | PDF, DOCX, PPTX, XLSX  | Full text, metadata, tables |
| Web/Markup | HTML, Markdown, RST    | Structure preservation      |
| Images     | PNG, JPG, JPEG, BMP    | OCR with multiple engines   |
| Email      | EML, MSG               | Headers, body, attachments  |
| Data       | CSV, JSON, YAML        | Native parsing              |
| Archives   | ZIP (containing above) | Recursive extraction        |

## Technical Architecture

### Performance Optimizations

**Speed optimizations:**

- Native C extensions (PDFium for PDFs, Tesseract for OCR)
- Efficient data handling with minimal copies
- Memory pooling for frequently used objects
- Parallel processing for multi-page documents

**Memory optimizations:**

- Streaming extraction for large files
- Lazy loading of document components
- Automatic resource cleanup
- Bounded memory usage regardless of file size

**Async implementation:**

- True async/await support (not just wrapper functions)
- Intelligent task scheduling
- Process pool for CPU-intensive operations
- Non-blocking I/O throughout the pipeline

## Production Deployment

### Infrastructure Benefits

**Resource efficiency:**

- Minimal memory footprint (~360MB) enables higher container density
- Small installation size (71MB) reduces image build times
- Fast processing speeds reduce compute costs
- Predictable resource usage simplifies capacity planning

**Deployment options:**

- Docker images for all architectures (linux/amd64, linux/arm64)
- Serverless compatible (AWS Lambda, Google Cloud Functions)
- Native Python package for traditional deployments
- REST API server for microservice architectures

**Operational advantages:**

- Zero external API dependencies
- Local processing for data sovereignty
- Configurable resource limits
- Comprehensive logging and monitoring

## Benchmark Methodology

### Test Environment

- **Platform**: Linux CI runners with standardized hardware
- **Python Version**: 3.12-3.13
- **Document Set**: 18 file formats across 6 categories
- **Metrics Collected**: Processing speed, memory usage, success rate
- **Methodology**: [Full details and source code](https://github.com/Goldziher/python-text-extraction-libs-benchmarks)

### Key Performance Indicators

**Kreuzberg demonstrates:**

- **Fastest processing**: Leading throughput across all file size categories
- **Lowest memory usage**: ~360MB average vs industry alternatives
- **Smallest footprint**: 71MB installation size
- **High reliability**: 100% success rate in comprehensive testing
- **Comprehensive format support**: 18 file types with consistent performance

## Conclusion

Kreuzberg's performance leadership stems from its efficient architecture, optimized implementation, and focus on real-world production needs. The combination of speed, reliability, and resource efficiency makes it the optimal choice for Python-based text extraction workloads.

For the latest benchmark results and to compare performance across different frameworks, visit [benchmarks.kreuzberg.dev](https://benchmarks.kreuzberg.dev/).

______________________________________________________________________

*Performance data is based on comprehensive benchmarking across real-world document corpus. Results may vary based on specific use cases and hardware configurations.*
