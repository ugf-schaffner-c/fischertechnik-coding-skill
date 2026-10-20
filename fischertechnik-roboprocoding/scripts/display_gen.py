#!/usr/bin/env python3
"""Generate lib/display.xml + lib/display.qml for a TXT 4.0 project from a small JSON spec, using the exact
structure seen in assets/samples/txt4_sample.ft. Event handlers are NOT generated (their storage format is not
verified; see references/display-ui.md).

spec.json:
{"width":480,"height":460,"background":"grey","items":[
  {"class":"TXTLabel","name":"title","x":10,"y":10,"width":300,"height":40,"text":"Speed","fontSize":22},
  {"class":"TXTSlider","name":"speed","x":10,"y":60,"width":300,"height":40,"min":0,"max":512,"value":0},
  {"class":"TXTButton","name":"go","x":10,"y":110,"width":120,"height":50,"text":"Start"} ]}
classes: TXTButton TXTCheckBox TXTSwitch TXTSlider TXTLabel TXTInput StatusIndicator Gauge TXTImage

usage: display_gen.py spec.json --template in.ft --out out.ft      (replaces/adds lib/display.xml and lib/display.qml)
       display_gen.py spec.json --print                              (just print both files)
"""
import argparse, json, os, sys, uuid
from html import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc

ICON = 'assets/npx-robo-pro-coding/modules/display/ic_ft_rpc_controller_%s.svg'
ICONS = {'TXTButton': 'button', 'TXTCheckBox': 'checkbox_checked', 'TXTSwitch': 'switch_off', 'TXTSlider': 'slider', 'TXTLabel': 'label',
         'TXTInput': 'text', 'StatusIndicator': 'led', 'Gauge': 'scale', 'TXTImage': 'image'}
MIN = {'TXTButton': (32, 5), 'TXTCheckBox': (32, 20), 'TXTSwitch': (52, 20), 'TXTSlider': (40, 40), 'TXTLabel': (5, 5), 'TXTInput': (5, 5),
       'StatusIndicator': (5, 5), 'Gauge': (70, 70), 'TXTImage': (5, 5)}
DEF = {'TXTButton': dict(text='button', fontSize=22), 'TXTCheckBox': dict(text='check', fontSize=22, checked=False),
       'TXTSwitch': dict(text='switch', fontSize=22, checked=False), 'TXTSlider': dict(min=0, max=100, value=0),
       'TXTLabel': dict(text='label', fontSize=16, color='#ffffff', align='left'),
       'TXTInput': dict(text='', fontSize=22, color='#444444', align='left'),
       'StatusIndicator': dict(color='#ff0000', active=True), 'Gauge': dict(min=0, max=100, value=0), 'TXTImage': {}}


def b(v): return 'true' if v else 'false'


