# LLM Configuration Guide

Marker supports multiple LLM providers for enhanced document conversion accuracy.

## Quick Reference

| Provider | Service Class | Key Environment Variables |
|----------|--------------|---------------------------|
| Alibaba DashScope | `marker.services.openai.OpenAIService` | `OPENAI_API_KEY` |
| Google Gemini | `marker.services.gemini.GoogleGeminiService` | `GOOGLE_API_KEY` |
| Google Vertex | `marker.services.vertex.GoogleVertexService` | `VERTEX_PROJECT_ID` |
| Anthropic Claude | `marker.services.claude.ClaudeService` | `ANTHROPIC_API_KEY` |
| OpenAI | `marker.services.openai.OpenAIService` | `OPENAI_API_KEY` |
| Azure OpenAI | `marker.services.azure_openai.AzureOpenAIService` | `AZURE_ENDPOINT`, `AZURE_API_KEY` |
| Ollama (Local) | `marker.services.ollama.OllamaService` | `OLLAMA_BASE_URL` |

## Alibaba Cloud (DashScope)

### Configuration

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser

config = {
    "use_llm": True,
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_base_url": "https://coding.dashscope.aliyuncs.com/v1",
    "openai_api_key": "sk-xxx",
    "openai_model": "qwen3.5-plus",
}

config_parser = ConfigParser(config)
converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    llm_service=config_parser.get_llm_service()
)
```

### Available Models

- `qwen3.5-plus` - Recommended for document conversion
- `qwen3.5-turbo` - Faster, lower cost
- `qwen3.5-max` - Highest quality

## Google Gemini

### Default (Developer API)

```bash
export GOOGLE_API_KEY="your-key"
```

```python
config = {
    "use_llm": True,
    "gemini_api_key": "your-key",
}
```

### Vertex AI

```python
config = {
    "use_llm": True,
    "llm_service": "marker.services.vertex.GoogleVertexService",
    "vertex_project_id": "your-project-id",
}
```

## Anthropic Claude

```python
config = {
    "use_llm": True,
    "llm_service": "marker.services.claude.ClaudeService",
    "claude_api_key": "your-key",
    "claude_model_name": "claude-3-sonnet-20240229",
}
```

## OpenAI

```python
config = {
    "use_llm": True,
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_api_key": "your-key",
    "openai_model": "gpt-4o",
}
```

## Azure OpenAI

```python
config = {
    "use_llm": True,
    "llm_service": "marker.services.azure_openai.AzureOpenAIService",
    "azure_endpoint": "https://your-resource.openai.azure.com/",
    "azure_api_key": "your-key",
    "deployment_name": "your-deployment",
}
```

## Ollama (Local)

```python
config = {
    "use_llm": True,
    "llm_service": "marker.services.ollama.OllamaService",
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "llama3.2",
}
```

## Advanced Options

### Custom Prompts

```python
config = {
    "use_llm": True,
    "block_correction_prompt": "Your custom prompt for post-processing",
}
```

### Table-Specific LLM

Use `TableConverter` for table extraction with LLM:

```python
from marker.converters.table import TableConverter

config = {
    "use_llm": True,
    "force_layout_block": "Table",
    "output_format": "json",
}
```
