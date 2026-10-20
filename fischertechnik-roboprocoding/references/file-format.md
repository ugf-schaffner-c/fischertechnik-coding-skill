# .ft file format, controller config and generated code (RX + TXT 4.0)

Tags: VERIFIED-FILE = seen in a real sample in assets/samples; VERIFIED-DOC = official docs; INFERRED = pattern guess, check against a sample; UNKNOWN = ask for a sample.

## 1. File format of a `.ft` project [VERIFIED-FILE]

A `.ft` is a **ZIP archive** (stored, no compression is fine). Real entry list, in this order:

```
.project.json
lib/                      (directory entry)
lib/controller.blockly    (controller / hardware configuration, XML)
lib/controller.py         (generated hardware init, Python)
/mainCode.blockly         (main program, Blockly XML)   <- NOTE the leading slash
/mainCode.py              (generated Python for the main program)
```

Rules for editing or generating:
- Keep the **leading slash** in `/mainCode.py` and `/mainCode.blockly`, and keep the entry names byte-exact. Do not rename them.
- Rewrite the archive by copying all original entries and replacing only the ones you changed. Never rebuild the ZIP from scratch with new names.
- ROBO Pro Coding regenerates the `.py` from the `.blockly` when it saves or opens a project. **Always generate both and keep them consistent.** The `.py` is what runs on the controller; the `.blockly` is what the user sees and edits.
- Keep `lib/controller.*` untouched unless the I/O configuration changes. Changing it means changing both files and every block id that refers to it (section 3).

`.project.json` example (RX):
```json
{"uuid":"e4aaa6a2-70a0-4e91-b21c-f2caa53ae18f","name":"Untitled","mode":"ADVANCED","version":"1.0","controller":"RX","unsaved":true}
```
Fields: `uuid`, `name`, `mode` ("ADVANCED" in the samples seen), `version`, `controller` ("RX" in the sample; other values for TXT, TXT 4.0 and BT Smart are [UNKNOWN]), `unsaved`.

Other ROBO Pro Coding project parts mentioned in the docs [VERIFIED-DOC]: more modules under `lib/` (own Python modules, shown as "Imports" in Blockly), and a GUI definition `lib/display.qml` (+ `display.py`) for TXT 4.0 on-screen displays. A `display.qml` entry is how SofTXT detects a display. Their exact layout in a `.ft` is [UNKNOWN].

---

## 2. Main program: Python shape [VERIFIED-FILE]

```python
import asyncio
import user.lib.controller as controller
from fischertechnik.logging import log as print

async def run(instance):
  await controller.init(instance)
  controller.RX_O8_magnetic_valve.on()
  controller.RX_O1_unidirectional_motor.set_speed(int(255))
  while True:
    if controller.RX_I1_mini_switch.is_closed():
      ...
    await asyncio.sleep(0.01)
```

Facts:
- The entry point is `async def run(instance)`. The first line must be `await controller.init(instance)`.
- Hardware objects live in the module `user.lib.controller` (the file `lib/controller.py`) and are used as `controller.<NAME>`.
- Waiting is `await asyncio.sleep(seconds)`. This is the Blockly block `util_wait_for` with `format=s` [VERIFIED-FILE]. An endless loop **must** contain an `await asyncio.sleep(...)`, otherwise the program starves the scheduler.
- `from fischertechnik.logging import log as print`: use `print` for log output. The docs warn against printing inside loops with a ~10 ms response time [VERIFIED-DOC].
- Generated code indents with 2 spaces. Blockly integers appear as `int(255)`, and `for` loops as `for i in range(int(1), int(N) + 1):`.
- **Variables**: the docs state that all Blockly variables initialise to `None`, and that "local variables are treated as global in the generated file" [VERIFIED-DOC]. In hand-written Python that comes from Blockly, a function that assigns a program variable needs `global name`. Do not use a name before it is set (`None` arithmetic raises `TypeError`).
- Scheduler: one cooperative event loop. A block of code between two `await`s is atomic. Do not block with `time.sleep` or long computations.
- A "Start each time" block exists in the Input, Output, Motor and Counter categories. It runs a section whenever a condition becomes true. Its docs say to keep it short and free of blocking calls and endless loops [VERIFIED-DOC].

---

## 3. Controller configuration: `lib/controller.blockly` [VERIFIED-FILE, RX]

