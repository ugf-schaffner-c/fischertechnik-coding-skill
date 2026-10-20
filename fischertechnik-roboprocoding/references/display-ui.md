# TXT 4.0 display (on-device UI)

File layout and element properties are verified in file-format.md (section "VERIFIED TXT 4.0 sample"). Read that section first.

## 12. TXT 4.0 display (on-device UI) [mostly VERIFIED-DOC; code-level details from SofTXT = INFERRED]

The TXT 4.0 has a touch display. ROBO Pro Coding lets a project define a **screen** with UI elements, and the program reads and writes them. Only the TXT 4.0 has this; RX and BT Smart have no display (use LEDs / the app instead).

> **Update:** a real TXT 4.0 sample file has since been analysed. File layout, `display.xml`/`display.qml` structure and element properties are verified in **section 12b**; read that first. Only the program-side UI calls below are still inferred.

### 12.1 Workflow in the IDE [VERIFIED-DOC]
1. In the **Display** category create a new file (pages symbol), drag elements onto the screen area, and set properties in the Inspector.
2. Every element has a **name** (the identifier used by the program), a size, a top-left position in pixels and an initial state.
3. Reaction to the user is programmed either in the main program or in the element's **own event program** ("Wenn ... gedrueckt" type programs). Event programs share variables with the main program.

### 12.2 Elements, blocks and events [VERIFIED-DOC]
| Element | Properties | Set blocks | Event program | Event value |
|---|---|---|---|---|
| **Label** | size, position, name, text | set label text | none | |
| **Input field** | size, position, name, initial text | set input field text | "when input is complete" | event block = `text` |
| **Measurement instrument** (gauge) | size, position, name, alignment, min/max range, start value | set instrument to value (out-of-range values are clamped; docs say it shows no values below 1) | none | |
| **Status indicator** (diode) | size, position, name, colour, initial active/inactive | set status indicator active / inactive | none | |
| **Slider** | size, position, name, active, alignment, range, start value | set slider value; set slider activated | "on slider moved" | `value` (decimal, use round for integers) |
| **Button** | size, position, name, text, active | set button activated | "on button clicked" (fires on release) | no value |
| **Switch** | size, position, name, side text, active, start state | set enabled / checked (true/false) | "on switch toggled" | `checked` (bool) |
| **Checkbox** | size, position, name, side text, active, start state | set enabled / checked | "on checkbox toggled" | `checked` (bool) |

The **event block** returns the element's value, only works inside an event program, and refers automatically to the element that owns it; a dropdown selects the returned property (`value`, `checked`, `text`).

