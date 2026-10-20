import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('report_renderer', ROOT / 'scripts/render_report.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class RendererTests(unittest.TestCase):
    def test_metadata_is_text_and_body_tokens_are_not_reprocessed(self):
        output = report.render_report('<section>{{TITLE}} remains literal</section>', '<script>x</script>', 'A & B')
        self.assertIn('&lt;script&gt;x&lt;/script&gt;', output)
        self.assertIn('A &amp; B', output)
        self.assertNotIn('<script>x</script>', output)
        self.assertIn('<section>{{TITLE}} remains literal</section>', output)

    def test_multiple_visual_forms_survive(self):
        body = '<nav><a href="#map">目录</a></nav><section id="map"><table><tr><th>确定项</th></tr></table><svg viewBox="0 0 20 20"><title>关系</title><circle cx="10" cy="10" r="5"/></svg><details><summary>证据</summary><p>未验证</p></details></section>'
        output = report.render_report(body, '虚构产品')
        self.assertIn(body, output)
        self.assertNotIn('<script src=', output)
        self.assertNotIn('<link ', output)

    def test_invalid_document_and_missing_template_markers_rejected(self):
        for body in ['', '  ', '<!doctype html><html><body>text</body></html>']:
            with self.assertRaises(ValueError):
                report.render_report(body, '产品')
        with self.assertRaises(ValueError):
            report.render_report('<p>ok</p>', '产品', template='{{TITLE}}{{BODY}}')

    def test_existing_report_is_preserved_without_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.html'
            report.write_report(output, 'original')
            with self.assertRaises(FileExistsError):
                report.write_report(output, 'replacement')
            self.assertEqual(output.read_text(), 'original')
            report.write_report(output, 'updated', overwrite=True)
            self.assertEqual(output.read_text(), 'updated')


if __name__ == '__main__':
    unittest.main()