```xml
<xml xmlns="https://developers.google.com/blockly/xml" version="23">
  <block type="rx_controller" id=";xJoC8`g}L6~ldLTFvk#" x="0" y="0">
    <mutation>
      <arg type="Input"  name="Input-0"  value="I1"/>
      <arg type="Input"  name="Input-1"  value="I4"/>
      <arg type="Input"  name="Input-4"  value="-"/>          <!-- "-" = unused slot -->
      <arg type="Output" name="Output-0" value="O1"/>
      <arg type="Output" name="Output-5" value="-"/>
      <arg type="Motor"  name="Motor-0"  value="-"/>
      <arg type="I2C"    name="I2C-0"    value="-"/>
    </mutation>
    <field name="controller_name">RX</field>
    <field name="Input-0">I1</field> ... <field name="Output-0">O1</field> ...
    <value name="Input-0"><block type="mini_switch" id="aGy.+H`;g}5|gcZ{B-@G"/></value>
    <value name="Output-0"><block type="unidirectional_motor" id="!SI82sE~3=ir@pa_FYvF"/></value>
    <value name="Output-1"><block type="compressor"           id="j=g?!pHWU5X5%Ntx-|aq"/></value>
    <value name="Output-2"><block type="magnetic_valve"       id="6F5iD{0xLPlH%};ed3!2"/></value>
    <value name="Output-3"><block type="led"                  id="3p$aNT(JTn.rhN1BCw-Y"/></value>
  </block>
</xml>
```

- The controller block type for RX is `rx_controller`. Types for BT Smart, TXT and TXT 4.0 are [UNKNOWN]; [INFERRED] to follow a similar pattern (`txt_controller` and the like). Verify from a sample file.
- The mutation lists **slot groups**: `Input`, `Output`, `Motor`, `I2C`. Each is a numbered series (`Input-0`, `Input-1`, ...) with the port name as value, or `-` for an unused slot. Each non-empty slot gets a `<value name="Input-n">` containing a device block.
- Device block types seen: `mini_switch`, `unidirectional_motor`, `compressor`, `magnetic_valve`, `led`. Slot counts in the sample: 5 input slots, 6 output slots, 1 motor slot, 1 I2C slot. The sample grew by one empty `-` slot as items were added, so counts are not fixed [INFERRED].
- **Block ids matter**: the id of the controller block and the id of every device block are used by the main program (below). Keep them stable. When a new program is generated, reuse the ids from `lib/controller.blockly`.

### How blocks in `/mainCode.blockly` address a device [VERIFIED-FILE]
```xml
<block type="output_magnetic_valve_toggle_state" id="...">
  <field name="instance_name">;xJoC8`g}L6~ldLTFvk#-6F5iD{0xLPlH%};ed3!2</field>
  <field name="property_name">on</field>
</block>
```
`instance_name` = `<controller block id>` + `-` + `<device block id>`.

---

## 4. Generated hardware init: `lib/controller.py` [VERIFIED-FILE, RX]

```python
import asyncio
import fischertechnik.factories as rx_factory
from fischertechnik.logging import log as print

async def init(controller):
  global instance
  global RX_I1_mini_switch
  ...
  rx_factory.init_controller_factory()
  rx_factory.init_input_factory()
  rx_factory.init_output_factory()
  instance = controller
  RX_I1_mini_switch = rx_factory.input_factory.create_mini_switch(controller, 1)
  RX_O1_unidirectional_motor = rx_factory.output_factory.create_unidirectional_motor(controller, 1)
  RX_O7_compressor = rx_factory.output_factory.create_compressor(controller, 7)
  RX_O8_magnetic_valve = rx_factory.output_factory.create_magnetic_valve(controller, 8)
  RX_O4_led = rx_factory.output_factory.create_led(controller, 4)
```

Naming rule: **`<CTRL>_<PORT>_<device_type>`**, e.g. `RX_I1_mini_switch`, `RX_O8_magnetic_valve`, `RX_I2C_1_gesture_sensor`. Controller prefix `RX` for RX; prefixes for other controllers are [UNKNOWN].

The init functions that exist [VERIFIED-DOC]:
```python
rx_factory.init_controller_factory()   # controller communication
rx_factory.init_input_factory()        # sensors
rx_factory.init_output_factory()       # outputs
rx_factory.init_motor_factory()        # (encoder) motors
rx_factory.init_i2c_factory()          # I2C devices
```
Only the factories that are used appear in the generated `init`.

---

## 12b. VERIFIED TXT 4.0 sample file (`txt4.0_example.ft`) [VERIFIED-FILE]

