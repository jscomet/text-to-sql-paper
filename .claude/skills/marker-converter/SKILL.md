---
name: marker-converter
description: Convert PDF, DOCX, and other documents to Markdown using Marker with optional LLM enhancement. Use when the user needs to convert documents (PDF, DOCX, PPTX, XLSX, EPUB, HTML) to Markdown format, process scanned documents with OCR, handle complex tables and formulas, batch convert multiple files, or configure LLM services for enhanced accuracy.
---

# Marker Document Converter

Convert documents to Markdown with high accuracy using the Marker library. Supports both fast local conversion and LLM-enhanced processing for complex documents.

## Quick Start

```bash
# Basic conversion (fast)
marker_single input.pdf

# LLM-enhanced conversion (better accuracy)
marker_single input.pdf --use_llm

# Force OCR for scanned documents
marker_single input.pdf --use_llm --force_ocr
```

## Python API

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# Basic conversion
converter = PdfConverter(artifact_dict=create_model_dict())
rendered = converter("input.pdf")
text, _, images = text_from_rendered(rendered)
```

## LLM Configuration

Configure LLM services for enhanced accuracy. See [references/llm-config.md](references/llm-config.md) for detailed provider setup.

### Alibaba Cloud (DashScope)

```python
config = {
    "use_llm": True,
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_base_url": "https://coding.dashscope.aliyuncs.com/v1",
    "openai_api_key": "your-api-key",
    "openai_model": "qwen3.5-plus",
}
```

### Other Providers

- **Gemini**: Set `GOOGLE_API_KEY`, use default service
- **Claude**: Use `marker.services.claude.ClaudeService`
- **OpenAI**: Use `marker.services.openai.OpenAIService`
- **Azure**: Use `marker.services.azure_openai.AzureOpenAI`
- **Ollama**: Use `marker.services.ollama.OllamaService`

## Batch Conversion

Use [scripts/batch_convert.py](scripts/batch_convert.py) for converting multiple files:

```bash
python scripts/batch_convert.py /path/to/input/dir /path/to/output/dir --use_llm
```

## Output Formats

- `markdown` (default): Clean Markdown with embedded images
- `json`: Structured JSON with block hierarchy
- `html`: HTML output
- `chunks`: Flattened chunks for RAG applications

## Common Options

| Option | Description |
|--------|-------------|
| `--use_llm` | Enable LLM enhancement |
| `--force_ocr` | Force OCR on all pages |
| `--output_format` | markdown/json/html/chunks |
| `--page_range` | Process specific pages (e.g., "0,5-10,20") |
| `--output_dir` | Custom output directory |

## When to Use LLM Mode

Use LLM enhancement when:
- Document contains complex tables spanning multiple pages
- Mathematical formulas need LaTeX formatting
- Document is a scanned image requiring OCR
- Forms need structured extraction
- Highest accuracy is required

Avoid LLM mode when:
- Processing simple, text-based PDFs
- Speed is critical
- API costs are a concern

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for common issues.

### First Run

Initial model download (~2-3GB) is required. Progress will be shown automatically.

### Memory Issues

Reduce workers for large documents:
```bash
marker_single large.pdf --workers 1
```

### GPU vs CPU

Device is auto-detected. Override with:
```bash
export TORCH_DEVICE=cuda  # or cpu, mps
```
