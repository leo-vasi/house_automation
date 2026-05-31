# main.py - Sistema IoT Residencial com Relays
import time, network, json

print("="*40)
print("[BOOT] Casa Inteligente IoT")
print("="*40)

def boot_import(name):
    try:
        mod = __import__(name)
        print("[BOOT] {} OK".format(name))
        return mod
    except Exception as e:
        print("[BOOT] ERRO {}: {}".format(name, e))
        raise

config      = boot_import("config")
sensors     = boot_import("sensors")
actuators   = boot_import("actuators")
mqtt_client = boot_import("mqtt_client")
web_server  = boot_import("web_server")

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("[WiFi] Ja conectado:", wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    print("[WiFi] Conectando...")
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for i in range(20):
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print("[WiFi] Conectado! IP:", ip)
            return ip
        print("  {}/20".format(i+1))
        time.sleep(1)
    print("[WiFi] FALHA!")
    return None

def setup():
    actuators.all_relays_off()
    actuators.set_servo(0)
    try:
        actuators.oled_message("Iniciando...\nCasa IoT\nESP32")
    except Exception as e:
        print("[SETUP] OLED:", e)

    ip = connect_wifi()
    if ip:
        try:
            mqtt_client.connect()
            actuators.oled_message("WiFi OK!\n{}\nMQTT OK!".format(ip))
        except Exception as e:
            print("[SETUP] MQTT:", e)
            actuators.oled_message("MQTT ERRO")
    else:
        actuators.oled_message("Sem WiFi\nModo local")

    try:
        web_server.start()
    except Exception as e:
        print("[SETUP] Web:", e)

    print("[SETUP] Pronto!\n")

SENSOR_INTERVAL  = 5
PUBLISH_INTERVAL = 10
_t_sensor  = 0
_t_publish = 0
_data      = {}
_alerts    = []

def loop():
    global _t_sensor, _t_publish, _data, _alerts
    now = time.time()

    if now - _t_sensor >= SENSOR_INTERVAL:
        _t_sensor = now
        try:
            _data   = sensors.read_all()
            _alerts = sensors.check_alerts(_data)
            actuators.oled_show_status(_data, _alerts)
            web_server.update_state(_data, _alerts)

            print("[SENS] T={:.1f}C H={:.1f}% LDR={} GAS={:.1f}% PIR={}".format(
                _data["temperature"], _data["humidity"],
                _data["ldr"], _data["gas"], _data["motion"]))
            if _alerts:
                print("[ALRT]", _alerts)

            # ── Automação: sensor -> relay ─────────────────────────────────
            # Relay 1: LDR escuro (valor baixo) -> liga luzes
            escuro = _data["ldr"] < config.LDR_MIN
            actuators.set_relay(0, escuro)
            print("[LDR] valor={} limiar={} escuro={}".format(_data["ldr"], config.LDR_MIN, escuro))
            # Relay 2: PIR movimento -> liga alarme
            actuators.set_relay(1, _data["motion"])
            # Relay 3: Gás alto -> liga exaustor
            actuators.set_relay(2, _data["gas"] >= config.GAS_MAX)
            # Relay 4: Temp alta -> liga ar-condicionado
            actuators.set_relay(3, _data["temperature"] >= config.TEMP_MAX)

            # Publica estado dos relays via MQTT
            for i, topic in enumerate((
                config.TOPIC_RELAY1, config.TOPIC_RELAY2,
                config.TOPIC_RELAY3, config.TOPIC_RELAY4)):
                try:
                    mqtt_client.publish(topic,
                        "on" if actuators.get_relay_state(i) else "off")
                except: pass

        except Exception as e:
            print("[SENS] Erro:", e)

    if now - _t_publish >= PUBLISH_INTERVAL and _data:
        _t_publish = now
        try:
            mqtt_client.publish(config.TOPIC_SENSORS, json.dumps({
                "temperature": _data.get("temperature", 0),
                "humidity":    _data.get("humidity", 0),
                "ldr":         _data.get("ldr", 0),
                "gas":         _data.get("gas", 0),
                "motion":      1 if _data.get("motion") else 0,
                "relay1":      1 if actuators.get_relay_state(0) else 0,
                "relay2":      1 if actuators.get_relay_state(1) else 0,
                "relay3":      1 if actuators.get_relay_state(2) else 0,
                "relay4":      1 if actuators.get_relay_state(3) else 0,
                "servo":       actuators.get_servo_angle(),
            }))
            if _alerts:
                mqtt_client.publish(config.TOPIC_ALERTS,
                    json.dumps({"alerts": _alerts}))
            print("[MQTT] Publicado")
        except Exception as e:
            print("[MQTT] Erro:", e)

    try: mqtt_client.check_messages()
    except: pass
    try: web_server.handle_requests()
    except: pass

    time.sleep(0.1)

try:
    setup()
    while True:
        loop()
except KeyboardInterrupt:
    print("[MAIN] Parado.")
except Exception as e:
    import sys
    sys.print_exception(e)
    time.sleep(5)
    import machine; machine.reset()