A real TXT 4.0 project, saved by ROBO Pro Coding with one of every device and display element. It replaces most of the [UNKNOWN]/[INFERRED] marks for TXT 4.0 above. Where this section and an earlier section disagree, **this section wins for TXT 4.0**.

### Archive entries (all stored, no compression)
```
.project.json            {"uuid":"...","name":"Untitled","mode":"ADVANCED","version":"1.0","controller":"TXT4","unsaved":true}
lib/
lib/controller.blockly   hardware config, block type txt4_controller
lib/controller.py        generated hardware init
lib/camera.xml           camera config + detectors (only with a camera in the config)
lib/camera.py            generated camera setup
lib/display.xml          display design (editor model)
lib/display.qml          display design (generated QML, what the controller renders)
/Untitled.blockly        main program Blockly   <- name = PROJECT NAME, leading slash
/Untitled.py             main program Python    <- name = PROJECT NAME, leading slash
```
- **The main-program files are named after the project name** (`/<name>.blockly`, `/<name>.py`), not `mainCode` (that was the name in the RX sample, where the project was also called "Untitled" but the files were `/mainCode.*`; so the naming may differ by controller or version: **copy the names from the sample you are given**).
- `.project.json` `controller` is `"TXT4"` here (RX: `"RX"`).

### Main program shape on TXT 4.0 (different from RX!)
```python
from lib.controller import *

while True:
  pass
```
- **No `async def run(instance)`, no `await controller.init(...)`.** It is a plain top-level script. All hardware objects are module-level globals imported with `from lib.controller import *` (no `controller.` prefix). Whether `asyncio`/`await asyncio.sleep` is used for waiting in TXT 4.0 programs: [UNKNOWN] here (the sample is empty). Look at the generated code of the `util_wait_for` block in a sample before using `time.sleep` or `asyncio.sleep`.
- Blockly: same skeleton as RX: `start_block` with `<statement name="statement">` and e.g. `loop_endless`.

### `lib/controller.blockly` for TXT 4.0
- Controller block type **`txt4_controller`**, with `<field name="controller_name">TXT</field>` and `<field name="mode">0</field>`.
- Slot groups in the mutation (each `-` = unused slot, numbered `Group-n`): `Input` (I1..I8), `Output` (O1..O8, single outputs), `Motor` (M1..M4), `Servomotor` (S1..S3), `Counter` (C1..C4), `I2C` (I2C_1..I2C_4), `USB` (USB1_1, USB1_2). Note the I2C items appear out of order in the sample (`I2C-3` before `I2C-2`): order in the file does not matter, the name does.
- Device block types in a `<value name="Group-n">`:

| Slot | Block type | Python factory call (from `lib/controller.py`) |
|---|---|---|
| Input | `mini_switch` | `txt_factory.input_factory.create_mini_switch(TXT_M, n)` |
| Input | `reed_switch` | `create_mini_switch(TXT_M, n)` (same call as a mini switch) |
| Input | `ultrasonic_distance_meter` | `create_ultrasonic_distance_meter(TXT_M, n)` |
| Input | `color_sensor` | `create_color_sensor(TXT_M, n)` |
| Input | `trail_follower` | `create_trail_follower(TXT_M, n)` |
| (other analog inputs) | `photo_resistor`, `photo_transistor`, `ntc_resistor` [INFERRED from the RX factory and SofTXT; not in this sample] | `create_photo_resistor/photo_transistor/ntc_resistor` |
| Output | `magnetic_valve` | `txt_factory.output_factory.create_magnetic_valve(TXT_M, n)` |
| Output | `led` | `create_led(TXT_M, n)` |
| Output | `unidirectional_motor` | `create_unidirectional_motor(TXT_M, n)` |
| (other outputs) | `compressor` [as on RX] | `create_compressor(TXT_M, n)` |
| Motor | `encodermotor` | `txt_factory.motor_factory.create_encodermotor(TXT_M, n)` |
| Servomotor | `servomotor` | `txt_factory.servomotor_factory.create_servomotor(TXT_M, n)` |
| Counter | `motor_step_counter` with `<field name="instance_name">M1</field>` (names the motor it counts) | `txt_factory.counter_factory.create_encodermotor_counter(TXT_M, n)` followed by `TXT_M_C1_motor_step_counter.set_motor(TXT_M_M1_encodermotor)` |
| I2C | `gesture_sensor` | `txt_factory.i2c_factory.create_gesture_sensor(TXT_M, n)` |
| I2C | `environment_sensor` | `create_environment_sensor(TXT_M, n)` |
| I2C | `rgb_color_sensor` | `create_rgb_color_sensor(TXT_M, n)` |
| I2C | `combined_sensor_6pin` | `create_combined_sensor_6pin(TXT_M, n)` (a 10-pin variant presumably `combined_sensor` [INFERRED]) |
| USB | `camera` | `txt_factory.usb_factory.create_camera(TXT_M, 1)` |
| USB | `microphone` | `create_microphone(TXT_M, 2)` (note: the sample numbers USB1_2 as 2) |

