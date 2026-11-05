# `content_zh.json` structure

All text fields use plain text (literal `<`, `&` are HTML-escaped). Newline separation is supported. Do not use raw HTML. `translation` and `commentary` are **separate** to prevent an interpretation being mistaken for a literal translation.

```json
{
  "title": "Article title",
  "source": "journal / URL / DOI",
  "summary": "中文核心摘要（请核对原文）",
  "terms": [{"term":"DID","meaning":"双重差分方法……"}],
  "figures": [{"label":"Fig. 1","page":1,"caption_zh":"原文图注忠实翻译","explanation":"说明每个子图、坐标轴、趋势、支持的主张和边界","crop":[100,150,700,650]}],
  "pages": [
    {"page":1,"translation":"完整、按原文段落排列的中文翻译", "commentary":"单独的研究性说明、图表讲解与讨论"}
  ]
}
```

`page` uses 1-based PDF numbering. `crop` is optional, and crop coordinates are measured against the preview page image (`work_reader/pages/page_0001.jpg`), **not PDF points**. Omit crop to display the entire page in the global figure gallery. If the PDF contains references, translate or explain according to the user's request; the default skill allows summarizing threads. All PDF pages MUST have a matching object and non-placeholder translation/commentary. The build script validates this.
