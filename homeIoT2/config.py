# config.py — Configurações centrais do projeto
# Altere apenas este arquivo para adaptar ao seu ambiente

# ── Wi-Fi (Wokwi fornece rede virtual automaticamente) ──────────────────────
WIFI_SSID     = "Wokwi-GUEST"
WIFI_PASSWORD = ""

# ── MQTT Broker ─────────────────────────────────────────────────────────────
MQTT_BROKER   = "broker.hivemq.com"
MQTT_PORT     = 1883          # 1883 = sem TLS (público)
MQTT_CLIENT_ID = "esp32_home_iot_001"
MQTT_USER     = ""            # HiveMQ público não exige
MQTT_PASSWORD = ""

# ── Tópicos MQTT ─────────────────────────────────────────────────────────────
TOPIC_SENSORS    = b"home/sensors"
TOPIC_ALERTS     = b"home/alerts"
TOPIC_STATUS     = b"home/status"

# Atuadores — subscribe (recebe comandos)
TOPIC_RGB        = b"home/actuators/rgb"
TOPIC_SERVO      = b"home/actuators/servo"
TOPIC_ALARM      = b"home/actuators/alarm"
TOPIC_OLED       = b"home/actuators/oled"

# ── Pinos GPIO ───────────────────────────────────────────────────────────────
PIN_DHT22     = 4
PIN_LDR       = 34
PIN_PIR       = 35
PIN_MQ2       = 32

PIN_RGB_R     = 25
PIN_RGB_G     = 26
PIN_RGB_B     = 27
PIN_SERVO     = 18
PIN_ALARM_LED = 23
PIN_OLED_SDA  = 21
PIN_OLED_SCL  = 22

# ── Limites para alertas ─────────────────────────────────────────────────────
TEMP_MAX      = 35.0   # °C
HUMIDITY_MAX  = 80.0   # %
GAS_MAX       = 60.0   # % da escala (potenciômetro MQ-2 simulado)
LDR_MIN       = 200    # valor ADC mínimo (muito escuro → acende luz)