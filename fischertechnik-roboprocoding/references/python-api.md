# Python API (fischertechnik package) per device family

## 5. Python API reference (all controller families)

The Python package is `fischertechnik` (imported as `fischertechnik.factories`), preinstalled on the controller. It is not on PyPI. Do not `pip install` it for the controller. For a PC simulation, the SofTXT project re-implements parts of it (section 10).

Constructors: `<factory>.<input|output|motor|i2c>_factory.create_<type>(controller, port)`. `port` is an integer. For ports with counters/servos the numbering is [UNKNOWN].

### 5.1 Outputs (`output_factory`)
Value range for every analog output: **0..512** (stored/clamped as int). **Never exceed 512** [VERIFIED-DOC, VERIFIED-RUN].

| Create call | Methods | Notes |
|---|---|---|
| `create_unidirectional_motor(c, port)` | `set_speed(0..512)`, `get_speed()`, `is_running()`, `stop()` | [VERIFIED-FILE + DOC]. Output pair used as single-direction motor. `set_speed(int(...))` is how Blockly generates it. |
| `create_magnetic_valve(c, port)` | `on()`, `off()`, `is_on()`, `is_off()` | [VERIFIED-FILE + DOC]. "on" = energised (a pneumatic cylinder with return spring is extended while on). |
| `create_compressor(c, port)` | `on()`, `off()`, `is_on()`, `is_off()` | [VERIFIED-FILE + DOC]. |
| `create_led(c, port)` | `on()`, `off()`, `set_brightness(0..512)`, `get_brightness()` | `on/off` verified in Blockly output; brightness from docs. LEDs/lamps are driven on an output. |

Blockly output docs [VERIFIED-DOC]: motors `set motor speed to []` (0-512, direction dropdown), `get motor speed`, `if motor is running`, `stop motor` (stop immediately or coast); LEDs `set LED on/off`, `set LED brightness` (0-512), `get LED brightness`, `is LED ...`; solenoid valve `set solenoid valve on/off`; compressor `set compressor on/off`.

### 5.2 Motors and encoder motors (`motor_factory`) [VERIFIED-DOC for blocks, SofTXT for API shape]
- Direct control: direction CW/CCW (`Motor.CW`, `Motor.CCW`) plus speed 0..512 (PWM). Reversing is done with direction or a negative value.
- Encoder motor (Art. 186175 / 153422, with the Impuls-Zahnrad 4): all standard motor functions plus step counting. About **64 pulses (63.9) per revolution**. Blocks: set speed + direction + steps, synchronised control of several motors (up to 4 motors, M1+M2 synchronised by firmware), stop, "has motor reached position".
- Synchronised calls repeated quickly in a loop can reduce synchronicity or prevent it.
- SofTXT's API: `create_motor(c, port)`, `create_encodermotor(c, port)`, with `set_speed(val, dir)`, `start()`, `stop()` (brake), `coast()` (open). Treat as a hint, not as the real signatures [INFERRED]. Check a sample file.
- Encoder as counter: the encoder motor counts revolutions whether driven or turned by hand. Blocks: get counter value, compare counter, reset counter (to 0).

### 5.3 Servos (TXT 4.0: S1..S3) [VERIFIED-DOC]
- Set position 0..512 (0 = full left, 256 = centre, 512 = full right), roughly -90°..+90°. Get position.
- No feedback: a blocked servo draws too much current. Calibrate min/mid/max pulse widths in the controller menu (Settings > Servo).

### 5.4 Digital and analog inputs (`input_factory`)
| Create call | Methods | Meaning |
|---|---|---|
| `create_mini_switch(c, port)` | `is_open()`, `is_closed()`, `get_state()` | Mini button, reed contact (same call), or any contact. [VERIFIED-FILE + DOC] |
| `create_photo_transistor(c, port)` | `is_bright()`, `is_dark()`, `get_state()` | Digital light. |
| `create_trail_follower(c, port)` | `get_state()` -> 0 no track / 1 track | IR track sensor, works at about 5-30 mm. Uses two inputs. |
| `create_photo_resistor(c, port)` | `get_resistance()` | Resistance falls with more light. |
| `create_ntc_resistor(c, port)` | `get_resistance()`, `get_temperature()` | Resistance falls with temperature. SofTXT uses B=3900, 1500 ohm at 25 C. |
| `create_color_sensor(c, port)` | `get_voltage()` | Analog; Blockly shows reflected red light, 0-2000. |
| `create_ultrasonic_distance_meter(c, port)` | `get_distance()` | Blockly says cm; the RX Python reference says a 0..1024 value. |

Button wiring [VERIFIED-DOC]: contacts 1-3 are normally open (current flows when pressed). Contacts 1-2 are normally closed. For an input that is normally open, `is_closed()` means "pressed / activated". This was relied on in the working project: I5 was a normally-open button and `is_closed()` meant pressed [VERIFIED-RUN].

Digital inputs on the RX are read as a state (`is_open` / `is_closed`). They are polled (no interrupts). Poll every cycle and detect edges yourself (keep a `*_prev` variable), because a chain of short `await`s still gives about 10 ms resolution.

Blockly input blocks [VERIFIED-DOC]: get/ask mini button status, ultrasonic distance, colour value, IR track status, phototransistor status, photoresistor value, NTC resistance or temperature, each with a query block (`<, <=, =, !=, >=, >`).

### 5.5 I2C sensors (`i2c_factory`) [VERIFIED-DOC]
`create_gesture_sensor(c, port)`, `create_environment_sensor(c, port)`, `create_combined_sensor(c, port)`:
- Gesture / RGB: `enable_gesture() / get_gesture() / disable_gesture()`; `enable_light() / get_rgb() / get_hex() / get_hsv() / disable_light()` (also `get_rgb_red/green/blue`, `get_rgb_hsv_hue/saturation/value`); `get_ambient()`; `enable_proximity() / get_proximity() (0..255) / disable_proximity()`.
- Environment (BME680): `get_temperature()` (C), `get_humidity()` (%), `get_pressure()` (hPa), `get_indoor_air_quality_as_number()` (0..500), `get_indoor_air_quality_as_text()`, `calibrate()`, `needs_calibration()`.
- Combined (accelerometer, magnetometer, gyro): `init_accelerometer(range, bandwidth, high_res)`, `init_magnetometer(data_rate)`, `init_gyrometer(range, bandwidth, high_res)`, then `get_acceleration_x/y/z()` (g), `get_magnetic_field_x/y/z()` (uT), `get_rotation_x/y/z()` (deg/s). The "compensation"/`high_res` parameter applies only to the 10-pin version, not the 6-pin.
- RGB colour sensor (Blockly, up to 8 chained): measurement time, LED auto-off, LED brightness 0..255, value as HEX / RGB / HSV / white.
- I2C runs at 3.3 V.

### 5.6 Other functions in Blockly [VERIFIED-DOC]
Categories: General; Actuators (Outputs, Engine, Sound, Display); Sensors (Input, Counter, I2C, USB); Processing (Logic, Loops, Mathematics, Text, File, Data structures, Util, Variables, Functions, Machine Learning, Imports); Communication (Voice Control, Cloud / MQTT). Special blocks: **"python imports"** (adds imports at the top of the generated file) and **"python code"** (raw Python inline, indentation matters).

---
