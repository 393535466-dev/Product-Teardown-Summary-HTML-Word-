#!/usr/bin/env python3
"""Check a real DOCX/HTML pair and compare requirement/evidence identifiers (stdlib only)."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
from zipfile import ZipFile, BadZipFile

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
CT = '{http://schemas.openxmlformats.org/package/2006/content-types}'
DOC_MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'


class ReportHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.hidden = 0
        self.html = False
        self.body = False
        self.resources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.html |= tag == 'html'
        self.body |= tag == 'body'
        if tag in ('style', 'script', 'template'):
            self.hidden += 1
        if tag in ('img', 'script', 'source') and attrs.get('src'):
            self.resources.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet' and attrs.get('href'):
            self.resources.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag in ('style', 'script', 'template'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)


def docx_text(path):
    path = Path(path)
    if path.suffix.lower() != '.docx':
        raise ValueError('Word file must have a .docx extension')
    try:
        with ZipFile(path) as archive:
            if archive.testzip():
                raise ValueError('DOCX contains corrupt entries')
            relations = ET.fromstring(archive.read('_rels/.rels'))
            if not any(e.get('Type', '').endswith('/officeDocument')
                       and e.get('Target', '').lstrip('/') == 'word/document.xml'
                       and e.get('TargetMode') != 'External' for e in relations):
                raise ValueError('DOCX has no main document relationship')
            types = ET.fromstring(archive.read('[Content_Types].xml'))
            if not any(e.get('PartName') == '/word/document.xml' and e.get('ContentType') == DOC_MIME
                       for e in types.findall(CT + 'Override')):
                raise ValueError('DOCX is missing the Word document content type')
            xml = ET.fromstring(archive.read('word/document.xml'))
            body = xml.find(W + 'body')
            if body is None:
                raise ValueError('DOCX has no document body')
            text = ' '.join(e.text or '' for e in body.iter(W + 't'))
            if not text.strip():
                raise ValueError('DOCX has no editable body text')
            return text
    except (BadZipFile, KeyError, ET.ParseError) as exc:
        raise ValueError(f'Not a readable DOCX package: {exc}') from exc


def html_text(path):
    path = Path(path)
    if path.suffix.lower() not in ('.html', '.htm'):
        raise ValueError('HTML file must have an .html or .htm extension')
    parser = ReportHTML()
    parser.feed(path.read_text(encoding='utf-8'))
    if not parser.html or not parser.body or not ''.join(parser.text).strip():
        raise ValueError('HTML must be a full document with readable body content')
    for resource in parser.resources:
        parts = urlsplit(resource)
        if parts.scheme or parts.netloc or resource.startswith('#'):
            continue
        if not (path.parent / unquote(parts.path)).is_file():
            raise ValueError('Missing HTML resource: ' + resource)
    return ' '.join(parser.text)


def identifiers(text):
    return set(re.findall(r'\b(?:F|E|I|Q)\d+\b', text))


def check_pair(docx, html):
    word_text = docx_text(docx)
    web_text = html_text(html)
    word_ids, web_ids = identifiers(word_text), identifiers(web_text)
    if word_ids != web_ids:
        raise ValueError('Identifier mismatch; only in Word: ' + ', '.join(sorted(word_ids-web_ids))
                         + '; only in HTML: ' + ', '.join(sorted(web_ids-word_ids)))
    return len(word_ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('docx', type=Path)
    parser.add_argument('html', type=Path)
    args = parser.parse_args()
    try:
        count = check_pair(args.docx, args.html)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Deliverable check failed: {exc}\n')
    print(f'Both files are readable; {count} matching identifiers. Content and visual review still required.')


if __name__ == '__main__':
    main()
