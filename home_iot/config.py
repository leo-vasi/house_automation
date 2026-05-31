# config.py - Configurações centrais do projeto

WIFI_SSID     = "Wokwi-GUEST"
WIFI_PASSWORD = ""

MQTT_BROKER    = "broker.hivemq.com"
MQTT_PORT      = 1883
MQTT_CLIENT_ID = "11232100617_esp32"
MQTT_USER      = ""
MQTT_PASSWORD  = ""

TOPIC_SENSORS = b"11232100617/home/sensors"
TOPIC_ALERTS  = b"11232100617/home/alerts"
TOPIC_RELAY1  = b"11232100617/home/actuators/relay1"  # LDR  -> luzes do andar
TOPIC_RELAY2  = b"11232100617/home/actuators/relay2"  # PIR  -> alarme sonoro
TOPIC_RELAY3  = b"11232100617/home/actuators/relay3"  # GAS  -> exaustor
TOPIC_RELAY4  = b"11232100617/home/actuators/relay4"  # TEMP -> ar-condicionado
TOPIC_SERVO   = b"11232100617/home/actuators/servo"
TOPIC_OLED    = b"11232100617/home/actuators/oled"

# Sensores
PIN_LDR  = 33
PIN_DHT  = 5
PIN_PIR  = 35
PIN_GAS  = 32

# Relays (IN = LOW ativa, HIGH desativa no wokwi-relay-module)
PIN_RELAY1 = 18   # Luzes do andar    (LDR)
PIN_RELAY2 = 19   # Alarme sonoro     (PIR)
PIN_RELAY3 = 16   # Exaustor          (GAS)
PIN_RELAY4 = 17   # Ar-condicionado   (TEMP)

# Servo e OLED
PIN_SERVO    = 26
PIN_OLED_SDA = 21
PIN_OLED_SCL = 22

# Limites para acionamento automático
TEMP_MAX = 35.0   # °C  -> liga ar-condicionado
GAS_MAX  = 60.0   # %   -> liga exaustor
LDR_MIN  = 1000   # ADC -> liga luzes quando valor < 1000 (escuro)