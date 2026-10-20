---
name: fischertechnik-roboprocoding
description: Write, convert, validate and package fischertechnik ROBO Pro Coding programs (Blockly graphical or Python) for the RX controller, TXT 4.0 (incl. on-device display UI, camera, servo, encoder, I2C) and BT Smart controller. Use this skill whenever the user mentions fischertechnik, ft, ROBO Pro Coding, RoboProCoding, TXT 4.0, RX controller, BT Smart, a .ft project file, Blockly for a robot or model (lift, conveyor, sorting, pneumatics, sensors, motors), or wants a fischertechnik program, a Python version of one, or a TXT display UI, even if they do not name the controller or file type.
---

# fischertechnik ROBO Pro Coding

Produces working **ROBO Pro Coding** programs for fischertechnik controllers. The deliverable is either a **`.ft` project** (Blockly + generated Python, opens in ROBO Pro Coding) or a plain **`.py`** file. Block types, factory names and file layouts differ per controller and several are only known from real sample files, so this skill works from samples and checks documentation on demand instead of guessing.

## 1. Choose the output format first (ask once, at the start)

Ask: **Python (.py)** or **Blockly (.ft project)?** Explain the consequence in one line each and say it can be converted later:

| Choice | What the user gets | Good for |
|---|---|---|
| **Blockly** | `.ft` containing `.blockly` + matching `.py` + controller config | Opening in ROBO Pro Coding, graphical editing, teaching |
| **Python** | `.py` (and, in Claude Code, files edited in place) | Complex logic, state machines, quick iteration, testing in a simulator |

Conversion later: Python to Blockly with `scripts/rpc.py build` (restricted subset, see `references/blockly-xml.md`); Blockly to Python is the `.py` stored in the `.ft` (`rpc.py extract-py`). A `.ft` must never contain a `.py` that disagrees with its `.blockly`: ROBO Pro Coding can regenerate the Python from the Blockly. If the user wants Python features outside the convertible subset but still needs a `.ft`, say plainly that the Blockly part cannot represent it and offer the `.py` only, or a flat simplified program.

Where am I running?
- **Web chat** (no shared filesystem with the user): work in a scratch directory, then send the finished `.ft` or `.py` with the file tool. Say what was tested and what not.
- **Claude Code / agent with the user's files**: edit the project files in place. Use `rpc.py unpack` to a directory, edit, `rpc.py pack --template original.ft`, then `rpc.py validate`. Never rewrite a file from a truncated tool output.

## 2. Establish ground truth (sample file or question round)

1. If the user gave a `.ft` (or a project folder): run `python scripts/rpc.py inspect FILE.ft`. It lists controller type, every device with its **Python variable name and `instance_name` id**, block types in use, display elements. Treat this as the truth.
2. If not, and the controller is **RX** or **TXT 4.0**, start from `assets/samples/rx_sample.ft` or `assets/samples/txt4_sample.ft` as a template, but first run the question round below so the device list matches the user's wiring. Device ids must come from the template's `lib/controller.blockly`; the user's hardware configuration (which ports have which device) changes the config, not just the program. If the wiring differs from the sample, ask the user to save a project with the right configuration in ROBO Pro Coding and send it. Do not hand-edit controller configs unless a sample shows the exact device block.
3. For **BT Smart** or any controller without a sample: stop and ask for a minimal `.ft` saved from ROBO Pro Coding with that controller and one block of each needed kind. Guessing block names produces files that fail to load.

Question round (one message; use AskUserQuestion when available; skip what the sample already answers):
- Controller (RX, TXT 4.0, BT Smart), connection (USB, WLAN, Bluetooth).
- Per port: device type and meaning (button wiring normally open or closed; valve on = extended or not; motor direction), safe state.
- What must happen at start and in normal operation; timings, speeds (0..512), counts, positions; error handling and indicators; what the user wants to tune by hand (constants at the top).
- TXT 4.0 only: on-screen UI wanted? Elements, values shown, commands, locking, layout (`references/display-ui.md`).
- Can the user test on hardware? If not, plan a simulation (`references/patterns.md`).
Repeat a short spec back and confirm anything that could damage hardware (pneumatics, compressors, lifts, jams).

## 3. Documentation refinder (read only what the task needs)

Never load all documentation. Run:

```
python scripts/find_docs.py --controller <rx|txt4|bt> --need "<comma separated topics, e.g. encoder motor, servo, display slider>"
```

