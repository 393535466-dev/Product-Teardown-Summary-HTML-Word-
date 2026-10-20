import importlib.util
from pathlib import Path
import tempfile
import unittest
from xml.sax.saxutils import escape
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('deliverable_checker', ROOT / 'scripts/check_deliverables.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def docx_fixture(path, text):
    # Minimal OOXML test fixture; not a user-facing report or a layout test.
    with ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="' + checker.DOC_MIME + '"/></Types>')
        z.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + escape(text) + '</w:t></w:r></w:p></w:body></w:document>')


class PairTests(unittest.TestCase):
    def test_folded_evidence_is_counted_and_style_is_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            docx, web = Path(d)/'report.docx', Path(d)/'report.html'
            docx_fixture(docx, 'F01 要求 E01 证据 Q02 待确认')
            web.write_text('<html><head><style>F999</style></head><body><p>F01 要求</p><details><summary>证据</summary><p>E01 证据 Q02 待确认</p></details></body></html>')
            self.assertEqual(checker.check_pair(docx, web), 3)

    def test_missing_word_evidence_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            docx, web = Path(d)/'report.docx', Path(d)/'report.html'
            docx_fixture(docx, 'F01')
            web.write_text('<html><body>F01 E02</body></html>')
            with self.assertRaisesRegex(ValueError, 'only in HTML: E02'):
                checker.check_pair(docx, web)

    def test_renamed_html_is_not_a_word_document(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'fake.docx'; path.write_text('<html><body>text</body></html>')
            with self.assertRaisesRegex(ValueError, 'Not a readable DOCX'):
                checker.docx_text(path)

    def test_missing_local_image_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'report.html';path.write_text('<html><body>text<img src="assets/missing.png"></body></html>')
            with self.assertRaisesRegex(ValueError, 'Missing HTML resource'):
                checker.html_text(path)

    def test_empty_docx_text_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'empty.docx';docx_fixture(path, '')
            with self.assertRaisesRegex(ValueError, 'editable body text'):
                checker.docx_text(path)


if __name__ == '__main__':
    unittest.main()
