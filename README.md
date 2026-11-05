# PDF Chinese Web Reader

An installable Agent Skill that transforms an academic PDF into an **offline Chinese HTML reader**: original page on the left, faithful Chinese translation in the middle, separate explanatory commentary on the right. It retains a sticky table of contents and detailed figure explanations.

> The PDF is a *specification*; this repository is the installable implementation. The Python helper renders/extracts/builds HTML. **The model/agent, not the Python script, performs the translation, evidence assessment, and figure interpretation.**

## Requirements
Python >=3.10, `pip install -r requirements.txt`.

## Install as a Skill

**Claude Code**: copy the `pdf-chinese-web-reader` folder into `~/.claude/skills/`.

**Codex**: copy into `~/.agents/skills/` (some older Codex installations use `~/.codex/skills/`). Restart/new session as needed.

For a repository on GitHub, users can run `npx skills add <your-github-username>/pdf-chinese-web-reader` in compatible agents, or install from the cloned directory if their CLI supports local paths. The repo has not been published by the author of this ZIP.

## Run manually

```bash
python scripts/build_pdf_chinese_reader.py path/to/paper.pdf --extract-text --workdir work_reader
# Agent fills work_reader/content_zh.json with faithful translations and commentary.
python scripts/build_pdf_chinese_reader.py path/to/paper.pdf --content work_reader/content_zh.json --workdir work_reader --output paper_chinese_reading.html
```

`--allow-incomplete` is ONLY for draft HTML preview; the final build rejects `TODO` and empty translation/commentary on any PDF page.

## Validate with a sample

```bash
python scripts/build_pdf_chinese_reader.py --help
python -m unittest discover -s tests -v
```

## Notes
- The report is self-contained with page previews embedded as data URIs; large PDF files may make large HTML outputs.
- Image crops use coordinates in extracted preview pixels. Use visual verification.
- Page source text is extracted from the PDF, which can be unreliable with scanned pages and mathematical expressions. Read the PDF images when extraction is unreliable.
- Only run the scripts on PDFs you are entitled to process, and inspect generated HTML before sharing.
