#!/usr/bin/env python3
"""Tools for fischertechnik ROBO Pro Coding projects (.ft = ZIP). Standard library only.

  rpc.py inspect  FILE.ft            what controller, devices (python names + instance_name ids), blocks used, display elements
  rpc.py unpack   FILE.ft DIR        extract all entries
  rpc.py pack     DIR OUT.ft [--template T.ft]   zip a directory; entry order/names follow the template
  rpc.py validate FILE.ft            python/xml parse, device references, entry naming
  rpc.py extract-py FILE.ft          print the main program python
  rpc.py py2blockly PROG.py --template T.ft [--out OUT.ft] [--xml OUT.blockly]
                                     convert a python program (restricted subset, see references/blockly-xml.md)
                                     into Blockly XML using the template's controller devices; with --out also
                                     writes the .ft with matching .py + .blockly
  rpc.py build    PROG.py --template T.ft --out OUT.ft    same as py2blockly --out (alias)
Exit code 1 on errors. Nothing here talks to a controller or to ROBO Pro Coding.
"""
import argparse, ast, json, os, random, re, string, sys, zipfile
import xml.dom.minidom as md
import xml.etree.ElementTree as ET
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKMAP = os.path.join(HERE, '..', 'assets', 'block-map.json')


# ------------------------------------------------------------------ zip helpers
def read_ft(path):
    z = zipfile.ZipFile(path)
    return [(i.filename, z.read(i.filename)) for i in z.infolist()]


def write_ft(path, entries):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as zo:
        for name, data in entries:
            zo.writestr(name, data)


def main_names(entries):
    """(py entry, blockly entry) of the main program: top-level entries starting with '/'"""
    py = [n for n, _ in entries if n.startswith('/') and n.endswith('.py')]
    bl = [n for n, _ in entries if n.startswith('/') and n.endswith('.blockly')]
    return (py[0] if py else None), (bl[0] if bl else None)


def get(entries, name):
    for n, d in entries:
        if n == name:
            return d.decode('utf-8')
    return None


# ------------------------------------------------------------------ controller model
def parse_controller(entries):
    """returns dict(ctrl_id, ctrl_type, slots:[{group,index,port,block_type,block_id}], devices:[{var,type,port,instance_name}])"""
    bl = get(entries, 'lib/controller.blockly')
    py = get(entries, 'lib/controller.py') or ''
    info = {'ctrl_id': None, 'ctrl_type': None, 'controller_name': None, 'slots': [], 'devices': []}
    if bl:
        root = ET.fromstring(bl)
        ns = {'b': root.tag.split('}')[0].strip('{')} if root.tag.startswith('{') else {}
        q = lambda t: ('{%s}%s' % (ns['b'], t)) if ns else t
        top = next(root.iter(q('block')))
        info['ctrl_id'] = top.get('id'); info['ctrl_type'] = top.get('type')
        for f in top.findall(q('field')):
            if f.get('name') == 'controller_name':
                info['controller_name'] = f.text
        fields = {f.get('name'): f.text for f in top.findall(q('field'))}
        for v in top.findall(q('value')):
            name = v.get('name'); blk = v.find(q('block'))
            if blk is None:
                continue
            group, _, idx = name.rpartition('-')
            info['slots'].append({'group': group, 'index': idx, 'port': fields.get(name), 'block_type': blk.get('type'), 'block_id': blk.get('id')})
    vars_ = re.findall(r'^\s*(\w+)\s*=\s*\w+\.(\w+_factory)\.create_(\w+)\(\s*\w+\s*,\s*(\d+)\)', py, flags=re.M)
    for var, fac, typ, n in vars_:
        dev = {'var': var, 'factory': fac, 'type': typ, 'index': int(n), 'port': None, 'instance_name': None}
        for s in info['slots']:
            if s['port'] and var.endswith('_%s_%s' % (s['port'], s['block_type'])):
                dev['port'] = s['port']
                dev['instance_name'] = '%s-%s' % (info['ctrl_id'], s['block_id'])
        info['devices'].append(dev)
    return info


