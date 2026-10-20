# Controller families

## 6. Controller families: differences

| | **RX** | **BT Smart** | **TXT** | **TXT 4.0** |
|---|---|---|---|---|
| Programming | ROBO Pro Coding (Python/Blockly, `async def run(instance)`) [VERIFIED-FILE] | ROBO Pro Coding (USB / Bluetooth) [VERIFIED-DOC: only listed in the manual's TOC] | Legacy: ROBO Pro (classic) or ftrobopy; ROBO Pro Coding availability [UNKNOWN] | ROBO Pro Coding (Blockly + Python) [VERIFIED-DOC] |
| Inputs | I1..I8 (the sample used 5 input slots) [VERIFIED-FILE]; counters / motor-encoder inputs [UNKNOWN] | [UNKNOWN] | I1..I8, C1..C4 [VERIFIED-DOC] | 8 universal inputs I1..I8 (digital or analog), 4 counter inputs C1..C4 [VERIFIED-DOC] |
| Outputs | O1..O8 (sample used O1, O4, O6, O7, O8) [VERIFIED-FILE] | [UNKNOWN] | M1..M4 or O1..O8 [INFERRED] | 4 motor outputs M1..M4, or 8 single outputs O1..O8; 3 servo outputs S1..S3 [VERIFIED-DOC] |
| I2C | `Motor`/`I2C` slots in config [VERIFIED-FILE]; ports from docs: `create_*_sensor(controller, 1..3)` | [UNKNOWN] | | 2 six-pin I2C sockets EXT1, EXT2 (3.3 V) [VERIFIED-DOC] |
| Connection | USB, Bluetooth [VERIFIED-DOC TOC] | USB, Bluetooth | | USB, WLAN, WLAN access point, Bluetooth; API key from Settings > API key [VERIFIED-DOC] |
| Display | none | none | has a screen; legacy programming [UNKNOWN] | touch display with UI elements (section 12) [VERIFIED-DOC] |
| Factory prefix in generated code | `rx_factory`, vars `RX_...` [VERIFIED-FILE] | [UNKNOWN] | [UNKNOWN] | [UNKNOWN]; SofTXT uses `fischertechnik.factories` with `create_graphical_controller` |

Mixing controllers (master + extensions, or old + new) is covered in the ROBO Pro Coding manual on pages ~399-404 [VERIFIED-DOC TOC], but no content was read. Ask the user before assuming a multi-controller design.

**TXT 4.0 details (project layout, factories, block types, display) are in section 12b and differ from RX** (flat script, `TXT_M_...` names, `txt4_controller`).

**Rule:** for BT Smart and any case marked [UNKNOWN], obtain a sample `.ft` first. Do not extrapolate port numbers or class names from the RX tables above.

---

## Known gaps
- Full block type list for outputs/inputs other than the ones in section 7 (lamps, encoder motors, servos, counters, ultrasonic, I2C, display, MQTT, voice, ML): **not read from any file**.
- Controller config block types and `controller` value in `.project.json` for BT Smart (TXT 4.0 is now verified, see section 12b).
- Official Python reference for outputs/motors/servos: only the RX **sensor** reference page exists in the public docs. Output/motor signatures come from `.ft` files and the SofTXT re-implementation.
- Whether ROBO Pro Coding accepts hand-built `procedures_*` blocks was not confirmed at the time of writing. Offer a flat fallback.
- Counter inputs on RX, servo ports, and pulse-counter ports: not documented in the pages read.
- TXT 4.0: the main program in the sample is empty, so the Blockly block types and generated Python for motor/servo/counter/display/waiting blocks, event programs for display elements, and `instance_name` addressing are still unverified for TXT 4.0 (see section 12b).

Close each gap by asking the user for a sample `.ft` that contains the missing block. This is the most reliable method.

---

## BT Smart Controller (what is known)
- [VERIFIED-DOC] 2 motor/lamp outputs M1, M2 and 4 inputs I1..I4 (buttons, light barriers). Official app: ROBO Pro Smart (Android/iOS) for the BT Smart Beginner Set. Sources: https://www.ftcommunity.de/knowhow/computing/roboprosmart/ and https://www.fischertechnik.de/en/toys/e-learning/bt-smart-controller
- [VERIFIED-DOC, only a table of contents] The ROBO Pro Coding manual has chapters for the BT Smart Controller (USB, Bluetooth, LED blink codes) and for mixing controllers.
- [UNKNOWN] Block type of the controller config (maybe `bt_smart_controller`), `.project.json` `controller` value, Python factory prefix and variable naming, whether M1/M2 are created as `create_unidirectional_motor`/`create_motor`. Do not guess: ask the user for a minimal `.ft` saved from ROBO Pro Coding with a BT Smart controller and one block of each type, then use `scripts/rpc.py inspect` on it.
