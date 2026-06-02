# main.py — Ponto de entrada principal do sistema IoT residencial
# ESP32 + MicroPython | Wokwi Simulator
import time
import network
import json

print("=" * 40)
print("[BOOT] Iniciando Casa Inteligente IoT")
print("=" * 40)

# ── Importa módulos do projeto com tratamento de erro ─────────────────────────
try:
    import config
    print("[BOOT] config.py OK")
except Exception as e:
    print(f"[ERRO] config.py: {e}")
    raise

try:
    import sensors
    print("[BOOT] sensors.py OK")
except Exception as e:
    print(f"[ERRO] sensors.py: {e}")
    raise

try:
    import actuators
    print("[BOOT] actuators.py OK")
except Exception as e:
    print(f"[ERRO] actuators.py: {e}")
    raise

try:
    import mqtt_client
    print("[BOOT] mqtt_client.py OK")
except Exception as e:
    print(f"[ERRO] mqtt_client.py: {e}")
    raise

try:
    import web_server
    print("[BOOT] web_server.py OK")
except Exception as e:
    print(f"[ERRO] web_server.py: {e}")
    raise

print("[BOOT] Todos os módulos carregados!")

# ── 1. Conexão Wi-Fi ──────────────────────────────────────────────────────────
def connect_wifi():
    print(f"\n[WiFi] Conectando a '{config.WIFI_SSID}'...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"[WiFi] Já conectado! IP: {ip}")
        return ip
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for i in range(20):
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print(f"\n[WiFi] Conectado! IP: {ip}")
            return ip
        print(f"  Aguardando... {i+1}/20")
        time.sleep(1)
    print("[WiFi] FALHA na conexão!")
    return None

# ── 2. Inicialização ──────────────────────────────────────────────────────────
def setup():
    try:
        actuators.oled_message("Iniciando...\nCasa IoT\nESP32")
        print("[SETUP] OLED OK")
    except Exception as e:
        print(f"[SETUP] OLED erro: {e}")

    try:
        actuators.set_rgb(0, 100, 0)
        time.sleep(0.3)
        actuators.set_rgb(0, 0, 100)
        time.sleep(0.3)
        actuators.rgb_off()
        actuators.set_servo(0)
        actuators.set_alarm(False)
        print("[SETUP] Atuadores OK")
    except Exception as e:
        print(f"[SETUP] Atuadores erro: {e}")

    ip = connect_wifi()

    if ip:
        try:
            actuators.oled_message(f"WiFi OK\n{ip}\nMQTT...")
            mqtt_client.connect()
            print("[SETUP] MQTT conectado!")
            actuators.oled_message("MQTT OK!\nSistema\nPronto!")
        except Exception as e:
            print(f"[SETUP] MQTT erro: {e}")
            actuators.oled_message(f"MQTT ERRO\n{str(e)[:14]}")
    else:
        print("[SETUP] Sem WiFi — MQTT ignorado")
        actuators.oled_message("Sem WiFi\nModo local\nAtivo")

    try:
        web_server.start()
        print("[SETUP] Servidor web iniciado na porta 80")
    except Exception as e:
        print(f"[SETUP] Web server erro: {e}")

    print("\n[SETUP] === Sistema pronto! ===\n")

# ── 3. Loop principal ─────────────────────────────────────────────────────────
SENSOR_INTERVAL  = 5
PUBLISH_INTERVAL = 10

_last_sensor  = 0
_last_publish = 0
_sensor_data  = {}
_active_alerts = []

def loop():
    global _last_sensor, _last_publish, _sensor_data, _active_alerts

    now = time.time()

    if now - _last_sensor >= SENSOR_INTERVAL:
        _last_sensor = now
        try:
            _sensor_data = sensors.read_all()
            _active_alerts = sensors.check_alerts(_sensor_data)

            print(f"[SENS] T={_sensor_data['temperature']:.1f}C "
                  f"H={_sensor_data['humidity']:.1f}% "
                  f"LDR={_sensor_data['ldr']} "
                  f"GAS={_sensor_data['gas']:.1f}% "
                  f"PIR={_sensor_data['motion']}")

            if _active_alerts:
                print(f"[ALRT] {_active_alerts}")

            actuators.oled_show_status(_sensor_data, _active_alerts)
            web_server.update_state(_sensor_data, _active_alerts)

            if any("GAS_HIGH" in a for a in _active_alerts):
                if not actuators.get_alarm_state():
                    actuators.set_alarm(True)
                    print("[AUTO] Alarme ativado por gas alto!")
                    try:
                        mqtt_client.publish(config.TOPIC_ALARM, "on")
                    except:
                        pass

            if _sensor_data["ldr"] <= config.LDR_MIN:
                actuators.set_rgb(255, 200, 0)

        except Exception as e:
            print(f"[ERRO] Leitura sensores: {e}")

    if now - _last_publish >= PUBLISH_INTERVAL and _sensor_data:
        _last_publish = now
        try:
            payload = json.dumps({
                "temperature": _sensor_data.get("temperature", 0),
                "humidity":    _sensor_data.get("humidity", 0),
                "ldr":         _sensor_data.get("ldr", 0),
                "gas":         _sensor_data.get("gas", 0),
                "motion":      1 if _sensor_data.get("motion") else 0,
                "alarm":       1 if actuators.get_alarm_state() else 0,
                "servo":       actuators.get_servo_angle(),
            })
            mqtt_client.publish(config.TOPIC_SENSORS, payload)
            if _active_alerts:
                mqtt_client.publish(config.TOPIC_ALERTS,
                                    json.dumps({"alerts": _active_alerts}))
            print(f"[MQTT] Publicado OK")
        except Exception as e:
            print(f"[MQTT] Erro ao publicar: {e}")

    try:
        mqtt_client.check_messages()
    except Exception as e:
        print(f"[MQTT] Erro check_msg: {e}")

    try:
        web_server.handle_requests()
    except Exception as e:
        print(f"[WEB] Erro: {e}")

    time.sleep(0.1)

# ── 4. Entry point ────────────────────────────────────────────────────────────
try:
    setup()
    while True:
        loop()
except KeyboardInterrupt:
    print("\n[MAIN] Interrompido.")
except Exception as e:
    import sys
    print(f"\n[MAIN] ERRO CRITICO: {e}")
    sys.print_exception(e)
    print("Reiniciando em 5s...")
    time.sleep(5)
    import machine
    machine.reset()