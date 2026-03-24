---
name: "markitdown"
displayName: "MarkItDown"
description: "Convert files and URLs to clean Markdown using MarkItDown. Supports PDF, DOCX, PPTX, XLSX, images, audio, HTML, and more."
keywords: ["markitdown", "convert to markdown", "convert file to markdown", "document to markdown", "extract to markdown", "converter para markdown", "converter arquivo para markdown", "documento para markdown", "extrair para markdown"]
author: "Bruno Lopes"
---

# MarkItDown Power

Convert virtually any document or URL into clean, structured Markdown. Powered by Microsoft's MarkItDown library.

## Onboarding

### Prerequisites
- Python 3.10+ with `uvx` installed
- MCP server `markitdown-mcp` configured (auto-installed from this power's mcp.json)

### Verification
After installation, the `mcp_convert_to_markdown` tool should be available. Test with any URL or local file.

## Supported Formats

| Category | Formats |
|----------|---------|
| Documents | PDF, DOCX, PPTX, XLSX, XLS |
| Web | HTML, URLs (http/https) |
| Images | JPG, PNG (with EXIF/OCR) |
| Audio | MP3, WAV (with speech-to-text) |
| Data | CSV, JSON, XML |
| Code | ZIP archives, Jupyter Notebooks (.ipynb) |
| Other | RSS feeds, EPUB |

## Common Workflows

### Convert a URL to Markdown
```
Use mcp_convert_to_markdown with uri: "https://example.com/page"
```

### Convert a Local File
```
Use mcp_convert_to_markdown with uri: "file:///path/to/your/report.pdf"
```

### Convert from Data URI
```
Use mcp_convert_to_markdown with uri: "data:text/html;base64,..."
```

### Batch Conversion Pattern
For multiple files, call `mcp_convert_to_markdown` sequentially for each URI. Combine results as needed.

## Tool Reference

### `mcp_convert_to_markdown`

**Purpose:** Convert a resource (URL, file, or data URI) to Markdown.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uri` | string | Yes | URI to convert. Supports `http:`, `https:`, `file:`, `data:` schemes |

**Returns:** Markdown text extracted from the source.

## Use Cases

- **Content ingestion:** Convert PDFs/DOCX into Markdown for processing
- **Web scraping:** Extract clean text from web pages
- **Document analysis:** Convert spreadsheets/presentations for review
- **Knowledge base building:** Transform existing docs into Markdown format
- **Research:** Extract content from papers, reports, slides

## Troubleshooting

### Error: "Unsupported format"
**Cause:** File type not supported by MarkItDown
**Solution:** Check supported formats table above. Convert to a supported format first.

### Error: "File not found"
**Cause:** Invalid file path in `file://` URI
**Solution:** Use absolute paths. Verify file exists: `ls -la /path/to/file`

### Empty or Poor Output
**Cause:** Scanned PDFs without OCR layer, or complex layouts
**Solution:** For scanned docs, ensure OCR dependencies are installed. For complex layouts, results may vary.

## Best Practices

- Use `file://` with absolute paths for local files
- For web pages, prefer direct URLs over saved HTML files
- Large files may take longer — PDFs with many pages are heavier
- Combine with Research Assistant power for full research workflows
- Output quality depends on source document structure

---

**Package:** `markitdown-mcp`
**MCP Server:** markitdown-mcp
