# Blockly XML cookbook for the main program

## 7. Blockly XML cookbook (main program) [VERIFIED-FILE unless noted]

Document skeleton:
```xml
<xml xmlns="https://developers.google.com/blockly/xml" version="23">
  <variables><variable id="v_x">x</variable></variables>   <!-- when variables are used [INFERRED, accepted by the program in the working project] -->
  <block type="start_block" id="..." deletable="false" x="0" y="0">
    <statement name="statement"> ...chained blocks via <next>... </statement>
  </block>
</xml>
```
- Entry block: `start_block`, with `<statement name="statement">`. Statements chain with `<next><block ...>...</block></next>`.
- Every block needs a **unique `id`**. Use a counter-based unique string. Characters allowed in ids include `` ` ; # { } ~ ! @ | + . `` etc. (the files use random Blockly "soup" ids). Escape `& < >` in text.
- Numbers and expressions use value inputs with shadow blocks: `<value name="value"><shadow type="output_number"><field name="OUTPUT_NUM">255</field></shadow></value>`, `<shadow type="math_number"><field name="NUM">0.5</field></shadow>`.

Block types observed [VERIFIED-FILE] or produced by a generator and then accepted in the working project [VERIFIED-RUN where noted]:

| Block type | What it does | Key fields / inputs |
|---|---|---|
| `start_block` | Program start | statement `statement` |
| `loop_endless` | `while True:` | statement `DO` |
| `controls_if` | if / elif / else | value `IF0`, statement `DO0`; `ELSE` statement with `<mutation else="1">` and `elseif="n"` [VERIFIED-RUN] |
| `controls_whileUntil` | while / until | field `MODE`=`WHILE`; value `BOOL`; statement `DO` |
| `controls_for` | for-range loop | field `VAR`; values `FROM`, `TO`, `BY`; statement `DO` [VERIFIED-RUN] |
| `util_wait_for` | `await asyncio.sleep(x)` | field `format`=`s`; value `value` (math_number) |
| `input_mini_switch_if_state` | condition: switch state | fields `instance_name`, `property_name` = `open` / `closed` |
| `output_magnetic_valve_toggle_state` | valve on/off | `instance_name`, `property_name` = `on` / `off` |
| `output_compressor_toggle_state` | compressor on/off | same |
| `output_led_toggle_state` | LED on/off | same [VERIFIED-RUN] |
| `unidirectional_motor_set_speed` | motor speed | `instance_name`; value `value` (shadow `output_number`, field `OUTPUT_NUM`) |
| `variables_set` / `variables_get` | variables | field `VAR` (with id), value `VALUE` [VERIFIED-RUN] |
| `math_number`, `math_arithmetic`, `math_modulo`, `math_round`, `logic_compare`, `logic_operation`, `lists_*` | expressions | standard Blockly [VERIFIED-RUN] |
| `procedures_defnoreturn` | function definition | field `NAME`; statement `STACK` [INFERRED from standard Blockly; **not verified to load in ROBO Pro Coding**] |
| `procedures_callnoreturn` | function call | `<mutation name="...">` [same caveat] |

Naming pattern for hardware blocks [INFERRED]: `output_<device>_toggle_state`, `output_<device>_<action>`, `input_<device>_if_state`, `<device>_set_speed`. Anything not in the table above: ask for a sample, or ask the user to place the block in a scratch program and send the `.ft`.

### Style and robustness rules
- Keep generated Blockly readable: group the logic into named functions and add a comment per block when generating from a program model.
- When a program must work even if function blocks are rejected, also produce a **flat variant** (everything inlined in `run`) as a fallback file. Offer both.
- Never trust a hand-generated `.blockly` to load. Validate that the XML parses (`xml.dom.minidom`), that the Python parses (`ast.parse`), and say clearly that loading in ROBO Pro Coding was not tested.

---

## Packaging checklist
1. Copy the original `.ft`, or the extracted `lib/controller.*` and `.project.json`.
2. Generate `/mainCode.py` and `/mainCode.blockly` from **one** program description, so both always agree.
3. `ast.parse` the Python, parse the XML, and check that every referenced `instance_name` exists in `controller.blockly`.
4. Write the ZIP with the original entry names and order. Replace only the changed entries.
5. Also deliver a plain `mainCode_Vorschau.py` (readable preview) and, when functions/globals are used, a flat fallback `.ft`.
6. State clearly what was tested (simulation or hardware) and what was not (loading in ROBO Pro Coding).

---

## Facts learned from comparing the RX sample's Python and Blockly [VERIFIED-FILE]
- ROBO Pro Coding appends `await asyncio.sleep(0.01)` to every loop body itself (`loop_endless`, `controls_whileUntil`). The sample Python has 4 sleeps, the Blockly has 2 `util_wait_for` blocks. So **do not add an explicit 0.01 s wait at the end of a loop in Blockly**; it would double the cycle time (about 0.02 s) when the Python is regenerated. `scripts/rpc.py py2blockly` drops a trailing `await asyncio.sleep(0.01)` for that reason.
- Python written by hand with a trailing 0.01 sleep and the regenerated Python from its Blockly therefore agree.
- A `.ft` whose `.py` and `.blockly` disagree is dangerous: opening/saving in ROBO Pro Coding may regenerate the Python from Blockly. Always generate both from the same source (`rpc.py build`).

## Python subset accepted by `rpc.py py2blockly` / `build`
Statements: assignment and `+=`-style updates of plain names, `if/elif/else`, `while True`, `while cond`, `for i in range(...)`, `break`, `pass`, zero-argument `def` (procedures, unverified in the IDE), calls of mapped hardware methods (`assets/block-map.json`), `await asyncio.sleep(<number>)`.
Expressions: numbers, booleans, names, `+ - * / % **`, comparisons, `and/or/not`, `int()/round()`, mapped hardware queries (e.g. `is_closed()`).
Not supported (converter stops with an error instead of guessing): strings, lists, f-strings, `print`, classes, imports of own modules, functions with parameters, threads, display handlers. Use a flat program or ask for a sample so a mapping can be added to the block map.