- Block ids are random Blockly ids, one per device and one for the controller. As on RX, main-program blocks address a device through `instance_name` = `<controller block id>-<device block id>` [carry-over from RX; the TXT 4.0 main program in the sample is empty, so this is [INFERRED] for TXT 4.0].

### `lib/controller.py` for TXT 4.0 (verbatim structure)
```python
import fischertechnik.factories as txt_factory
from fischertechnik.control.RemoteControl import RemoteControl
from fischertechnik.control.VoiceControl import VoiceControl

voice_control = None
remote_control = None
def get_voice_control(): ...      # creates VoiceControl() lazily
def get_remote_control(): ...     # creates RemoteControl() lazily

txt_factory.init()
txt_factory.init_input_factory()
txt_factory.init_output_factory()
txt_factory.init_motor_factory()
txt_factory.init_servomotor_factory()
txt_factory.init_counter_factory()
txt_factory.init_i2c_factory()
txt_factory.init_usb_factory()
txt_factory.init_camera_factory()

TXT_M = txt_factory.controller_factory.create_graphical_controller()
TXT_M_I1_mini_switch = txt_factory.input_factory.create_mini_switch(TXT_M, 1)
TXT_M_O3_magnetic_valve = txt_factory.output_factory.create_magnetic_valve(TXT_M, 3)
TXT_M_M1_encodermotor = txt_factory.motor_factory.create_encodermotor(TXT_M, 1)
TXT_M_S1_servomotor = txt_factory.servomotor_factory.create_servomotor(TXT_M, 1)
TXT_M_C1_motor_step_counter = txt_factory.counter_factory.create_encodermotor_counter(TXT_M, 1)
TXT_M_C1_motor_step_counter.set_motor(TXT_M_M1_encodermotor)
...
txt_factory.initialized()
```
- Variable naming on TXT 4.0: **`TXT_M_<PORT>_<device_type>`** (`TXT_M` = the master controller). With extension controllers other prefixes exist [UNKNOWN].
- Initialisation runs at import time (module top level, synchronous), not in an `async def init`.
- Remote and voice control helpers are always generated (`get_remote_control()`, `get_voice_control()`).
- The factories used on TXT 4.0 beyond RX: `init_servomotor_factory`, `init_counter_factory`, `init_usb_factory`, `init_camera_factory`.

### `lib/display.xml` (editor model) and `lib/display.qml` (generated)
`display.xml` header: `<xml width="480" height="460" type="display" version="3">` (the editor canvas is 480 x 460; **the real TXT 4.0 screen size should be taken from the project/IDE, 480 x 460 is the canvas used in this sample**). Each element is `<item id="uuid" class="..."><icon>...</icon><nodeType>...</nodeType><x/><y/><width/><height/><minWidth/><minHeight/><name>...</name> ... <geometry><x/><y/><width/><height/></geometry></item>`.

| class | extra properties in display.xml | QML element and properties in display.qml |
|---|---|---|
| `TXTButton` | `text`, `fontSize`, `fontStyle`, `enabled` | `TXTButton { id; text; font.pixelSize; font.bold; font.italic; font.underline; enabled; x; y; width; height }` |
| `TXTCheckBox` | `text`, `fontSize`, `fontStyle`, `enabled`, `checked` | `TXTCheckBox { ... checked; enabled ... }` |
| `TXTSwitch` | `text`, `fontSize`, `fontStyle`, `enabled`, `checked` | `TXTSwitch { ... }` |
| `TXTSlider` | `value`, `minValue`, `maxValue`, `orientation` (`Qt.Horizontal`), `enabled` | `TXTSlider { from; value; to; orientation; enabled; x; y; width; height }` |
| `TXTLabel` | `text`, `textAlign`, `color` (`#ffffff`), `fontSize`, `fontStyle` | `TXTLabel { text; font...; verticalAlignment: Text.AlignVCenter; horizontalAlignment: Text.AlignLeft; color; elide: Text.ElideRight; ... }` |
| `TXTInput` | `text`, `textAlign`, `color`, `fontSize`, `fontStyle` | `TXTInput { text; onTextChanged: ...; ... }` |
| `StatusIndicator` | `color`, `active` | `StatusIndicator { color; active; x; y; width; height }` |
| `Gauge` | `value`, `minValue`, `maxValue`, `orientation`, `tickmarkStepSize`, `minorTickmarkCount` | `Gauge { minimumValue; value; maximumValue; orientation; tickmarkStepSize; minorTickmarkCount; formatValue: function(value){return value.toFixed(1);} ... }` |
| `TXTImage` | `image` | generated as a `TXTLabel { id; text: ""; ... }` (the image content is not in the QML in the sample) |

