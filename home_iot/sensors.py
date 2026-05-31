# sensors.py - 4 sensores: LDR, DHT22, PIR, Gas
import machine, dht, config

_ldr = machine.ADC(machine.Pin(config.PIN_LDR))
_ldr.atten(machine.ADC.ATTN_11DB)

_dht = dht.DHT22(machine.Pin(config.PIN_DHT))

_pir = machine.Pin(config.PIN_PIR, machine.Pin.IN)

_gas = machine.ADC(machine.Pin(config.PIN_GAS))
_gas.atten(machine.ADC.ATTN_11DB)

def read_all():
    temp, hum = 0.0, 0.0
    try:
        _dht.measure()
        temp = _dht.temperature()
        hum  = _dht.humidity()
    except: pass

    return {
        "temperature": temp,
        "humidity":    hum,
        "ldr":         _ldr.read(),
        "motion":      bool(_pir.value()),
        "gas":         round((_gas.read() / 4095) * 100, 1),
    }

def check_alerts(d):
    alerts = []
    if d["ldr"] <= config.LDR_MIN:
        alerts.append("POUCA_LUZ:{}".format(d["ldr"]))
    if d["motion"]:
        alerts.append("MOVIMENTO_DETECTADO")
    if d["gas"] >= config.GAS_MAX:
        alerts.append("GAS_ALTO:{:.1f}%".format(d["gas"]))
    if d["temperature"] >= config.TEMP_MAX:
        alerts.append("TEMP_ALTA:{:.1f}C".format(d["temperature"]))
    return alerts