# actuators.py - 4 Relays + Servo + OLED
import machine, config
import ssd1306

# ── RELAYS ────────────────────────────────────────────────────────────────────
# wokwi-relay-module: IN=LOW  -> relay ATIVADO (LED acende, bobina energizada)
#                     IN=HIGH -> relay DESATIVADO
_r1 = machine.Pin(config.PIN_RELAY1, machine.Pin.OUT, value=1)  # inicia OFF
_r2 = machine.Pin(config.PIN_RELAY2, machine.Pin.OUT, value=1)
_r3 = machine.Pin(config.PIN_RELAY3, machine.Pin.OUT, value=1)
_r4 = machine.Pin(config.PIN_RELAY4, machine.Pin.OUT, value=1)

_relays = [_r1, _r2, _r3, _r4]
_states  = [False, False, False, False]

_nomes = [
    "Luzes do Andar",
    "Alarme Sonoro",
    "Exaustor Gas",
    "Ar-Condicionado",
]

def set_relay(n, state):
    """n = 0..3 | state = True (ON) / False (OFF)"""
    _states[n] = bool(state)
    # Relay ativo com LOW
    _relays[n].value(0 if state else 1)
    print("[RELAY{}] {} = {}".format(n+1, _nomes[n], "ON" if state else "OFF"))

def relay_from_str(n, cmd):
    set_relay(n, cmd.strip().lower() in ("on", "1", "true", "activate"))

def get_relay_state(n):
    return _states[n]

def all_relays_off():
    for i in range(4):
        set_relay(i, False)

# ── SERVO ─────────────────────────────────────────────────────────────────────
_servo = machine.PWM(machine.Pin(config.PIN_SERVO), freq=50)
_servo_angle = 0

def set_servo(angle):
    global _servo_angle
    angle = max(0, min(180, int(angle)))
    _servo_angle = angle
    us = 600 + (angle / 180) * 1800
    _servo.duty(int((us / 20000) * 1023))

def get_servo_angle():
    return _servo_angle

def servo_from_str(cmd):
    cmd = cmd.strip().lower()
    if cmd == "open":    set_servo(180)
    elif cmd == "close": set_servo(0)
    elif cmd == "half":  set_servo(90)
    else:
        try: set_servo(int(cmd))
        except: set_servo(0)

# ── OLED ──────────────────────────────────────────────────────────────────────
_i2c  = machine.I2C(0,
    sda=machine.Pin(config.PIN_OLED_SDA),
    scl=machine.Pin(config.PIN_OLED_SCL),
    freq=400000)
_oled = ssd1306.SSD1306_I2C(128, 64, _i2c, addr=0x3c)

def oled_show_status(data, alerts):
    _oled.fill(0)
    _oled.text("T:{:.1f}C H:{:.0f}%".format(
        data["temperature"], data["humidity"]), 0, 0)
    _oled.text("LDR:{} GAS:{:.0f}%".format(
        data["ldr"], data["gas"]), 0, 10)
    _oled.text("PIR:{}".format("SIM" if data["motion"] else "NAO"), 0, 20)
    _oled.text("R1:{} R2:{} R3:{} R4:{}".format(
        "ON" if _states[0] else "--",
        "ON" if _states[1] else "--",
        "ON" if _states[2] else "--",
        "ON" if _states[3] else "--"), 0, 30)
    if alerts:
        _oled.text(alerts[0][:16], 0, 44)
        if len(alerts) > 1:
            _oled.text(alerts[1][:16], 0, 54)
    else:
        _oled.text("Status: OK", 0, 48)
    _oled.show()

def oled_message(msg):
    _oled.fill(0)
    for i, line in enumerate(msg.split("\n")[:5]):
        _oled.text(line[:16], 0, i * 12)
    _oled.show()