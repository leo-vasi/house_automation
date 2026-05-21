# actuators.py — Controle dos 4 atuadores
import machine
import time
import config

# ── LED RGB ───────────────────────────────────────────────────────────────────
_rgb_r = machine.PWM(machine.Pin(config.PIN_RGB_R), freq=1000)
_rgb_g = machine.PWM(machine.Pin(config.PIN_RGB_G), freq=1000)
_rgb_b = machine.PWM(machine.Pin(config.PIN_RGB_B), freq=1000)

def _duty(val):
    """Converte 0-255 em duty cycle 0-1023."""
    return int((val / 255) * 1023)

def set_rgb(r, g, b):
    """Define cor do LED RGB. Valores 0–255 para cada canal."""
    _rgb_r.duty(_duty(r))
    _rgb_g.duty(_duty(g))
    _rgb_b.duty(_duty(b))

def rgb_off():
    set_rgb(0, 0, 0)

def rgb_from_str(cmd):
    """
    Interpreta comando string para o RGB.
    Exemplos: "on", "off", "red", "green", "blue", "white", "255,128,0"
    """
    cmd = cmd.strip().lower()
    presets = {
        "on":     (255, 255, 255),
        "off":    (0,   0,   0),
        "red":    (255, 0,   0),
        "green":  (0,   255, 0),
        "blue":   (0,   0,   255),
        "white":  (255, 255, 255),
        "yellow": (255, 200, 0),
        "purple": (128, 0,   128),
    }
    if cmd in presets:
        set_rgb(*presets[cmd])
    elif "," in cmd:
        try:
            r, g, b = [int(x) for x in cmd.split(",")]
            set_rgb(r, g, b)
        except:
            rgb_off()
    else:
        rgb_off()


# ── SERVO MOTOR ───────────────────────────────────────────────────────────────
_servo = machine.PWM(machine.Pin(config.PIN_SERVO), freq=50)

def _angle_to_duty(angle):
    """Converte ângulo 0–180 em duty cycle para servo (600–2400µs)."""
    min_us = 600
    max_us = 2400
    us = min_us + (angle / 180) * (max_us - min_us)
    duty = int((us / 20000) * 1023)
    return duty

_servo_angle = 0

def set_servo(angle):
    """Move servo para ângulo especificado (0–180°)."""
    global _servo_angle
    angle = max(0, min(180, int(angle)))
    _servo_angle = angle
    _servo.duty(_angle_to_duty(angle))

def get_servo_angle():
    return _servo_angle

def servo_from_str(cmd):
    """
    Interpreta comando string para o servo.
    Exemplos: "open" (180°), "close" (0°), "half" (90°), "45"
    """
    cmd = cmd.strip().lower()
    if cmd == "open":
        set_servo(180)
    elif cmd == "close":
        set_servo(0)
    elif cmd == "half":
        set_servo(90)
    else:
        try:
            set_servo(int(cmd))
        except:
            set_servo(0)


# ── LED DE ALARME ─────────────────────────────────────────────────────────────
_alarm = machine.Pin(config.PIN_ALARM_LED, machine.Pin.OUT)
_alarm_state = False

def set_alarm(state: bool):
    global _alarm_state
    _alarm_state = state
    _alarm.value(1 if state else 0)

def alarm_from_str(cmd):
    cmd = cmd.strip().lower()
    if cmd in ("on", "1", "true", "activate"):
        set_alarm(True)
    else:
        set_alarm(False)

def get_alarm_state():
    return _alarm_state


# ── DISPLAY OLED ──────────────────────────────────────────────────────────────
from machine import I2C
import ssd1306

_i2c  = I2C(0, sda=machine.Pin(config.PIN_OLED_SDA),
               scl=machine.Pin(config.PIN_OLED_SCL), freq=400000)
_oled = ssd1306.SSD1306_I2C(128, 64, _i2c, addr=0x3c)

def oled_show_status(data, alerts):
    """
    Exibe no OLED:
      Linha 0: Temp e Umidade
      Linha 1: Luminosidade e Gás
      Linha 2: Movimento
      Linha 3: Servo e Alarme
      Linha 4-5: Alertas (se houver)
    """
    _oled.fill(0)
    _oled.text(f"T:{data['temperature']:.1f}C H:{data['humidity']:.0f}%", 0, 0)
    _oled.text(f"LDR:{data['ldr']} GS:{data['gas']:.0f}%",               0, 10)
    _oled.text(f"MOV:{'SIM' if data['motion'] else 'NAO'}",               0, 20)
    _oled.text(f"SRV:{get_servo_angle()}  ALM:{'ON' if get_alarm_state() else 'OFF'}", 0, 30)

    if alerts:
        _oled.text("! " + alerts[0][:14], 0, 42)
        if len(alerts) > 1:
            _oled.text("! " + alerts[1][:14], 0, 52)
    else:
        _oled.text("Status: OK", 0, 48)

    _oled.show()

def oled_message(msg):
    """Exibe mensagem livre no OLED (máx 4 linhas de 16 chars)."""
    _oled.fill(0)
    lines = msg.split("\n")
    for i, line in enumerate(lines[:5]):
        _oled.text(line[:16], 0, i * 12)
    _oled.show()