# ------------------------------------------------------------------ inspect / validate
def cmd_inspect(a):
    e = read_ft(a.file)
    out = {'entries': [n for n, _ in e]}
    pj = get(e, '.project.json')
    out['project'] = json.loads(pj) if pj else None
    c = parse_controller(e)
    out['controller_block'] = {'type': c['ctrl_type'], 'name': c['controller_name'], 'id': c['ctrl_id']}
    out['devices'] = c['devices']
    pyn, bln = main_names(e)
    out['main_py'], out['main_blockly'] = pyn, bln
    if bln:
        used = {}
        for m in re.finditer(r'<block type="([^"]+)"', get(e, bln)):
            used[m.group(1)] = used.get(m.group(1), 0) + 1
        out['blocks_used'] = used
    dx = get(e, 'lib/display.xml')
    if dx:
        root = ET.fromstring(dx)
        out['display'] = {'size': [root.get('width'), root.get('height')],
                          'elements': [{'class': i.get('class'), 'name': (i.find('name').text if i.find('name') is not None else None)} for i in root.findall('item')]}
    if get(e, 'lib/camera.xml'):
        out['camera'] = True
    if pyn:
        out['main_py_head'] = '\n'.join(get(e, pyn).split('\n')[:12])
    print(json.dumps(out, indent=2, ensure_ascii=False))


def validate_entries(e):
    errs, warns = [], []
    for n, d in e:
        if n.endswith('.py'):
            try: ast.parse(d.decode('utf-8'))
            except SyntaxError as x: errs.append('%s: python syntax error line %s: %s' % (n, x.lineno, x.msg))
        if n.endswith('.blockly') or n.endswith('.xml'):
            try: md.parseString(d)
            except Exception as x: errs.append('%s: XML error: %s' % (n, x))
    c = parse_controller(e)
    valid_inst = {d['instance_name'] for d in c['devices'] if d['instance_name']}
    pyn, bln = main_names(e)
    if not pyn or not bln:
        errs.append('main program entries (leading "/") missing: py=%s blockly=%s' % (pyn, bln))
    if bln:
        for m in re.finditer(r'<field name="instance_name">([^<]*)</field>', get(e, bln)):
            v = m.group(1).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            if v not in valid_inst and not re.fullmatch(r'[A-Z]\d', v):
                errs.append('%s: instance_name not in controller.blockly: %s' % (bln, v))
        ids = re.findall(r'<block [^>]*?id="([^"]+)"', get(e, bln))
        dup = {i for i in ids if ids.count(i) > 1}
        if dup: errs.append('%s: duplicate block ids: %s' % (bln, sorted(dup)[:5]))
    if pyn:
        src = get(e, pyn)
        names = {d['var'] for d in c['devices']}
        for m in set(re.findall(r'\b((?:RX|TXT_M)\w*?_(?:I|O|M|S|C|I2C|USB)\w*)\b', src)):
            if m not in names: errs.append('%s: unknown hardware name %s' % (pyn, m))
    return errs, warns


def cmd_validate(a):
    errs, warns = validate_entries(read_ft(a.file))
    for w in warns: print('WARN', w)
    for x in errs: print('ERROR', x)
    print('OK' if not errs else '%d error(s)' % len(errs))
    sys.exit(1 if errs else 0)


def cmd_unpack(a):
    for n, d in read_ft(a.file):
        p = os.path.join(a.dir, n.lstrip('/') if not n.startswith('/') else 'ROOT' + n)
        if n.endswith('/'):
            os.makedirs(p, exist_ok=True); continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(d)
    print('unpacked to', a.dir, '(entries starting with "/" go to ROOT/ so the leading slash survives packing)')


def cmd_pack(a):
    files = {}
    for root, _, fs in os.walk(a.dir):
        for f in fs:
            rel = os.path.relpath(os.path.join(root, f), a.dir).replace(os.sep, '/')
            name = rel[len('ROOT'):] if rel.startswith('ROOT/') else rel
            files[name] = open(os.path.join(root, f), 'rb').read()
    entries = []
    if a.template:
        for n, d in read_ft(a.template):
            entries.append((n, files.pop(n, d) if not n.endswith('/') else d))
    for n in sorted(files):
        entries.append((n, files[n]))
    write_ft(a.out, entries)
    print('wrote', a.out)


