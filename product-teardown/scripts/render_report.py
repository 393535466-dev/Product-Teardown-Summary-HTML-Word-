#!/usr/bin/env python3
"""Wrap an agent-authored HTML body in the responsive report template (stdlib only)."""
import argparse
import html
from pathlib import Path
import re

TEMPLATE = Path(__file__).resolve().parent.parent / 'assets' / 'report-template.html'


def render_report(body, title, subtitle='', template=None):
    if not isinstance(body, str) or not body.strip():
        raise ValueError('body must be nonempty HTML')
    if not isinstance(title, str) or not title.strip():
        raise ValueError('title must be nonempty text')
    if not isinstance(subtitle, str):
        raise ValueError('subtitle must be text')
    # Body is deliberately flexible, agent-authored markup; this is not a sanitizer.
    # Source excerpts must be escaped before the agent inserts them into the body.
    if re.search(r'<\s*(?:html|head|body)\b|<!doctype\b', body, re.I):
        raise ValueError('body must be a fragment, not a full HTML document')
    source = TEMPLATE.read_text(encoding='utf-8') if template is None else template
    values = {'TITLE': html.escape(title), 'SUBTITLE': html.escape(subtitle), 'BODY': body}
    for key in values:
        if '{{' + key + '}}' not in source:
            raise ValueError('template is missing ' + key)
    # Single pass: content that happens to contain template tokens is not reinterpreted.
    return re.sub(r'\{\{(TITLE|SUBTITLE|BODY)\}\}', lambda m: values[m[1]], source)


def write_report(output, document, overwrite=False):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w' if overwrite else 'x', encoding='utf-8') as handle:
        handle.write(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('body', type=Path, help='Agent-authored UTF-8 HTML fragment')
    parser.add_argument('output', type=Path)
    parser.add_argument('--title', required=True)
    parser.add_argument('--subtitle', default='')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        document = render_report(args.body.read_text(encoding='utf-8'), args.title, args.subtitle)
        write_report(args.output, document, args.overwrite)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Cannot generate report: {exc}\n')
    print(f'Created {args.output.resolve()}')


if __name__ == '__main__':
    main()
