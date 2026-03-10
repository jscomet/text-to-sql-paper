# Marker Configuration Template
# Copy this file and customize for your environment

import os

# =============================================================================
# ALIBABA CLOUD (DASHSCOPE) - qwen3.5-plus
# =============================================================================

# 方式1: 直接配置（已内置默认配置）
ALIBABA_CONFIG = {
    "use_llm": True,
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_base_url": "https://coding.dashscope.aliyuncs.com/v1",
    "openai_api_key": "sk-sp-439b962366f7459db037434930cdeb7e",
    "openai_model": "qwen3.5-plus",
}

# 方式2: 从环境变量读取（推荐用于安全场景）
ALIBABA_CONFIG_FROM_ENV = {
    "use_llm": True,
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_base_url": os.getenv("DASHSCOPE_BASE_URL", "https://coding.dashscope.aliyuncs.com/v1"),
    "openai_api_key": os.getenv("DASHSCOPE_API_KEY", ""),
    "openai_model": os.getenv("DASHSCOPE_MODEL", "qwen3.5-plus"),
}

# Available models:
# - qwen3.5-plus (recommended)
# - qwen3.5-turbo (faster, lower cost)
# - qwen3.5-max (highest quality)


# =============================================================================
# GOOGLE GEMINI
# =============================================================================

GEMINI_CONFIG = {
    "use_llm": True,
    "gemini_api_key": "your-google-api-key",
    # Uses gemini-2.0-flash by default
}


# =============================================================================
# GOOGLE VERTEX AI
# =============================================================================

VERTEX_CONFIG = {
    "use_llm": True,
    "llm_service": "marker.services.vertex.GoogleVertexService",
    "vertex_project_id": "your-gcp-project-id",
}


# =============================================================================
# ANTHROPIC CLAUDE
# =============================================================================

CLAUDE_CONFIG = {
    "use_llm": True,
    "llm_service": "marker.services.claude.ClaudeService",
    "claude_api_key": "your-anthropic-api-key",
    "claude_model_name": "claude-3-sonnet-20240229",
}


# =============================================================================
# OPENAI
# =============================================================================

OPENAI_CONFIG = {
    "use_llm": True,
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_api_key": "your-openai-api-key",
    "openai_model": "gpt-4o",
}


# =============================================================================
# AZURE OPENAI
# =============================================================================

AZURE_CONFIG = {
    "use_llm": True,
    "llm_service": "marker.services.azure_openai.AzureOpenAIService",
    "azure_endpoint": "https://your-resource.openai.azure.com/",
    "azure_api_key": "your-azure-api-key",
    "deployment_name": "your-deployment-name",
}


# =============================================================================
# OLLAMA (LOCAL)
# =============================================================================

OLLAMA_CONFIG = {
    "use_llm": True,
    "llm_service": "marker.services.ollama.OllamaService",
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "llama3.2",
}


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

# from marker.converters.pdf import PdfConverter
# from marker.models import create_model_dict
# from marker.config.parser import ConfigParser
#
# # Choose your config
# config = ALIBABA_CONFIG  # or GEMINI_CONFIG, CLAUDE_CONFIG, etc.
#
# config_parser = ConfigParser(config)
# converter = PdfConverter(
#     config=config_parser.generate_config_dict(),
#     artifact_dict=create_model_dict(),
#     llm_service=config_parser.get_llm_service()
# )
#
# rendered = converter("input.pdf")
