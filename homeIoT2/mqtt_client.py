# mqtt_client.py — Gerenciamento da conexão MQTT
from umqtt.simple import MQTTClient
import config
import actuators

_client = None
_on_message_cb = None

def _internal_callback(topic, msg):
    """Callback interno: despacha para o atuador correto."""
    cmd = msg.decode().strip()
    print(f"[MQTT] {topic} → {cmd}")

    if topic == config.TOPIC_RGB:
        actuators.rgb_from_str(cmd)
    elif topic == config.TOPIC_SERVO:
        actuators.servo_from_str(cmd)
    elif topic == config.TOPIC_ALARM:
        actuators.alarm_from_str(cmd)
    elif topic == config.TOPIC_OLED:
        actuators.oled_message(cmd)

    # Repassa para callback externo se definido
    if _on_message_cb:
        _on_message_cb(topic, msg)

def connect(on_message=None):
    """Conecta ao broker e faz subscribe nos tópicos de atuadores."""
    global _client, _on_message_cb
    _on_message_cb = on_message

    _client = MQTTClient(
        client_id=config.MQTT_CLIENT_ID,
        server=config.MQTT_BROKER,
        port=config.MQTT_PORT,
        user=config.MQTT_USER or None,
        password=config.MQTT_PASSWORD or None,
        keepalive=60,
    )
    _client.set_callback(_internal_callback)
    _client.connect()

    # Subscribe em todos os tópicos de atuadores
    for topic in (config.TOPIC_RGB, config.TOPIC_SERVO,
                  config.TOPIC_ALARM, config.TOPIC_OLED):
        _client.subscribe(topic)
        print(f"[MQTT] Subscrito: {topic}")

    print(f"[MQTT] Conectado em {config.MQTT_BROKER}")
    return _client

def publish(topic, payload):
    """Publica mensagem. Reconecta se necessário."""
    global _client
    try:
        _client.publish(topic, payload.encode() if isinstance(payload, str) else payload)
    except Exception as e:
        print(f"[MQTT] Erro ao publicar: {e}. Reconectando...")
        connect(_on_message_cb)
        _client.publish(topic, payload.encode() if isinstance(payload, str) else payload)

def check_messages():
    """Verifica mensagens pendentes (non-blocking)."""
    global _client
    try:
        _client.check_msg()
    except Exception as e:
        print(f"[MQTT] Erro check_msg: {e}. Reconectando...")
        connect(_on_message_cb)
