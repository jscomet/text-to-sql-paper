# Marker 使用指南

## 快速开始

### 1. 基础转换（推荐用于格式良好的文档）

```bash
# Python 脚本方式
python src/convert_to_md.py docs/示例.pdf

# Windows 批处理方式
convert.bat docs/示例.pdf
```

### 2. LLM 增强转换（推荐用于复杂文档）

使用阿里云 **qwen3.5-plus** 模型，提高复杂表格、公式、跨页表格的识别准确性。

```bash
# Python 脚本方式
python src/convert_to_md.py docs/示例.pdf --use-llm

# Windows 批处理方式
convert.bat docs/示例.pdf --use-llm
```

### 3. 强制 OCR + LLM（适合扫描件）

```bash
python src/convert_to_md.py docs/扫描件.pdf --use-llm --force-ocr
```

### 4. 指定输出目录

```bash
python src/convert_to_md.py docs/示例.pdf -o ./output --use-llm
```

## 配置说明

阿里云 DashScope 配置已内置在脚本中：

| 配置项 | 值 |
|--------|-----|
| Base URL | `https://coding.dashscope.aliyuncs.com/v1` |
| 模型 | `qwen3.5-plus` |
| API Key | 已配置 |

## 支持格式

- PDF (`.pdf`)
- Word (`.docx`, `.doc`)
- PowerPoint (`.pptx`)
- Excel (`.xlsx`)
- EPUB (`.epub`)
- HTML (`.html`)

## 输出内容

- Markdown 文件（与输入文件同名，扩展名改为 `.md`）
- 自动提取的图片（保存在同目录）

## 两种模式对比

| 特性 | 基础模式 | LLM 增强模式 |
|------|----------|--------------|
| 速度 | ⚡ 快 | 🐢 较慢 |
| 准确性 | 良好 | 优秀 |
| 表格识别 | 标准 | 智能合并跨页表格 |
| 公式处理 | 基础 | LaTeX 格式化 |
| 适用场景 | 清晰文档 | 复杂/扫描文档 |

## 故障排除

### 1. 模型下载问题

首次运行需要下载 AI 模型（约 2-3GB）：

```bash
# 手动下载模型
python -c "from marker.models import create_model_dict; create_model_dict()"
```

### 2. 内存不足

如果转换大文件时出现内存错误：
- 减少并发 worker 数量
- 分割 PDF 后再转换

### 3. 中文乱码

确保文件编码为 UTF-8，输出文件已强制使用 UTF-8 编码。

## Python 代码中使用

```python
from src.convert_to_md import convert_basic, convert_with_llm

# 基础转换
convert_basic("input.pdf", "output_dir")

# LLM 增强转换
convert_with_llm("input.pdf", "output_dir", force_ocr=True)
```

## 参考

- [Marker GitHub](https://github.com/datalab-to/marker)
- [阿里云 DashScope](https://dashscope.aliyun.com/)
