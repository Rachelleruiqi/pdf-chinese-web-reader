import importlib.util
from pathlib import Path
import tempfile
import unittest
import fitz

SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'build_pdf_chinese_reader.py'
spec=importlib.util.spec_from_file_location('reader',SCRIPT)
reader=importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)

class BuilderTest(unittest.TestCase):
    def test_prepare_build_and_validation(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); pdf=d/'a.pdf'; work=d/'work'
            x=fitz.open(); p=x.new_page(); p.insert_text((72,90),'Test article and formula'); x.save(str(pdf)); x.close()
            meta=reader.prepare(pdf,work,85)
            import json
            c=json.loads((work/'content_zh.json').read_text())
            with self.assertRaises(ValueError): reader.validate(c,meta,False)
            c['pages'][0]['translation']='这是对示例原文的中文翻译。'
            c['pages'][0]['commentary']='这是单独的研究性解释。'
            c['summary']='文章概要。'
            self.assertEqual(reader.validate(c,meta,False),[])
            outfile=d/'out.html';reader.render(c,meta,work,outfile,[])
            output=outfile.read_text()
            self.assertIn('这是对示例原文的中文翻译',output)
            self.assertIn('page-image',output)
            self.assertIn('pointer-events:none',output)
            self.assertIn('data:image/jpeg;base64,',output)

if __name__=='__main__':unittest.main()
