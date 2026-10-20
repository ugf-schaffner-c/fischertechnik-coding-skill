#!/usr/bin/env python3
"""Documentation finder ("refinder"): decides which docs are really needed for a task.

Usage:
  find_docs.py --controller txt4 --need "encoder motor, servo, display slider"
  find_docs.py --controller rx --need "ultrasonic" --max 3 --fetch     # also prints page text (needs internet)
  find_docs.py --list

Logic (keep context small):
  1. Always start from the user's sample .ft (assets/samples or the user's file): it is ground truth.
  2. Score each doc in assets/docs-index.json: topic keyword hits (x2 for exact phrase) + controller match.
  3. Drop everything below the threshold, cap at --max entries, prefer cheap docs when scores tie.
  4. Print URL + which local reference file covers the same topic, so the caller can read local first
     and fetch the URL only for detail or when the page may have changed.
"""
import argparse, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, '..', 'assets', 'docs-index.json')
LOCAL = {  # topic keyword -> local reference that already summarises it
    'display': 'references/display-ui.md', 'gui': 'references/display-ui.md', 'ui': 'references/display-ui.md',
    'servo': 'references/python-api.md', 'encoder': 'references/python-api.md', 'motor': 'references/python-api.md',
    'sensor': 'references/python-api.md', 'i2c': 'references/python-api.md', 'led': 'references/python-api.md',
    'valve': 'references/python-api.md', 'counter': 'references/python-api.md',
    'camera': 'references/file-format.md', 'blockly': 'references/blockly-xml.md', 'function': 'references/blockly-xml.md',
    'bt smart': 'references/controllers.md', 'controller': 'references/controllers.md',
    'pid': 'references/patterns.md', 'debounce': 'references/patterns.md', 'state machine': 'references/patterns.md',
}
CTRL_ALIASES = {'txt4': 'txt4', 'txt4.0': 'txt4', 'txt 4.0': 'txt4', 'rx': 'rx', 'bt': 'bt', 'btsmart': 'bt', 'bt smart': 'bt',
                'txt': 'txt-legacy', 'txt-legacy': 'txt-legacy'}


def load():
    with open(INDEX) as f:
        return json.load(f)['docs']


def terms(text):
    text = text.lower()
    parts = [p.strip() for p in re.split(r'[,;\n]+', text) if p.strip()]
    words = set(re.findall(r'[a-z0-9\.]+', text))
    return parts, words


def score(doc, ctrl, parts, words):
    s = 0.0
    for t in doc['topics']:
        if t in parts or any(t == p for p in parts):
            s += 3
        elif ' ' in t and t in ' '.join(parts):
            s += 3
        elif t in words:
            s += 2
    if ctrl:
        cs = doc['controllers']
        if ctrl in cs:
            s += 1.5
        elif 'all' in cs:
            s += 0.5
        elif s > 0:
            s -= 2   # topic match but wrong controller
    if doc['cost'] == 'large':
        s -= 3   # big docs only when clearly the best source
    return s


def fetch(url, limit=6000):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if url.lower().endswith('.pdf'):
            return '[PDF: use WebFetch or a PDF reader with a narrow question]'
        txt = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', data.decode('utf-8', 'replace'), flags=re.S)
        txt = re.sub(r'<[^>]+>', ' ', txt)
        return re.sub(r'\s+', ' ', txt)[:limit]
    except Exception as e:
        return '[fetch failed: %s. Use WebFetch/WebSearch, or the local reference]' % e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--controller', default='')
    ap.add_argument('--need', default='')
    ap.add_argument('--max', type=int, default=4)
    ap.add_argument('--min-score', type=float, default=2.5)
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    docs = load()
    if a.list:
        for d in docs:
            print('%-24s %-8s %s\n    %s' % (d['id'], d['cost'], d['title'], d['url']))
        return
    ctrl = CTRL_ALIASES.get(a.controller.lower().strip(), a.controller.lower().strip())
    parts, words = terms(a.need)
    ranked = sorted(((score(d, ctrl, parts, words), d) for d in docs),
                    key=lambda x: (-x[0], {'small': 0, 'medium': 1, 'large': 2}[x[1]['cost']]))
    picks = [(s, d) for s, d in ranked if s >= a.min_score][:a.max]
    print('# Read first: the user\'s sample .ft (python scripts/rpc.py inspect <file>) and assets/samples/ for TXT4/RX ground truth.')
    locals_ = sorted({LOCAL[k] for k in LOCAL if k in a.need.lower()})
    if locals_:
        print('# Local summaries covering the need: ' + ', '.join(locals_))
    if not picks:
        print('# No indexed doc scored high enough. Try WebSearch "site:doc.fischertechnik-cloud.com <topic>" or ask the user for a sample .ft containing the block.')
        return
    for s, d in picks:
        print('\n[%.1f] %s (%s, cost %s)\n  %s' % (s, d['title'], d['id'], d['cost'], d['url']))
        if d.get('note'):
            print('  note: ' + d['note'])
        if a.fetch and d['cost'] != 'large':
            print('  ---\n  ' + fetch(d['url']))


if __name__ == '__main__':
    main()
