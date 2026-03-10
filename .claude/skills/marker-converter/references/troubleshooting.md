# Troubleshooting Guide

## Installation Issues

### Model Download Fails

**Problem**: Initial model download times out or fails.

**Solution**:
```bash
# Pre-download models manually
python -c "from marker.models import create_model_dict; create_model_dict()"

# Or set HuggingFace cache directory
export HF_HOME=/path/to/large/disk
```

### CUDA/GPU Issues

**Problem**: CUDA out of memory or GPU not detected.

**Solution**:
```bash
# Force CPU usage
export TORCH_DEVICE=cpu

# Limit GPU memory
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Reduce workers
marker_single file.pdf --workers 1
```

## Conversion Issues

### Garbled Text

**Problem**: Output contains unreadable characters.

**Solution**:
```bash
# Force OCR on entire document
marker_single file.pdf --force_ocr

# Strip existing OCR and re-process
marker_single file.pdf --strip_existing_ocr
```

### Poor Table Formatting

**Problem**: Tables are not properly formatted or merged.

**Solution**:
```bash
# Use LLM for better table handling
marker_single file.pdf --use_llm

# For table-only extraction
marker_single file.pdf --converter_cls marker.converters.table.TableConverter --output_format json
```

### Missing Equations

**Problem**: Mathematical equations not converted properly.

**Solution**:
```bash
# Force OCR with inline math support
marker_single file.pdf --force_ocr --use_llm --redo_inline_math
```

## Performance Issues

### Slow Conversion

**Problem**: Conversion takes too long.

**Solutions**:
1. Use GPU if available
2. Process specific pages only: `--page_range "0-10"`
3. Disable image extraction: `--disable_image_extraction`
4. Use batch mode for multiple files

### High Memory Usage

**Problem**: Process killed or system freezes.

**Solutions**:
```bash
# Reduce concurrent workers
marker_single large.pdf --workers 1

# Process in chunks
marker_chunk_convert input_dir output_dir --num_devices 1 --num_workers 2
```

## LLM Issues

### API Errors

**Problem**: LLM service returns errors.

**Check**:
1. API key is valid and has credits
2. Base URL is correct (especially for Alibaba Cloud)
3. Model name is correct
4. Network can reach the API endpoint

### LLM Too Slow

**Problem**: LLM enhancement significantly slows conversion.

**Solutions**:
1. Use faster models (e.g., `gemini-2.0-flash`)
2. Only use LLM for problematic pages
3. Consider local Ollama deployment

## Output Issues

### Images Not Extracted

**Problem**: Images missing from output.

**Solutions**:
```bash
# Enable image extraction (default)
marker_single file.pdf  # images saved to output folder

# Check output directory permissions
ls -la output/
```

### JSON Output Too Large

**Problem**: JSON output consumes too much memory.

**Solution**:
```bash
# Use chunks format instead
marker_single file.pdf --output_format chunks

# Or stream output programmatically
```

## Debug Mode

Enable debug mode for detailed diagnostics:

```bash
marker_single file.pdf --debug
```

This creates:
- Page images with layout annotations
- Bounding box information
- Processing logs

## Getting Help

1. Check [Marker GitHub Issues](https://github.com/datalab-to/marker/issues)
2. Join [Discord community](https://discord.gg/KuZwXNGnfH)
3. Review benchmark datasets for expected accuracy
