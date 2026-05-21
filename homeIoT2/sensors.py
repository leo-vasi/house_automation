# sensors.py — Leitura dos 4 sensores
import machine
import dht
import config

# ── Inicialização dos sensores ────────────────────────────────────────────────
_dht  = dht.DHT22(machine.Pin(config.PIN_DHT22))
_ldr  = machine.ADC(machine.Pin(config.PIN_LDR))
_pir  = machine.Pin(config.PIN_PIR, machine.Pin.IN)
_mq2  = machine.ADC(machine.Pin(config.PIN_MQ2))

# Configura ADC: atenuação 11dB → leitura até 3.3V (0–4095)
_ldr.atten(machine.ADC.ATTN_11DB)
_mq2.atten(machine.ADC.ATTN_11DB)

def read_dht22():
    """Retorna (temperatura_C, umidade_%) ou (None, None) em caso de erro."""
    try:
        _dht.measure()
        return _dht.temperature(), _dht.humidity()
    except OSError:
        return None, None

def read_ldr():
    """Retorna valor ADC bruto 0–4095. Valores baixos = mais luz."""
    return _ldr.read()

def read_pir():
    """Retorna True se detectou movimento, False caso contrário."""
    return bool(_pir.value())

def read_mq2():
    """Retorna concentração simulada em % (0–100) baseada no ADC 0–4095."""
    raw = _mq2.read()
    return round((raw / 4095) * 100, 1)

def read_all():
    """Retorna dicionário com todos os sensores."""
    temp, hum = read_dht22()
    return {
        "temperature": temp if temp is not None else 0.0,
        "humidity":    hum  if hum  is not None else 0.0,
        "ldr":         read_ldr(),
        "motion":      read_pir(),
        "gas":         read_mq2(),
    }

def check_alerts(data):
    """
    Verifica limites e retorna lista de strings de alerta.
    Lista vazia = sem alertas.
    """
    alerts = []
    if data["temperature"] >= config.TEMP_MAX:
        alerts.append(f"TEMP_HIGH:{data['temperature']:.1f}C")
    if data["humidity"] >= config.HUMIDITY_MAX:
        alerts.append(f"HUM_HIGH:{data['humidity']:.1f}%")
    if data["gas"] >= config.GAS_MAX:
        alerts.append(f"GAS_HIGH:{data['gas']:.1f}%")
    if data["ldr"] <= config.LDR_MIN:
        alerts.append(f"LOW_LIGHT:{data['ldr']}")
    if data["motion"]:
        alerts.append("MOTION_DETECTED")
    return alerts