def cmd_extract(a):
    e = read_ft(a.file); pyn, _ = main_names(e)
    print(get(e, pyn))


# ------------------------------------------------------------------ python -> blockly (restricted subset)
class Unsupported(Exception):
    pass


class Conv:
    def __init__(self, ctrl, ctrl_kind):
        self.ctrl = ctrl; self.kind = ctrl_kind
        self.bm = json.load(open(BLOCKMAP))
        self.n = 0; self.vars = {}; self.errors = []; self.warnings = set(); self.procs = []
        self.dev = {}
        for d in ctrl['devices']:
            self.dev[d['var']] = d
        self.salt = ''.join(random.choice(string.ascii_letters) for _ in range(3))

    def bid(self):
        self.n += 1
        return 'g%s%05d' % (self.salt, self.n)

    def var(self, name):
        self.vars.setdefault(name, 'v_' + name)
        return self.vars[name]

    def err(self, node, msg):
        self.errors.append('line %s: %s' % (getattr(node, 'lineno', '?'), msg))
        raise Unsupported(msg)

    # --- hardware lookup
    def hw(self, node):
        """Attribute chain controller.X or X -> device"""
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'controller':
            name = node.attr
        elif isinstance(node, ast.Name):
            name = node.id
        else:
            return None
        return self.dev.get(name)

    def mapping(self, dev, method, kind):
        m = self.bm['devices'].get(dev['type'], {}).get(kind, {}).get(method)
        if not m:
            return None
        if self.kind not in self.bm['devices'][dev['type']]['verified']:
            self.warnings.add('block %s verified on %s only; check it loads on %s' % (m['block'], self.bm['devices'][dev['type']]['verified'], self.kind))
        return m

    # --- expressions
    def expr(self, e, name):
        return '<value name="%s">%s</value>' % (name, self.ex(e))

    def ex(self, e):
        if isinstance(e, ast.Constant):
            if isinstance(e.value, bool):
                return '<block type="logic_boolean" id="%s"><field name="BOOL">%s</field></block>' % (self.bid(), 'TRUE' if e.value else 'FALSE')
            if isinstance(e.value, (int, float)):
                return '<block type="math_number" id="%s"><field name="NUM">%s</field></block>' % (self.bid(), e.value)
            self.err(e, 'string constants are not supported')
        if isinstance(e, ast.Name):
            return '<block type="variables_get" id="%s"><field name="VAR" id="%s">%s</field></block>' % (self.bid(), self.var(e.id), e.id)
        if isinstance(e, ast.UnaryOp) and isinstance(e.op, ast.USub):
            return self.ex(ast.BinOp(left=ast.Constant(0), op=ast.Sub(), right=e.operand))
        if isinstance(e, ast.UnaryOp) and isinstance(e.op, ast.Not):
            return '<block type="logic_negate" id="%s">%s</block>' % (self.bid(), self.expr(e.operand, 'BOOL'))
        if isinstance(e, ast.BinOp):
            ops = {ast.Add: 'ADD', ast.Sub: 'MINUS', ast.Mult: 'MULTIPLY', ast.Div: 'DIVIDE', ast.Pow: 'POWER'}
            if isinstance(e.op, ast.Mod):
                return '<block type="math_modulo" id="%s">%s%s</block>' % (self.bid(), self.expr(e.left, 'DIVIDEND'), self.expr(e.right, 'DIVISOR'))
            if type(e.op) in ops:
                return '<block type="math_arithmetic" id="%s"><field name="OP">%s</field>%s%s</block>' % (self.bid(), ops[type(e.op)], self.expr(e.left, 'A'), self.expr(e.right, 'B'))
            self.err(e, 'operator %s not supported' % type(e.op).__name__)
        if isinstance(e, ast.Compare):
            if len(e.ops) != 1:
                self.err(e, 'chained comparisons not supported')
            ops = {ast.Eq: 'EQ', ast.NotEq: 'NEQ', ast.Lt: 'LT', ast.LtE: 'LTE', ast.Gt: 'GT', ast.GtE: 'GTE'}
            if type(e.ops[0]) not in ops:
                self.err(e, 'comparison %s not supported' % type(e.ops[0]).__name__)
            return '<block type="logic_compare" id="%s"><field name="OP">%s</field>%s%s</block>' % (self.bid(), ops[type(e.ops[0])], self.expr(e.left, 'A'), self.expr(e.comparators[0], 'B'))
        if isinstance(e, ast.BoolOp):
            op = 'AND' if isinstance(e.op, ast.And) else 'OR'
            acc = e.values[0]
            cur = self.ex(acc)
            for v in e.values[1:]:
                cur = '<block type="logic_operation" id="%s"><field name="OP">%s</field><value name="A">%s</value>%s</block>' % (self.bid(), op, cur, self.expr(v, 'B'))
            return cur
        if isinstance(e, ast.Call):
            if isinstance(e.func, ast.Name) and e.func.id in ('int', 'round') and len(e.args) == 1:
                return '<block type="math_round" id="%s"><field name="OP">ROUND</field>%s</block>' % (self.bid(), self.expr(e.args[0], 'NUM'))
            if isinstance(e.func, ast.Attribute):
                d = self.hw(e.func.value)
                if d:
                    m = self.mapping(d, e.func.attr, 'queries')
                    if not m:
                        self.err(e, 'no block mapping for %s.%s() on device type %s (add it to assets/block-map.json from a sample)' % (d['var'], e.func.attr, d['type']))
                    fl = ''.join('<field name="%s">%s</field>' % (k, v) for k, v in m['fields'].items())
                    return '<block type="%s" id="%s"><field name="instance_name">%s</field>%s</block>' % (m['block'], self.bid(), escape(d['instance_name']), fl)
        self.err(e, 'expression not supported: %s' % ast.dump(e)[:60])

    @staticmethod
    def drop_auto_sleep(body):
        """ROBO Pro Coding appends `await asyncio.sleep(0.01)` to every loop body by itself (seen in the RX sample:
        the python has 4 sleeps, the Blockly only 2 wait blocks). Dropping it from the Blockly keeps both in sync."""
        if body:
            l = body[-1]
            if (isinstance(l, ast.Expr) and isinstance(l.value, ast.Await) and isinstance(l.value.value, ast.Call)
                    and isinstance(l.value.value.func, ast.Attribute) and l.value.value.func.attr == 'sleep'
                    and l.value.value.args and isinstance(l.value.value.args[0], ast.Constant) and l.value.value.args[0].value == 0.01):
                return body[:-1]
        return body

    # --- statements
    def chain(self, stmts):
        blocks = []
        for s in stmts:
            try:
                blocks.extend(self.st(s))
            except Unsupported:
                pass
        out = ''
        for b in reversed(blocks):
            out = b.replace('@@NEXT@@', '<next>%s</next>' % out if out else '')
        return out

    def st(self, s):
        N = '@@NEXT@@'
        if isinstance(s, (ast.Pass, ast.Global, ast.Import, ast.ImportFrom)):
            return []
        if isinstance(s, ast.Break):
            return ['<block type="controls_flow_statements" id="%s"><field name="FLOW">BREAK</field>%s</block>' % (self.bid(), N)]
        if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
            t = s.targets[0].id
            return ['<block type="variables_set" id="%s"><field name="VAR" id="%s">%s</field>%s%s</block>' % (self.bid(), self.var(t), t, self.expr(s.value, 'VALUE'), N)]
        if isinstance(s, ast.AugAssign) and isinstance(s.target, ast.Name):
            return self.st(ast.Assign(targets=[s.target], value=ast.BinOp(left=ast.Name(id=s.target.id), op=s.op, right=s.value), lineno=s.lineno))
        if isinstance(s, ast.If):
            els = ''
            if s.orelse:
                els = '<statement name="ELSE">%s</statement>' % self.chain(s.orelse)
            mut = '<mutation else="1"></mutation>' if s.orelse else ''
            return ['<block type="controls_if" id="%s">%s%s<statement name="DO0">%s</statement>%s%s</block>' % (self.bid(), mut, self.expr(s.test, 'IF0'), self.chain(s.body), els, N)]
        if isinstance(s, ast.While):
            s = ast.While(test=s.test, body=self.drop_auto_sleep(s.body), orelse=[], lineno=s.lineno)
            if isinstance(s.test, ast.Constant) and s.test.value is True:
                return ['<block type="loop_endless" id="%s"><statement name="DO">%s</statement>%s</block>' % (self.bid(), self.chain(s.body), N)]
            return ['<block type="controls_whileUntil" id="%s"><field name="MODE">WHILE</field>%s<statement name="DO">%s</statement>%s</block>' % (self.bid(), self.expr(s.test, 'BOOL'), self.chain(s.body), N)]
        if isinstance(s, ast.For):
            c = s.iter
            if not (isinstance(s.target, ast.Name) and isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == 'range'):
                self.err(s, 'only "for i in range(...)" is supported')
            a = c.args
            lo, hi = (ast.Constant(0), ast.BinOp(left=a[0], op=ast.Sub(), right=ast.Constant(1))) if len(a) == 1 else (a[0], ast.BinOp(left=a[1], op=ast.Sub(), right=ast.Constant(1)))
            by = a[2] if len(a) == 3 else ast.Constant(1)
            return ['<block type="controls_for" id="%s"><field name="VAR" id="%s">%s</field>%s%s%s<statement name="DO">%s</statement>%s</block>' % (
                self.bid(), self.var(s.target.id), s.target.id, self.expr(lo, 'FROM'), self.expr(hi, 'TO'), self.expr(by, 'BY'), self.chain(s.body), N)]
        if isinstance(s, ast.FunctionDef):
            self.warnings.add('procedures_defnoreturn/callnoreturn were never confirmed to load in ROBO Pro Coding; keep a flat variant')
            if s.args.args:
                self.err(s, 'functions with parameters are not supported')
            self.procs.append('<block type="procedures_defnoreturn" id="%s" x="520" y="%d"><field name="NAME">%s</field><statement name="STACK">%s</statement></block>' % (self.bid(), 80 + 300 * len(self.procs), s.name, self.chain(s.body)))
            return []
        if isinstance(s, ast.Expr):
            v = s.value
            if isinstance(v, ast.Await):
                v = v.value
            if isinstance(v, ast.Call):
                f = v.func
                if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in ('asyncio', 'time') and f.attr == 'sleep':
                    g = self.bm['generic']['wait']
                    val = v.args[0]
                    if not isinstance(val, ast.Constant):
                        self.err(s, 'sleep() needs a numeric constant (the wait block has a number input)')
                    return ['<block type="util_wait_for" id="%s"><field name="format">s</field><value name="value"><shadow type="math_number" id="%s"><field name="NUM">%s</field></shadow></value>%s</block>' % (self.bid(), self.bid(), val.value, N)]
                if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == 'controller' and f.attr == 'init':
                    return []
                if isinstance(f, ast.Name) and f.id in self.procnames:
                    return ['<block type="procedures_callnoreturn" id="%s"><mutation name="%s"></mutation>%s</block>' % (self.bid(), f.id, N)]
                if isinstance(f, ast.Attribute):
                    d = self.hw(f.value)
                    if d:
                        m = self.mapping(d, f.attr, 'methods')
                        if not m:
                            self.err(s, 'no block mapping for %s.%s() on device type %s (add it to assets/block-map.json from a sample)' % (d['var'], f.attr, d['type']))
                        fl = ''.join('<field name="%s">%s</field>' % (k, x) for k, x in m.get('fields', {}).items())
                        val = ''
                        if 'value_input' in m:
                            arg = v.args[0]
                            if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == 'int':
                                arg = arg.args[0]
                            if isinstance(arg, ast.Constant):
                                val = '<value name="%s"><shadow type="%s" id="%s"><field name="%s">%s</field></shadow></value>' % (m['value_input'], m['shadow'], self.bid(), m['shadow_field'], arg.value)
                            else:
                                val = self.expr(arg, m['value_input'])
                        return ['<block type="%s" id="%s"><field name="instance_name">%s</field>%s%s%s</block>' % (m['block'], self.bid(), escape(d['instance_name']), fl, val, N)]
            self.err(s, 'call not supported: %s' % ast.dump(s.value)[:70])
        self.err(s, 'statement %s not supported' % type(s).__name__)


