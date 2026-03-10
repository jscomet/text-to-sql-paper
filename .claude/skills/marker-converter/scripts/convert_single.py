#!/usr/bin/env python3
"""
Convert a single document to Markdown with various options.

This is a wrapper script that provides a simplified interface for common conversion tasks.
"""

import argparse
import os
import sys
from pathlib import Path

# Windows 控制台 UTF-8 编码设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser

# =============================================================================
# 阿里云 DashScope 配置
# =============================================================================

ALIBABA_CONFIG = {
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_base_url": "https://coding.dashscope.aliyuncs.com/v1",
    "openai_model": "qwen3.5-plus",
    # 从环境变量读取 API Key，或在此直接配置
    "openai_api_key": os.getenv("DASHSCOPE_API_KEY", "sk-sp-439b962366f7459db037434930cdeb7e"),
}

# 可选模型：
# - qwen3.5-plus    (推荐，平衡性能与成本)
# - qwen3.5-turbo   (更快，成本更低)
# - qwen3.5-max     (最高质量，成本较高)


def convert_document(
    input_path: str,
    output_dir: str = None,
    use_llm: bool = False,
    output_format: str = "markdown",
    page_range: str = None,
    force_ocr: bool = False,
    llm_config: dict = None
) -> str:
    """
    Convert a document to the specified format.

    Args:
        input_path: Path to input file
        output_dir: Output directory (default: same as input)
        use_llm: Enable LLM enhancement
        output_format: Output format (markdown/json/html/chunks)
        page_range: Page range to process (e.g., "0,5-10,20")
        force_ocr: Force OCR on all pages
        llm_config: Additional LLM configuration

    Returns:
        Path to output file
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Build configuration
    config = {
        "output_format": output_format,
    }

    if page_range:
        config["page_range"] = page_range

    if force_ocr:
        config["force_ocr"] = True

    if use_llm:
        config["use_llm"] = True
        if llm_config:
            config.update(llm_config)

    # Parse configuration
    config_parser = ConfigParser(config)

    # Create converter
    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service() if use_llm else None
    )

    # Convert document
    rendered = converter(str(input_file))
    text, _, images = text_from_rendered(rendered)

    # Determine output path
    if output_dir:
        output_path = Path(output_dir) / f"{input_file.stem}.md"
    else:
        output_path = input_file.parent / f"{input_file.stem}.md"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Convert a document to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  python convert_single.py document.pdf

  # LLM-enhanced conversion (默认使用阿里云 qwen3.5-plus)
  python convert_single.py document.pdf --use_llm

  # 快速使用阿里云 LLM
  python convert_single.py document.pdf --alibaba

  # 自定义阿里云配置
  python convert_single.py document.pdf --alibaba --llm_model qwen3.5-max

  # Process specific pages only
  python convert_single.py document.pdf --page_range "0,5-10"

  # Force OCR for scanned documents
  python convert_single.py document.pdf --force_ocr --alibaba
        """
    )

    parser.add_argument("input", help="Input file path")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("--use_llm", action="store_true", help="Enable LLM enhancement (默认使用阿里云)")
    parser.add_argument("--alibaba", action="store_true", help="使用阿里云 DashScope LLM (快捷方式)")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json", "html", "chunks"], help="Output format")
    parser.add_argument("--page_range", help="Page range to process (e.g., '0,5-10,20')")
    parser.add_argument("--force_ocr", action="store_true", help="Force OCR on all pages")

    # LLM options
    llm_group = parser.add_argument_group("LLM Configuration")
    llm_group.add_argument("--llm_service", help="LLM service class")
    llm_group.add_argument("--llm_base_url", help="Base URL for LLM API")
    llm_group.add_argument("--llm_model", help="Model name (覆盖默认 qwen3.5-plus)")
    llm_group.add_argument("--llm_api_key", help="API key (覆盖默认配置)")

    args = parser.parse_args()

    # 判断是否使用 LLM
    use_llm = args.use_llm or args.alibaba

    # Build LLM config
    if use_llm:
        # 默认使用阿里云配置
        llm_config = ALIBABA_CONFIG.copy()

        # 允许命令行参数覆盖
        if args.llm_service:
            llm_config["llm_service"] = args.llm_service
        if args.llm_base_url:
            llm_config["openai_base_url"] = args.llm_base_url
        if args.llm_model:
            llm_config["openai_model"] = args.llm_model
        if args.llm_api_key:
            llm_config["openai_api_key"] = args.llm_api_key
    else:
        llm_config = None

    try:
        output_file = convert_document(
            input_path=args.input,
            output_dir=args.output,
            use_llm=use_llm,
            output_format=args.format,
            page_range=args.page_range,
            force_ocr=args.force_ocr,
            llm_config=llm_config
        )
        print(f"✓ Conversion complete: {output_file}")
    except Exception as e:
        print(f"✗ Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
