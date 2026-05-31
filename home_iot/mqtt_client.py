# mqtt_client.py - MQTT publish/subscribe
from umqtt.simple import MQTTClient
import config, actuators

_client = None

def _callback(topic, msg):
    cmd = msg.decode().strip()
    print("[MQTT] {} -> {}".format(topic, cmd))
    if   topic == config.TOPIC_RELAY1: actuators.relay_from_str(0, cmd)
    elif topic == config.TOPIC_RELAY2: actuators.relay_from_str(1, cmd)
    elif topic == config.TOPIC_RELAY3: actuators.relay_from_str(2, cmd)
    elif topic == config.TOPIC_RELAY4: actuators.relay_from_str(3, cmd)
    elif topic == config.TOPIC_SERVO:  actuators.servo_from_str(cmd)
    elif topic == config.TOPIC_OLED:   actuators.oled_message(cmd)

def connect():
    global _client
    _client = MQTTClient(
        config.MQTT_CLIENT_ID,
        config.MQTT_BROKER,
        port=config.MQTT_PORT,
        keepalive=60)
    _client.set_callback(_callback)
    _client.connect()
    for t in (config.TOPIC_RELAY1, config.TOPIC_RELAY2,
              config.TOPIC_RELAY3, config.TOPIC_RELAY4,
              config.TOPIC_SERVO,  config.TOPIC_OLED):
        _client.subscribe(t)
    print("[MQTT] Conectado!")

def publish(topic, payload):
    global _client
    try:
        if isinstance(payload, str):
            payload = payload.encode()
        _client.publish(topic, payload)
    except Exception as e:
        print("[MQTT] Erro publish:", e)
        try: connect()
        except: pass

def check_messages():
    global _client
    try:
        _client.check_msg()
    except Exception as e:
        print("[MQTT] Erro check:", e)
        try: connect()
        except: pass