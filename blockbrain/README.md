# Verwendung in Blockbrain (und ähnlichen Prompt-basierten Plattformen)

Laut der Blockbrain-Dokumentation werden Skills dort in der App angelegt (Name, Handle wie `/fischertechnik`, Inhalt als Anweisungstext) und nicht als Ordner mit Skripten hochgeladen (https://docs.blockbrain.ai/for-users/all-about-knowledge-management/skills-in-blockbrain.md). Ob Skripte ausgeführt werden können, steht dort nicht; ohne Ausführung entfallen `rpc.py`, `find_docs.py` und `display_gen.py`.

**Vorgehen**
1. Neuen Skill anlegen, Inhalt von `skill-prompt.md` einfügen.
2. Die Dateien aus `fischertechnik-roboprocoding/references/` und `assets/samples/` (falls Dateianhänge erlaubt sind) als Wissensquelle (Knowledge) hinzufügen, damit der Assistent Dateiformat, API und Beispielprojekte nachschlagen kann.
3. Ausgabe: Der Assistent kann den Python-Code und die `.ft`-Struktur beschreiben bzw. als Text liefern; das Packen/Validieren muss lokal mit den Skripten erfolgen (`python rpc.py validate ...`).

Das Format von Blockbrain wurde nicht getestet; bitte prüfen und Rückmeldung als Issue geben.
