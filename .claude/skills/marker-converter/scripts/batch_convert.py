#!/usr/bin/env python3
"""
Batch convert documents to Markdown using Marker.

Usage:
    python batch_convert.py /path/to/input/dir /path/to/output/dir [options]
    python batch_convert.py ./documents ./output --use_llm --format markdown
"""

import os
import sys
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Windows 控制台 UTF-8 编码设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# =============================================================================
# 阿里云 DashScope 默认配置
# =============================================================================

ALIBABA_CONFIG = {
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_base_url": os.getenv("DASHSCOPE_BASE_URL", "https://coding.dashscope.aliyuncs.com/v1"),
    "openai_model": os.getenv("DASHSCOPE_MODEL", "qwen3.5-plus"),
    "openai_api_key": os.getenv("DASHSCOPE_API_KEY", "sk-sp-439b962366f7459db037434930cdeb7e"),
}

# Supported file extensions
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.epub', '.html'}


def convert_file(args):
    """Convert a single file."""
    input_file, output_dir, use_llm, output_format, llm_config = args

    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
        from marker.config.parser import ConfigParser

        # Build config
        config = {"output_format": output_format}
        if use_llm:
            config["use_llm"] = True
            if llm_config:
                config.update(llm_config)

        config_parser = ConfigParser(config)

        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service() if use_llm else None
        )

        rendered = converter(str(input_file))
        text, _, images = text_from_rendered(rendered)

        # Determine output path
        output_path = Path(output_dir) / f"{input_file.stem}.md"

        # Save Markdown
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return (input_file.name, True, str(output_path), None)

    except Exception as e:
        return (input_file.name, False, None, str(e))


def main():
    parser = argparse.ArgumentParser(
        description="Batch convert documents to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic batch conversion
  python batch_convert.py ./documents ./output

  # With LLM enhancement (默认使用阿里云 qwen3.5-plus)
  python batch_convert.py ./documents ./output --use_llm

  # 快速使用阿里云 LLM
  python batch_convert.py ./documents ./output --alibaba

  # JSON output format
  python batch_convert.py ./documents ./output --format json

  # 自定义阿里云模型
  python batch_convert.py ./documents ./output --alibaba --llm_model qwen3.5-max
        """
    )

    parser.add_argument("input_dir", help="Input directory containing documents")
    parser.add_argument("output_dir", help="Output directory for Markdown files")
    parser.add_argument("--use_llm", action="store_true", help="Enable LLM enhancement (默认使用阿里云)")
    parser.add_argument("--alibaba", action="store_true", help="使用阿里云 DashScope LLM (快捷方式)")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json", "html", "chunks"], help="Output format")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel workers (default: auto)")
    parser.add_argument("--recursive", action="store_true", help="Process subdirectories recursively")

    # LLM options
    llm_group = parser.add_argument_group("LLM Configuration")
    llm_group.add_argument("--llm_service", default=None, help="LLM service class")
    llm_group.add_argument("--llm_base_url", default=None, help="Base URL for LLM API")
    llm_group.add_argument("--llm_model", default=None, help="Model name (覆盖默认 qwen3.5-plus)")
    llm_group.add_argument("--llm_api_key", default=None, help="API key (覆盖默认配置)")

    args = parser.parse_args()

    # Validate directories
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)

    if not input_path.exists():
        print(f"Error: Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    # Collect files
    if args.recursive:
        files = [f for f in input_path.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS]
    else:
        files = [f for f in input_path.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not files:
        print(f"No supported files found in {args.input_dir}")
        print(f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
        sys.exit(1)

    print(f"Found {len(files)} file(s) to convert")

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
        llm_config = {}

    # Prepare tasks
    tasks = [(f, output_path, use_llm, args.format, llm_config) for f in files]

    # Process files
    success_count = 0
    fail_count = 0

    # Use single worker for LLM mode to avoid rate limits
    max_workers = 1 if use_llm else args.workers

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(convert_file, task): task for task in tasks}

        for future in as_completed(futures):
            filename, success, output_file, error = future.result()

            if success:
                print(f"✓ {filename} -> {output_file}")
                success_count += 1
            else:
                print(f"✗ {filename}: {error}")
                fail_count += 1

    print(f"\nConversion complete: {success_count} succeeded, {fail_count} failed")


if __name__ == "__main__":
    main()