- **The element `name` in display.xml becomes the QML `id`** (e.g. `txt_button`). Use these ids in the program.
- QML file skeleton:
```qml
// auto generated content from display configuration
import QtQuick 2.2
import QtQuick.Window 2.0
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Extras 1.4

TXTWindow {
  Rectangle { id: rect; color: "grey"; anchors.fill: parent }
  TXTButton { id: txt_button; text: "press me"; font.pixelSize: 22; ... x: 39; y: 34; width: 100; height: 40 }
  ...
}
```
- Elements overlap freely; the sample's elements are placed sloppily (switch under checkbox, gauge over label). Lay them out deliberately: avoid overlapping hit areas.
- **`lib/display.qml` is auto-generated from `lib/display.xml`.** To change a UI from outside the IDE: edit `display.xml` (name, x, y, width, height, text, ranges, enabled) and regenerate `display.qml` by the same mapping, so both stay in sync. Never edit only one of them.
- The sample contains **no handlers**: the main program is empty, so how event programs are stored (extra `display_<name>` files? inside `/Untitled.blockly`?) is [UNKNOWN]. Ask for a sample with one button event program before generating UI logic.

### `lib/camera.xml` and `lib/camera.py` (only when a USB camera is in the config)
- `camera.xml`: `<xml width="320" height="240" type="camera" version="3" rotate="false" name="TXT_M_USB1_1_camera" fps="15">` with detector items `ColorDetector`, `MotionDetector`, `BallDetector`, `LineDetector`, `BlockedArea`, each with `x y width height minWidth minHeight name geometry` and detector-specific fields (`contrast`, `tolerance`, `minBallDiameter`, `maxBallDiameter`, `startRangeValue`, `endRangeValue`, `color`, `minLineWidth`, `maxLineWidth`, `numberOfLines`, `invert`).
- `camera.py` (generated, runs `from lib.controller import *`):
```python
TXT_M_USB1_1_camera.set_rotate(False); .set_height(240); .set_width(320); .set_fps(15); .start()
color_detector  = txt_factory.camera_factory.create_color_detector(x, y, w, h, contrast)
TXT_M_USB1_1_camera.add_detector(color_detector)
motion_detector = txt_factory.camera_factory.create_motion_detector(x, y, w, h, tolerance)
ball_detector   = txt_factory.camera_factory.create_ball_detector(x, y, w, h, minDia, maxDia, startRange, endRange, [r,g,b], tolerance)
line_detector   = txt_factory.camera_factory.create_line_detector(x, y, w, h, minLine, maxLine, startRange, endRange, numberOfLines, invert)
blocked_area    = txt_factory.camera_factory.create_blocked_area(x, y, w, h)
TXT_M_USB1_1_camera.add_blocked_area(blocked_area)
```

### What this changes in the earlier sections
- Section 1: `.project.json` `controller` can be `RX` or `TXT4`. The ZIP can contain more `lib/` entries (display, camera). Main-program entry names are `/<project name>.*` on TXT 4.0.
- Section 2: the `async def run(instance)` skeleton is **RX only**. TXT 4.0 uses a flat script with `from lib.controller import *`.
- Section 3/4: controller block `txt4_controller`; extra slot groups `Servomotor`, `Counter`, `USB`; factory prefix `txt_factory`, device prefix `TXT_M_`.
- Section 6: TXT 4.0 column is now [VERIFIED-FILE] for factories, block types and file layout.
- Section 12 (display): the file format and element properties are now verified (above). The Python-side `ftgui` calls from SofTXT remain [INFERRED] until a sample with event handlers or display accesses is available.

---