It scores `assets/docs-index.json` and prints at most a few URLs, cheapest and most relevant first, plus the local summary that already covers the topic. Procedure:
1. Read the **local reference** named in the output first (`references/*.md`): file format, Python API, display, patterns.
2. Fetch the **live URL** (WebFetch) only when a detail is missing, a block or method is not in the local files, or the user asks for current behaviour. Online docs change; the local files are a dated summary. Prefer `doc.fischertechnik-cloud.com` pages; large PDFs only with a narrow question.
3. If nothing scores, WebSearch `site:doc.fischertechnik-cloud.com <topic>`, or ask for a sample.
4. When live docs disagree with a local reference, trust the live doc and the sample file, and say so. Add confirmed new facts to your answer, not silently to the references.

## 4. Write the program

Controller shapes differ (details and exact names: `references/file-format.md`, `references/python-api.md`):
- **RX**: `async def run(instance): await controller.init(instance)`, devices as `controller.RX_I1_mini_switch`, waits with `await asyncio.sleep(s)`. Main files are `/mainCode.py` and `/mainCode.blockly` in the sample.
- **TXT 4.0**: flat script with `from lib.controller import *`, devices as `TXT_M_<PORT>_<type>`, main files named after the project (`/Untitled.py`). Whether waits use `asyncio` or `time` is unverified: check how the sample or the live docs generate a wait before writing one.
- **BT Smart**: unknown until a sample exists.

Rules that prevent the usual failures:
- Put every tunable number at the top as an UPPER_CASE constant with a one-line comment; in Blockly they become variables set first.
- Tick-based logic: one loop, one `await asyncio.sleep(0.01)`; no blocking calls. Do not add a second 0.01 s wait at the end of a loop in Blockly (the IDE adds its own).
- Motor/PWM values are ints 0..512, never above 512. Servo 0..512, centre 256.
- Detect edges with a `*_prev` variable and debounce; count pulses for position instead of timing where a pulse sensor exists.
- Keep the Python inside the convertible subset when the user chose Blockly (`references/blockly-xml.md`); otherwise freer Python is fine.
- For hardware that can hurt itself (valves, compressor, lifts): define the safe state, order of switching, timeouts, and an error indication; follow `references/patterns.md`.
- Display (TXT 4.0): write a JSON spec and run `scripts/display_gen.py`; handlers are not generated because their stored form is unverified. Use the documented rules (refresh 0.2 to 1 s, disable elements until ready).

## 5. Build, validate, test, deliver

1. **Blockly output**: `python scripts/rpc.py build prog.py --template <sample-or-user>.ft --out result.ft`. It maps hardware calls through `assets/block-map.json`, warns when a block is only verified on another controller, and refuses (exit 1) when something cannot be converted. It never ships a partial conversion.
2. **Python output**: send the `.py`; if a `.ft` is also wanted, convert with `build`; if conversion fails, say which construct blocks it.
3. `python scripts/rpc.py validate result.ft`: syntax of every `.py`, XML of every `.blockly`/`.xml`, `instance_name` references, hardware names, duplicate ids.
4. Test without hardware when logic is non-trivial: mock the controller module and step a small physics model (`references/patterns.md`).
5. Deliver the file(s) (web chat: file tool). State plainly: what was simulated, what was validated, and that loading in ROBO Pro Coding / on the controller was **not** tested unless the user did.
6. When a block mapping is missing (encoder motor, servo, counter, display handlers, BT Smart): ask for a sample `.ft` containing that block, run `rpc.py inspect` on it, and add the mapping to `assets/block-map.json` (that is how the skill grows).

## Files in this skill
- `scripts/rpc.py`: inspect, unpack, pack, validate, extract-py, build (Python to Blockly).
- `scripts/find_docs.py` + `assets/docs-index.json`: the documentation refinder (live links, cost-aware).
- `scripts/display_gen.py`: TXT 4.0 `display.xml` + `display.qml` from a JSON spec.
- `assets/samples/`: real `.ft` files (RX, TXT 4.0) as ground truth. `assets/block-map.json`: verified block mappings.
- `references/file-format.md` (zip layout, controller config, generated code, display/camera files), `python-api.md` (device APIs), `blockly-xml.md` (block cookbook, convertible subset), `display-ui.md`, `controllers.md` (RX, TXT 4.0, BT Smart, gaps), `patterns.md` (control patterns, simulation).
