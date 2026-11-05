#!/usr/bin/env python3
"""Prepare PDF assets and render a self-contained, three-column Chinese reading HTML."""
import argparse
import base64
import html
import json
from pathlib import Path
import re
import sys

try:
    import fitz
except ImportError:
    sys.exit('PyMuPDF is required: python -m pip install "PyMuPDF>=1.24,<2"')


def safe(s):
    return html.escape(str(s or ''), quote=True)


def paras(s):
    return ''.join('<p>' + safe(part).replace('\n', '<br>') + '</p>' for part in re.split(r'\n\s*\n', (s or '').strip()) if part.strip())


def prepare(pdf, workdir, dpi):
    doc = fitz.open(pdf)
    pagesdir = workdir / 'pages'
    pagesdir.mkdir(parents=True, exist_ok=True)
    meta = []
    for n, page in enumerate(doc, 1):
        img = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
        file = pagesdir / f'page_{n:04d}.jpg'
        img.save(str(file), jpg_quality=78)
        txt = page.get_text('text', sort=True)
        meta.append({'page':n,'image':str(file.relative_to(workdir)),'width':img.width,'height':img.height,'extracted_text':txt,'text_characters':len(txt.strip()),'text_may_be_incomplete':len(txt.strip())<40})
    (workdir/'source_pages.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    content = workdir/'content_zh.json'
    if not content.exists():
        scaffold={'title':doc.metadata.get('title') or pdf.stem,'source':pdf.name,'summary':'TODO: 中文核心摘要', 'terms':[], 'figures':[], 'pages':[{'page':x['page'],'translation':'TODO: 逐段忠实翻译第 '+str(x['page'])+' 页','commentary':'TODO: 解释第 '+str(x['page'])+' 页的逻辑与关键证据'} for x in meta]}
        content.write_text(json.dumps(scaffold,ensure_ascii=False,indent=2),encoding='utf-8')
    return meta


def daturi(data, mime='image/jpeg'):
    return f'data:{mime};base64,' + base64.b64encode(data).decode('ascii')


def validate(content, meta, allow_incomplete):
    errors=[]
    pages=content.get('pages',[])
    ids=[x.get('page') for x in pages]
    if sorted(ids)!=list(range(1,len(meta)+1)):
        errors.append('pages must contain exactly one entry for every PDF page, numbered from 1')
    for x in pages:
        for key in ('translation','commentary'):
            val=x.get(key,'')
            if not isinstance(val,str) or not val.strip() or 'TODO' in val or '请使用实际 PDF 内容逐段翻译' in val:
                errors.append(f'page {x.get("page")}: incomplete {key}')
    for idx,fig in enumerate(content.get('figures',[]),1):
        p=fig.get('page')
        if not isinstance(p,int) or not 1<=p<=len(meta):
            errors.append(f'figure {idx}: invalid page')
        crop=fig.get('crop')
        if crop is not None:
            if not isinstance(crop,list) or len(crop)!=4 or not all(isinstance(v,(int,float)) for v in crop):
                errors.append(f'figure {idx}: crop must have four pixel coordinates')
            elif isinstance(p,int) and 1<=p<=len(meta):
                l,t,r,b=crop
                if not (0<=l<r<=meta[p-1]['width'] and 0<=t<b<=meta[p-1]['height']):
                    errors.append(f'figure {idx}: crop outside page image bounds')
    if errors and not allow_incomplete:
        raise ValueError('Content validation failed:\n - '+'\n - '.join(errors))
    return errors


def figure_image(fig,meta,workdir):
    n=fig['page']
    path=workdir/meta[n-1]['image']
    if 'crop' in fig:
        pix=fitz.Pixmap(str(path))
        l,t,r,b=map(int,fig['crop'])
        region=fitz.Pixmap(pix, fitz.IRect(l,t,r,b))
        return daturi(region.tobytes('png'),'image/png')
    return daturi(path.read_bytes())


def render(content,meta,workdir,output,notices):
    entries={v['page']:v for v in content.get('pages',[])}
    n=len(meta)
    toc=''.join(f'<a href="#page-{i}">第 {i} 页</a>' for i in range(1,n+1))
    nav='<a href="#summary">核心摘要</a><a href="#terms">术语表</a><a href="#figures">图表说明</a>'+toc
    glossary=''.join('<tr><th>'+safe(x.get('term'))+'</th><td>'+paras(x.get('meaning',''))+'</td></tr>' for x in content.get('terms',[]))
    visuals=[]
    for i,f in enumerate(content.get('figures',[]),1):
        src=figure_image(f,meta,workdir)
        visuals.append(f'<article class="figure-card"><h3>{safe(f.get("label",f"图表 {i}"))} · 第 {f["page"]} 页</h3><img loading="lazy" src="{src}" alt="Figure from original PDF"><div><strong>图注</strong>{paras(f.get("caption_zh"))}<strong>分析</strong>{paras(f.get("explanation"))}</div></article>')
    cards=[]
    for src in meta:
        i=src['page']; entry=entries.get(i,{})
        data=daturi((workdir/src['image']).read_bytes())
        cards.append(f'''<section class="page-card" id="page-{i}"><h2>第 {i} / {n} 页</h2><div class="page-grid">
<div class="panel original"><h3>原始 PDF · 第 {i} 页</h3><div class="page-image-wrap" tabindex="0"><img class="page-image" loading="lazy" alt="原始 PDF 第 {i} 页" src="{data}"><div class="zoom-pane" aria-hidden="true"></div></div></div>
<div class="panel"><h3>忠实中文翻译</h3><div class="body-text">{paras(entry.get('translation',''))}</div></div>
<div class="panel"><h3>精读讲解与思考</h3><div class="body-text">{paras(entry.get('commentary',''))}</div></div>
</div></section>''')
    css='''
:root{font-family:-apple-system,BlinkMacSystemFont,"Noto Sans SC","Microsoft Yahei",sans-serif;color:#1d2936;background:#f5f7fa}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0}a{color:#255989;text-decoration:none}a:hover{text-decoration:underline}
.header{background:#fff;border-bottom:1px solid #e3e8ed;padding:28px 38px}.header h1{margin:0 0 12px;font-size:clamp(23px,2.5vw,34px)}.header small{color:#66768b}.label{display:inline-block;background:#eaf3f8;color:#255989;border-radius:20px;padding:5px 10px;margin:10px 5px 0 0;font-size:12px}
.layout{display:grid;grid-template-columns:205px minmax(0,1fr);gap:24px;max-width:1850px;margin:0 auto;padding:22px}.sidebar{position:sticky;top:10px;align-self:start;max-height:calc(100vh - 20px);overflow:auto;padding:17px;background:#fff;border-radius:12px;border:1px solid #e3e8ed}.sidebar strong{display:block;margin-bottom:13px}.sidebar a{display:block;padding:8px 4px;border-bottom:1px solid #f0f1f3;font-size:13px}.main{min-width:0}.intro{max-width:1020px}.intro,.page-card{background:white;border:1px solid #e4e9ee;border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 2px 12px #20334a08}.intro h2,.page-card h2{font-size:20px;margin:0 0 16px}.intro p,.panel p{line-height:1.85;white-space:pre-wrap}.terms{border-collapse:collapse;width:100%}.terms th,.terms td{border-bottom:1px solid #e2e5eb;padding:9px 12px;text-align:left;vertical-align:top}.terms th{width:23%}.figure-card{border-top:1px solid #e2e5eb;padding:16px 0}.figure-card img{max-width:95%;max-height:550px;object-fit:contain;display:block;margin:12px auto;border:1px solid #eee}.figure-card strong{display:block;margin-top:8px}.page-grid{display:grid;grid-template-columns:minmax(260px,1fr) minmax(280px,1fr) minmax(280px,1fr);gap:16px;align-items:start}.panel{min-width:0;background:#f9fbfc;border:1px solid #e8edf1;border-radius:10px;padding:15px}.panel h3{font-size:15px;margin:0 0 12px}.page-image-wrap{position:relative;cursor:crosshair;max-width:100%}.page-image{display:block;max-width:100%;height:auto;margin:auto;box-shadow:0 1px 6px #0002}.zoom-pane{display:none;position:absolute;pointer-events:none;width:min(420px,88vw);height:330px;z-index:30;right:calc(100% + 12px);top:0;border:1px solid #b3c9d9;background-color:white;background-size:250% auto;background-repeat:no-repeat;box-shadow:0 7px 24px #152c4650}.page-image-wrap:hover .zoom-pane,.page-image-wrap:focus .zoom-pane{display:block}.body-text{font-size:14px;overflow-wrap:anywhere}.warning{background:#fff6e4;padding:13px;border-left:3px solid #b7791f}
@media(max-width:1250px){.zoom-pane{right:auto;left:0;top:100%}}@media(max-width:1080px){.page-grid{grid-template-columns:1fr}.original{max-width:620px}.layout{grid-template-columns:175px minmax(0,1fr)}}@media(max-width:690px){.layout{display:block;padding:11px}.sidebar{position:static;max-height:180px;margin-bottom:14px}.header{padding:20px}.intro,.page-card{padding:15px}.zoom-pane{width:270px;height:230px}}
'''
    js='''document.querySelectorAll('.page-image-wrap').forEach(w=>{const img=w.querySelector('.page-image');const pane=w.querySelector('.zoom-pane');pane.style.backgroundImage=`url("${img.src}")`;w.addEventListener('mousemove',e=>{let r=img.getBoundingClientRect();let x=Math.max(0,Math.min(1,(e.clientX-r.left)/r.width));let y=Math.max(0,Math.min(1,(e.clientY-r.top)/r.height));pane.style.backgroundPosition=`${x*100}% ${y*100}%`;});});'''
    warning=f'<div class="warning">草稿预览：{len(notices)} 项未完成或需核实。此文件不可作为完整精读交付。</div>' if notices else ''
    document='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+safe(content.get('title'))+' — 中文精读</title><style>'+css+'</style></head><body>'
    document+='<header class="header"><h1>'+safe(content.get('title'))+'</h1><small>'+safe(content.get('source'))+'</small><div><span class="label">原文对照</span><span class="label">忠实翻译</span><span class="label">研究讲解</span><span class="label">离线 HTML</span></div></header>'
    document+='<div class="layout"><nav class="sidebar"><strong>阅读目录</strong>'+nav+'</nav><main class="main">'+warning
    document+='<section class="intro" id="summary"><h2>核心摘要</h2>'+paras(content.get('summary'))+'</section>'
    document+='<section class="intro" id="terms"><h2>关键术语</h2><table class="terms">'+glossary+'</table></section>'
    document+='<section class="intro" id="figures"><h2>图表逐项说明</h2>'+(''.join(visuals) if visuals else '<p>暂无单独图表说明。请结合原文确认是否需要补充。</p>')+'</section>'
    document+=''.join(cards)+'</main></div><script>'+js+'</script></body></html>'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(document,encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pdf',type=Path)
    ap.add_argument('--extract-text',action='store_true',help='Render pages and prepare source_pages.json and editable content_zh.json')
    ap.add_argument('--workdir',type=Path,default=Path('work_reader'))
    ap.add_argument('--content',type=Path,help='Completed content_zh.json to render')
    ap.add_argument('--output',type=Path,help='Offline HTML output')
    ap.add_argument('--dpi',type=int,default=115)
    ap.add_argument('--allow-incomplete',action='store_true',help='Draft previews only; not permitted for final delivery')
    a=ap.parse_args()
    if not a.pdf.is_file(): ap.error(f'Input PDF not found: {a.pdf}')
    if not (a.extract_text or a.content): ap.error('Choose --extract-text or --content FILE')
    a.workdir.mkdir(parents=True,exist_ok=True)
    if a.extract_text or not (a.workdir/'source_pages.json').exists():
        meta=prepare(a.pdf,a.workdir,a.dpi)
    else:
        meta=json.loads((a.workdir/'source_pages.json').read_text(encoding='utf-8'))
        if not all((a.workdir/p['image']).exists() for p in meta): meta=prepare(a.pdf,a.workdir,a.dpi)
    print(f'Prepared {len(meta)} pages in {a.workdir}')
    if a.content:
        content=json.loads(a.content.read_text(encoding='utf-8'))
        notices=validate(content,meta,a.allow_incomplete)
        outfile=a.output or a.pdf.with_name(a.pdf.stem+'_chinese_reading.html')
        render(content,meta,a.workdir,outfile,notices)
        print(f'Generated {outfile} ({outfile.stat().st_size:,} bytes)')
        if notices: print('INCOMPLETE DRAFT:\n- '+'\n- '.join(notices))

if __name__=='__main__': main()