def convert_py(src, ctrl, kind):
    tree = ast.parse(src)
    cv = Conv(ctrl, kind)
    body = tree.body
    cv.procnames = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name != 'run'}
    run = next((n for n in body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'run'), None)
    top = [n for n in body if not isinstance(n, (ast.AsyncFunctionDef,))]
    main = (run.body if run else []) + []
    stmts = [n for n in top if not isinstance(n, (ast.Import, ast.ImportFrom))] if not run else [n for n in top if not isinstance(n, (ast.Import, ast.ImportFrom))]
    # constants/functions at module level first, then main body
    ordered = [s for s in stmts if isinstance(s, ast.FunctionDef)]
    rest = [s for s in stmts if not isinstance(s, ast.FunctionDef)]
    for f in ordered:
        try: cv.st(f)
        except Unsupported: pass
    start_body = cv.chain(rest + main)
    vs = ''.join('<variable id="%s">%s</variable>' % (v, k) for k, v in cv.vars.items())
    xml = ('<xml xmlns="https://developers.google.com/blockly/xml" version="23"><variables>%s</variables>'
           '<block type="start_block" id="start0" deletable="false" x="0" y="0"><statement name="statement">%s</statement></block>%s</xml>') % (vs, start_body, ''.join(cv.procs))
    md.parseString(xml)
    return xml, cv.errors, sorted(cv.warnings)


