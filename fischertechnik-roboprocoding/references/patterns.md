# Control patterns that worked on real hardware, and testing without hardware


Take these as a starting point.

1. **Tick loop**: `while True: step(); await asyncio.sleep(0.01)`. One tick = about 10 ms. Express timeouts in ticks (`TICKS = seconds * 100`) as named constants.
2. **State machine**: an integer `state` plus `settle` counters. One function per phase (`phase_xyz()`), called from the main step only when `state == ST_XYZ`.
3. **Edge detection and debounce**: read each input once per tick into `x`, keep `x_prev`. Accept an edge only if `tick - last_edge >= DEBOUNCE`. Ignore mechanical flicker of switches while a cylinder is moving.
4. **Position counting with a pulse sensor** (e.g. a magnet / wheel sensor on a normally-open mini switch): count rising edges into `total`. Use position differences (`total - x`) as time-independent "distances". This also keeps logic correct when the motor speed changes.
5. **Constant speed from voltage-controlled motors**: measure the period between pulses, smooth it (`pavg = (pavg*3 + p)/4`), and adjust `speed += KP*(pavg - target)`, clamped to `[SPEED_MIN, 512]`. A smaller target period means faster.
6. **Pneumatics**: valve ON = cylinder extended (blocking). Wait for pressure after switching the compressor on (50-200 ticks, tune). Never close a cylinder onto a moving part; open the exit and then start the conveyor, not the other way round.
7. **Supervision**: stall check (no pulses for N ticks while the motor should run), travel-time checks, missing-item checks, self test of sensors at start (motor on: do the pulses arrive?).
8. **Error indication on one LED**: tens digit = long blinks, ones digit = short blinks, pause, repeat. Compressor off on error. A normally-open button acknowledges minor errors and restarts the start-up.
9. **Config block**: put all tunable numbers at the top of the Python file as UPPER_CASE constants with a one-line comment each, and mirror them as variables at the start of the Blockly program.
10. **Pause**: a button that toggles `paused` and freezes counters/timers that would otherwise run out. Do not let timers keep counting during pause.

---

## Testing without hardware
- Mock the controller module: put a fake `user.lib.controller` (with the same attribute names, e.g. `RX_I1_mini_switch.is_closed()`, `.on()`, `.off()`, `.set_speed()`) and a fake `fischertechnik.logging` into `sys.modules`.
- Replace `asyncio.sleep` with a function that **steps a physics model** (positions, sensors, cylinders, queues) by `dt` and then yields. Raise a stop exception after `T` simulated seconds.
- Insert a probe via regex after the tick increment to log `state` changes, and record all output events with timestamps.
- Test: scenarios with different starting conditions, random seeds, pauses at random times, sensor flicker, stalls, missing items, acknowledge-button paths, and decode the error LED pulses back into error codes. Compare against the previous version (regression).
- [VERIFIED-DOC] The ROBO Pro Coding debug window supports only single-threaded programs. [VERIFIED-DOC] SofTXT (`github.com/harbaum/SofTXT`) runs ROBO Pro Coding projects against a PC with an optional ftDuino, and shows how the Python API is mocked. Its semantics are not identical to the real firmware (e.g. its `set_speed` handling and ultrasonic are incomplete).

---
