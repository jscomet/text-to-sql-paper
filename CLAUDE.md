# Project: paper

## 简介

工作论文项目

## 目录结构

```
.
├── .claude/              # Claude Code 配置
│   ├── memory/           # 记忆文件
│   └── skills/           # Claude Skills
│       └── marker-converter/  # 文档转换 Skill
├── src/                  # 源代码
├── docs/                 # 文档
└── CLAUDE.md             # 本项目文件
```

## 常用命令

### Marker 文档转换

阿里云配置已内置，可直接使用：

```bash
# 基础转换（本地快速转换，推荐用于 PDF）
python .claude/skills/marker-converter/scripts/convert_single.py docs/论文.pdf

# LLM 增强转换（使用阿里云 qwen3.5-plus）
python .claude/skills/marker-converter/scripts/convert_single.py docs/论文.pdf --alibaba

# 扫描件专用（OCR + LLM）
python .claude/skills/marker-converter/scripts/convert_single.py docs/扫描件.pdf --alibaba --force_ocr

# 批量转换
python .claude/skills/marker-converter/scripts/batch_convert.py ./input ./output --alibaba

# 切换模型（如使用 qwen3.5-max）
python .claude/skills/marker-converter/scripts/convert_single.py docs/论文.pdf --alibaba --llm_model qwen3.5-max

# 指定页码范围
python .claude/skills/marker-converter/scripts/convert_single.py docs/论文.pdf --page_range "0,5-10"
```

**环境变量配置（可选）**：
```bash
set DASHSCOPE_API_KEY=sk-xxx           # 覆盖默认 API Key
set DASHSCOPE_MODEL=qwen3.5-plus       # 覆盖默认模型
set DASHSCOPE_BASE_URL=xxx             # 覆盖默认 Endpoint
```

## 注意事项

### MCP MarkItDown 文档转换

**支持格式**: `.docx`, `.pdf`, `.pptx`, `.xlsx` 等（不支持旧版 `.doc`）

**URI 格式**: `file://localhost/workdir/<路径>`（基于 Docker 挂载）

**示例**:

```json
mcp__markitdown__convert_to_markdown
uri: file://localhost/workdir/docs/文件.docx
```

### MCP Open WebSearch 搜索建议

**中文搜索**: 优先使用 `csdn` 或 `baidu`

- CSDN 技术文章覆盖率高
- 百度适合中文内容和国内资源

**英文搜索**: 使用默认引擎（DuckDuckGo 等）

- 适合国际技术文档、论文、官方文档

**示例**:

```json
// 中文搜索
mcp__open-websearch__search
engines: ["baidu", "csdn"]
query: "PDF转Markdown工具"

// 英文搜索（使用默认引擎）
mcp__open-websearch__search
query: "best PDF to Markdown converter"
```
