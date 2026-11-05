---
name: pdf-chinese-web-reader
description: Convert academic PDFs into Chinese offline HTML reading pages with original PDF previews, faithful page-by-page Chinese translation, separate research commentary, and figure-by-figure explanation. Use for 中文论文精读网页、逐页翻译、原文对照、图表讲解、组会阅读。
---

# PDF Chinese Web Reader

**Goal:** Create a standalone `.html` Chinese paper reader. On wide screens every page uses **original PDF image | literal Chinese translation | independent interpretation**. Include left sticky navigation, pre-reading core summary, glossary, and detailed figure explanations. This is *not* an automatic translation engine; the agent reads the extracted PDF and authors faithful Chinese content before building.

## Install & requirements

Python 3.10+; `python -m pip install -r requirements.txt` (PyMuPDF). Always run scripts relative to the skill root or via absolute paths. Never assume a user's working directory.

## Workflow (mandatory)

1. **Inspect the original PDF** (all pages, formulas, captions, tables, appendices). Record whether text extraction appears reliable. For questionable regions visually inspect the rendered page. Do not invent missing text, formulas, or numerical findings.
2. **Prepare** rendered page previews and a draft JSON scaffold:

   ```bash
   python /path/to/pdf-chinese-web-reader/scripts/build_pdf_chinese_reader.py paper.pdf --extract-text --workdir work_reader
   ```

   This creates `work_reader/source_pages.json`, `work_reader/pages/`, and `work_reader/content_zh.json`. The JSON is a **draft with TODO fields**, not a finished translation.
3. **Read, translate, and interpret.** Fill every page's `translation` and `commentary` in `content_zh.json`. Keep Chinese translation strictly faithful to the source and in paragraph order, without AI comments inserted. Preserve equations, variables, units, bibliography numbers and abbreviations. Keep interpretation on the right. For references pages, summarise reference themes unless the user specifically asks for item-by-item translation. Use `source_pages.json` and the original PDF for verification.
4. **Figures:** Identify and explain every major figure (all relevant subpanels, labels, axes, trends and argumentative purpose). Put its caption translation and Chinese analysis in the `figures` list. Optional crop location: `page` (1-based) and `crop` = `[left, top, right, bottom]` in the **rendered page pixels**. Confirm each crop visually; omit `crop` if uncertain rather than guessing. For tables, explain model/sample/units/significance where relevant.
5. **Build** (rejects incomplete translations/commentary):

   ```bash
   python /path/to/pdf-chinese-web-reader/scripts/build_pdf_chinese_reader.py paper.pdf --content work_reader/content_zh.json --workdir work_reader --output paper_chinese_reading.html
   ```

   Images are embedded in base64; the HTML reads offline. `--allow-incomplete` is ONLY for local previews and MUST NOT be used for final delivery.
6. **Verify** the HTML visually: navigation, PDF image display, original–translation alignment, equation accuracy, right-side commentary, all intended crops and figure explanations, hover zoom on the **left** with `pointer-events:none`, and narrow screens. Do not add click-to-fullscreen.
7. Report the generated HTML, what is included, and limitations. Never claim full translation if some pages remain unprocessed.

## Document structure

- Compact reading-report header (paper title, source, badges).
- Left sticky TOC: core summary, terminology, figure index, all PDF pages.
- Pre-body summary, glossary, figure discussion in a comfortable single main reading column.
- Wide-screen page cards: left original screenshot, middle literal Chinese text, right research commentary/figure notes. Stack on narrow screens.
- Original page hover zoom floats **on the left**; mouse movement pans the zoom window. No fullscreen modal.

## Evidence and translation discipline

- Preserve source meaning and paragraph order; never silently omit pages. For text that extraction cannot recover, say so and rely on the screenshot.
- Do not turn correlation into causation, and do not invent regression coefficients, page numbers, or formulas.
- In research commentary distinguish author claims from reader's inferences; cite page/figure/table or equation numbers when relevant.
- Do not treat a rendered page as a substitute for reading its content.

Detailed schema: `references/content_schema.md`; usable starter: `examples/content_example.json`. Script: `scripts/build_pdf_chinese_reader.py`.