def cmd_py2blockly(a):
    e = read_ft(a.template)
    ctrl = parse_controller(e)
    kind = {'rx_controller': 'rx', 'txt4_controller': 'txt4'}.get(ctrl['ctrl_type'], ctrl['ctrl_type'])
    src = open(a.prog, encoding='utf-8').read()
    xml, errors, warns = convert_py(src, ctrl, kind)
    for w in warns: print('WARN', w)
    if errors:
        for x in errors: print('ERROR', x)
        print('Conversion incomplete: unsupported constructs were left out. Fix the program or add block mappings; do NOT ship this .ft.')
        sys.exit(1)
    if a.xml:
        open(a.xml, 'w', encoding='utf-8').write(xml)
    if a.out:
        pyn, bln = main_names(e)
        new = []
        for n, d in e:
            if n == pyn: d = src.encode('utf-8')
            elif n == bln: d = xml.encode('utf-8')
            new.append((n, d))
        errs, _ = validate_entries(new)
        write_ft(a.out, new)
        for x in errs: print('ERROR', x)
        print('wrote', a.out, '(validate: %s)' % ('OK' if not errs else 'FAILED'))
        sys.exit(1 if errs else 0)
    print('conversion OK')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    for n, f in (('inspect', cmd_inspect), ('validate', cmd_validate), ('extract-py', cmd_extract)):
        p = sp.add_parser(n); p.add_argument('file'); p.set_defaults(f=f)
    p = sp.add_parser('unpack'); p.add_argument('file'); p.add_argument('dir'); p.set_defaults(f=cmd_unpack)
    p = sp.add_parser('pack'); p.add_argument('dir'); p.add_argument('out'); p.add_argument('--template'); p.set_defaults(f=cmd_pack)
    for n in ('py2blockly', 'build'):
        p = sp.add_parser(n); p.add_argument('prog'); p.add_argument('--template', required=True); p.add_argument('--out'); p.add_argument('--xml'); p.set_defaults(f=cmd_py2blockly)
    a = ap.parse_args(); a.f(a)


if __name__ == '__main__':
    main()