### 12.3 Rules for display programs [VERIFIED-DOC]
- Refresh the display from a **separate thread / loop every 200 ms to 1 s**, never in the fast control loop (keep the control loop responsive; the docs mention a 10 ms loop).
- Event callbacks must be **short and non-blocking**.
- **Disable action elements at startup** (set activated/enabled = false) and enable them once the display thread is initialised, so a touch cannot fire before the program is ready.
- Do not let modules import each other's functions (circular references are not resolved).
- The debugger only supports single-threaded programs; a display thread disables normal debugging.
- The TXT 4.0 screen is small (a SofTXT window uses 240 x 230 px as a stand-in for the real size; the real pixel size is [UNKNOWN] here, so ask the user or read it from the IDE's editor canvas). Touch targets should be large.

### 12.4 File layout [VERIFIED-DOC + INFERRED]
- The UI is stored as **`lib/display.qml`** in the project (SofTXT looks for exactly this path and, if absent, runs without UI). A display module `display.py` can exist next to it. Whether the zip uses leading slashes for these entries is [UNKNOWN]; copy the entry names of a real sample.
- QML is the Qt Quick language. ROBO Pro Coding's QML uses custom elements from a `QtQuick.Window 2.0` module (SofTXT mimics them): `TXTWindow`, `TXTButton`, `TXTLabel`, `TXTSlider`, `TXTSwitch`, `TXTCheckBox`, `TXTInput`. Gauge and status-indicator elements exist in the IDE too but have no SofTXT counterpart.
- Visual style in the emulation: white text on a coloured background, scaled font (`font.pixelSize * 0.62`), blue (`#1984F3`) slider, grey (`#909090`) buttons.
- **Do not hand-write `display.qml` from scratch** unless the user supplied a sample. Ask for a `.ft` that contains at least one of each element needed, copy its structure, and only change names, positions, texts and ranges.

### 12.5 How the program talks to the UI (Python level) [INFERRED from SofTXT's `ftgui.py`; SofTXT copies the generated-code API of ROBO Pro Coding, but real generated code was not seen, so check a sample]
```python
import ftgui                              # provides fttxt2_gui_connector (import path in real projects: check a sample)
gui = ftgui.fttxt2_gui_connector("display")   # constructor takes a name

gui.set_attr("label1.text", "Hello")      # write a property. Strings are quoted, "true"/"false" are not
gui.set_attr("button1.enabled", "false")  # disable an element at startup
gui.set_attr("slider1.value", "128")
value = gui.get_attr("slider1.value")     # read a property back (blocks until the UI answers)

def on_slider(event):                     # event is a dict
    speed = event["value"]                # int for sliders
gui.slider_moved("slider1", on_slider)
gui.button_clicked("button1", lambda e: print("clicked"))   # e is empty
gui.switch_toggled("switch1", lambda e: print(e["checked"]))  # bool
gui.checkbox_toggled("cbox1", lambda e: print(e["checked"])) # bool
gui.input_accepted("input1", lambda e: print(e["text"]))     # str
```
- Property access is `<element name>.<qml property>` (`text`, `value`, `enabled`, `checked`, ...). Values travel as strings.
- Event handlers run in the GUI thread: keep them tiny, set variables, return. Let the main async loop do the real work.
- `get_attr` busy-waits for the answer; do not call it from the 10 ms control loop.
- Handler registration waits until the element exists in the QML scene; register handlers before enabling the elements.

### 12.6 Pattern for a UI-driven program
```python
state = {"run": False, "speed": 0}

def on_start(e): state["run"] = True
def on_stop(e):  state["run"] = False
def on_speed(e): state["speed"] = e["value"]

async def run(instance):
    await controller.init(instance)
    gui.set_attr("start_btn.enabled", "false"); gui.set_attr("stop_btn.enabled", "false")
    gui.button_clicked("start_btn", on_start); gui.button_clicked("stop_btn", on_stop)
    gui.slider_moved("speed_slider", on_speed)
    gui.set_attr("start_btn.enabled", "true"); gui.set_attr("stop_btn.enabled", "true")
    ui_tick = 0
    while True:
        controller.M1_motor...  # control logic here (names depend on the real config)
        ui_tick += 1
        if ui_tick >= 50:                 # refresh the display every ~0.5 s only
            ui_tick = 0
            gui.set_attr("speed_label.text", str(state["speed"]))
        await asyncio.sleep(0.01)
```
(Names are illustrative. Verify the actual object names against a real sample.)

### 12.7 Question round for a UI (add to section 0 when the controller is a TXT 4.0)
- What should be visible: values (labels, gauges), states (status lights), setpoints (sliders), commands (buttons, switches, checkboxes), text entry?
- Which actions need confirmation or must be locked during operation (disabled buttons)?
- Multiple screens/pages? (page switching is [UNKNOWN] here; ask for a sample)
- Language, text sizes, colours, naming of elements (use short ASCII names, e.g. `speed_slider`).
- Which values are updated how often? (default 200 ms to 1 s)

### 12.8 Testing a UI program
- On a PC, mock `ftgui.fttxt2_gui_connector` with a class that stores attributes in a dict and lets the test call the registered handlers. Check: handlers are registered before elements are enabled, handlers do not block, refresh rate is limited.
- SofTXT (PyQt5) can render `display.qml` and run the program against ROBO Pro Coding; it only supports part of the elements. Useful as a visual sanity check, not as proof.

---