def gen(spec):
    W, H = spec.get('width', 480), spec.get('height', 460)
    xml = ['<xml width="%d" height="%d" type="display" version="3">' % (W, H)]
    qml = ['// auto generated content from display configuration', 'import QtQuick 2.2', 'import QtQuick.Window 2.0', 'import QtQuick.Controls 1.1',
           'import QtQuick.Controls.Styles 1.1', 'import QtQuick.Extras 1.4', '', 'TXTWindow {', '  Rectangle {', '    id: rect',
           '    color: "%s"' % spec.get('background', 'grey'), '    anchors.fill: parent', '  }']
    names = set()
    for it in spec['items']:
        c = it['class']
        assert c in ICONS, 'unknown class %s' % c
        assert it['name'] not in names, 'duplicate name %s' % it['name']
        names.add(it['name'])
        d = dict(DEF[c]); d.update(it)
        x, y, w, h = d['x'], d['y'], d['width'], d['height']
        mw, mh = MIN[c]
        head = '<item id="%s" class="%s"><icon>%s</icon><nodeType>%s</nodeType><x>%d</x><y>%d</y><width>%d</width><height>%d</height><minWidth>%d</minWidth><minHeight>%d</minHeight><name>%s</name>' % (
            uuid.uuid4(), c, ICON % ICONS[c], c, x, y, w, h, mw, mh, escape(d['name']))
        tail = '<geometry><x>%d</x><y>%d</y><width>%d</width><height>%d</height></geometry></item>' % (x, y, w, h)
        font = lambda: ['    font.pixelSize: %d' % d['fontSize'], '    font.bold: false', '    font.italic: false', '    font.underline: false']
        pos = ['    x: %d' % x, '    y: %d' % y, '    width: %d' % w, '    height: %d' % h]
        q = ['  %s {' % c, '    id: %s' % d['name']]
        if c in ('TXTButton', 'TXTCheckBox', 'TXTSwitch'):
            body = '<text>%s</text><fontSize>%d</fontSize><fontStyle/><enabled>%s</enabled>' % (escape(d['text']), d['fontSize'], b(d.get('enabled', True)))
            q += ['    text: "%s"' % d['text']] + font()
            if c != 'TXTButton':
                body += '<checked>%s</checked>' % b(d['checked'])
            if c == 'TXTSwitch':
                q += ['    enabled: %s' % b(d.get('enabled', True)), '    checked: %s' % b(d['checked'])]
            else:
                q += (['    checked: %s' % b(d['checked'])] if c == 'TXTCheckBox' else []) + ['    enabled: %s' % b(d.get('enabled', True))]
        elif c == 'TXTSlider':
            body = '<value>%s</value><minValue>%s</minValue><maxValue>%s</maxValue><orientation>Qt.Horizontal</orientation><enabled>%s</enabled>' % (d['value'], d['min'], d['max'], b(d.get('enabled', True)))
            q += ['    from: %s' % d['min'], '    value: %s' % d['value'], '    to: %s' % d['max'], '    orientation: Qt.Horizontal', '    enabled: %s' % b(d.get('enabled', True))]
        elif c in ('TXTLabel', 'TXTInput'):
            body = '<text>%s</text><textAlign>%s</textAlign><color>%s</color><fontSize>%d</fontSize><fontStyle/>' % (escape(d['text']), d['align'], d['color'], d['fontSize'])
            al = 'Text.Align' + d['align'].capitalize()
            q += ['    text: "%s"' % d['text']] + font()
            if c == 'TXTLabel':
                q += ['    verticalAlignment: Text.AlignVCenter']
            q += ['    horizontalAlignment: %s' % al, '    color: "%s"' % d['color'], '    elide: Text.ElideRight']
        elif c == 'StatusIndicator':
            body = '<color>%s</color><active>%s</active>' % (d['color'], b(d['active']))
            q += ['    color: "%s"' % d['color'], '    active: %s' % b(d['active'])]
        elif c == 'Gauge':
            body = '<value>%s</value><minValue>%s</minValue><maxValue>%s</maxValue><orientation>Qt.Horizontal</orientation><tickmarkStepSize>10</tickmarkStepSize><minorTickmarkCount>4</minorTickmarkCount>' % (d['value'], d['min'], d['max'])
            q += ['    minimumValue: %s' % d['min'], '    value: %s' % d['value'], '    maximumValue: %s' % d['max'], '    orientation: Qt.Horizontal',
                  '    tickmarkStepSize: 10', '    minorTickmarkCount: 4', '    formatValue: function(value) {', '      return value.toFixed(1);', '    }']
        else:  # TXTImage (sample: generated as an empty TXTLabel)
            body = '<image/>'
            q = ['  TXTLabel {', '    id: %s' % d['name'], '    text: ""']
        xml.append(head + body + tail)
        qml += q + pos + ['  }']
    xml.append('</xml>')
    qml.append('}')
    return ''.join(xml), '\n'.join(qml) + '\n'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--template'); ap.add_argument('--out'); ap.add_argument('--print', action='store_true')
    a = ap.parse_args()
    x, q = gen(json.load(open(a.spec)))
    if a.print or not a.out:
        print(x); print(q); return
    e = rpc.read_ft(a.template)
    names = {n for n, _ in e}
    new = []
    for n, d in e:
        new.append((n, x.encode() if n == 'lib/display.xml' else q.encode() if n == 'lib/display.qml' else d))
    for n, d in (('lib/display.xml', x), ('lib/display.qml', q)):
        if n not in names:
            # insert after lib/controller.py if possible
            idx = max([i for i, (m, _) in enumerate(new) if m.startswith('lib/')] or [0]) + 1
            new.insert(idx, (n, d.encode()))
    errs, _ = rpc.validate_entries(new)
    rpc.write_ft(a.out, new)
    print('wrote', a.out, 'validate:', 'OK' if not errs else errs)


if __name__ == '__main__':
    main()
