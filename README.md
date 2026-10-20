# fischertechnik Coding Skill

Skill für KI-Assistenten (Claude, Claude Code, andere), der **ROBO Pro Coding**-Programme für fischertechnik-Controller schreibt, umwandelt, prüft und verpackt:
**RX Controller**, **TXT 4.0** (inkl. Display-UI) und **BT Smart** (benötigt ein Beispielprojekt).
Ausgabe wahlweise **Python (`.py`)** oder **Blockly (`.ft`-Projekt)**, spätere Umwandlung möglich.

*English:* A skill that lets an AI assistant write, convert, validate and package ROBO Pro Coding programs (Blockly or Python) for fischertechnik RX, TXT 4.0 and BT Smart controllers. Output is a `.ft` project or a `.py` file.

## Inhalt
| Pfad | Zweck |
|---|---|
| `fischertechnik-roboprocoding/SKILL.md` | Arbeitsablauf (Format-Wahl, Beispieldatei oder Fragerunde, Doku-Finder, Bauen, Prüfen) |
| `fischertechnik-roboprocoding/scripts/rpc.py` | `.ft` inspizieren, entpacken, packen, validieren; Python nach Blockly umwandeln |
| `fischertechnik-roboprocoding/scripts/find_docs.py` | Doku-Finder: wählt nur die nötigen Dokumente (Live-Links) |
| `fischertechnik-roboprocoding/scripts/display_gen.py` | TXT-4.0-Display (`display.xml`/`display.qml`) aus JSON |
| `fischertechnik-roboprocoding/assets/` | Doku-Register (`docs-index.json`), Block-Zuordnung, echte Beispielprojekte (RX, TXT 4.0) |
| `fischertechnik-roboprocoding/references/` | Dateiformat, Python-API, Blockly-XML, Display, Controller, Muster |
| `blockbrain/` | Variante für Plattformen ohne Skript-Ausführung (siehe unten) |

## Nutzung
**Claude Code / Claude:** Ordner `fischertechnik-roboprocoding/` nach `~/.claude/skills/` (oder Projekt `.claude/skills/`) kopieren, oder die Datei `fischertechnik-roboprocoding.skill` aus den Releases installieren. Dann z. B.: *„Schreibe ein ROBO-Pro-Coding-Programm für meinen TXT 4.0 …"*. Python 3 genügt, keine Abhängigkeiten.

**Skripte direkt:**
```bash
python fischertechnik-roboprocoding/scripts/rpc.py inspect projekt.ft
python fischertechnik-roboprocoding/scripts/rpc.py build programm.py --template projekt.ft --out neu.ft
python fischertechnik-roboprocoding/scripts/rpc.py validate neu.ft
python fischertechnik-roboprocoding/scripts/find_docs.py --controller txt4 --need "servo, display slider"
```

**Blockbrain & ähnliche Plattformen:** Skills dort sind Textbausteine (Anweisung, Handle `/name`), keine Ordner mit Skripten. Siehe `blockbrain/README.md`.

## Status und Grenzen (ehrlich)
- Getestet nur per Simulation und gegen zwei echte Beispieldateien (RX, TXT 4.0); Laden in ROBO Pro Coding und Lauf auf dem Controller sind **nicht** automatisiert getestet.
- Verifiziert: RX-Blöcke (Ventil, Kompressor, LED, Motor, Taster, Warten, Schleifen, If), TXT-4.0-Dateiaufbau, Controller-Konfiguration, Display-Dateien.
- Nicht verifiziert: BT Smart, Blöcke für Encoder-Motor/Servo/Zähler, Display-Event-Handler, Blockly-Funktionsblöcke. Der Skill verlangt dafür ein Beispiel-`.ft`, statt Blocknamen zu raten. Neue Zuordnungen in `assets/block-map.json` eintragen (Pull Requests willkommen).
- Dokumentation wird per Live-Link geholt; lokale Referenzen sind eine datierte Zusammenfassung.
- Inoffiziell, nicht von fischertechnik. Beispielprojekte sind eigene Testprojekte.

## Beitragen
Beispieldateien (`.ft`) mit neuen Blöcken/Controllern sind der wertvollste Beitrag: `rpc.py inspect` auswerten, Mapping in `assets/block-map.json` ergänzen, Referenz aktualisieren.
