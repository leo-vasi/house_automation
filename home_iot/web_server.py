import socket, json
import actuators, mqtt_client, config

_state = {}

def update_state(data, alerts):
    global _state
    _state = {
        "temperature": data.get("temperature", 0),
        "humidity":    data.get("humidity", 0),
        "ldr":         data.get("ldr", 0),
        "gas":         data.get("gas", 0),
        "motion":      data.get("motion", False),
        "alerts":      alerts,
        "relay1":      actuators.get_relay_state(0),
        "relay2":      actuators.get_relay_state(1),
        "relay3":      actuators.get_relay_state(2),
        "relay4":      actuators.get_relay_state(3),
        "servo":       actuators.get_servo_angle(),
    }

_HTML = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Casa Inteligente</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f172a;color:#e2e8f0;font-family:sans-serif;padding:16px}
h1{color:#38bdf8;text-align:center;margin-bottom:20px;font-size:1.3rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.card{background:#1e293b;border-radius:10px;padding:14px}
.card h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:#38bdf8;margin-bottom:10px}
.row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #334155;font-size:.9rem}
.row:last-child{border:none}.val{font-weight:700;color:#facc15}
.btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
button{border:none;border-radius:6px;padding:7px 14px;font-size:.82rem;font-weight:600;cursor:pointer}
.on{background:#22c55e;color:#000}.off{background:#ef4444;color:#fff}.bl{background:#38bdf8;color:#000}
.relay-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #334155}
.relay-row:last-child{border:none}
.badge{padding:3px 8px;border-radius:4px;font-size:.75rem;font-weight:700}
.badge.on{background:#22c55e;color:#000}.badge.off{background:#475569;color:#e2e8f0}
input[type=range]{width:100%;margin:8px 0;accent-color:#38bdf8}
.alert-box{background:#450a0a;border:1px solid #ef4444;border-radius:8px;padding:8px;margin-top:8px;font-size:.82rem}
#alert-list li{color:#fca5a5;padding:2px 0;list-style:none}
footer{text-align:center;margin-top:16px;font-size:.72rem;color:#64748b}
</style></head><body>
<h1>&#127968; Casa Inteligente &mdash; ESP32</h1>
<div class="grid">
  <div class="card">
    <h2>&#128202; Sensores</h2>
    <div class="row"><span>&#127777; Temperatura</span><span class="val" id="t">--</span></div>
    <div class="row"><span>&#128167; Umidade</span><span class="val" id="h">--</span></div>
    <div class="row"><span>&#9728; Luminosidade (ADC)</span><span class="val" id="l">--</span></div>
    <div class="row"><span>&#128680; Gas/Fumaca</span><span class="val" id="g">--</span></div>
    <div class="row"><span>&#128694; Movimento</span><span class="val" id="m">--</span></div>
  </div>
  <div class="card">
    <h2>&#128268; Relays</h2>
    <div class="relay-row"><span>&#128161; Luzes do Andar</span><span class="badge off" id="r1b">OFF</span></div>
    <div class="btns" style="margin-bottom:8px">
      <button class="on"  onclick="cmd('relay1','on')">Ligar</button>
      <button class="off" onclick="cmd('relay1','off')">Desligar</button>
    </div>
    <div class="relay-row"><span>&#128276; Alarme Sonoro</span><span class="badge off" id="r2b">OFF</span></div>
    <div class="btns" style="margin-bottom:8px">
      <button class="on"  onclick="cmd('relay2','on')">Ligar</button>
      <button class="off" onclick="cmd('relay2','off')">Desligar</button>
    </div>
    <div class="relay-row"><span>&#128168; Exaustor Gas</span><span class="badge off" id="r3b">OFF</span></div>
    <div class="btns" style="margin-bottom:8px">
      <button class="on"  onclick="cmd('relay3','on')">Ligar</button>
      <button class="off" onclick="cmd('relay3','off')">Desligar</button>
    </div>
    <div class="relay-row"><span>&#10052; Ar-Condicionado</span><span class="badge off" id="r4b">OFF</span></div>
    <div class="btns">
      <button class="on"  onclick="cmd('relay4','on')">Ligar</button>
      <button class="off" onclick="cmd('relay4','off')">Desligar</button>
    </div>
  </div>
  <div class="card">
    <h2>&#129695; Persiana (Servo)</h2>
    <p style="font-size:.8rem;color:#94a3b8">Angulo: <span id="sv">0</span>&deg;</p>
    <input type="range" id="sr" min="0" max="180" value="0"
      oninput="document.getElementById('sv').innerText=this.value"
      onchange="cmd('servo',this.value)">
    <div class="btns">
      <button class="on"  onclick="setServo(180)">Abrir</button>
      <button class="bl"  onclick="setServo(90)">Meio</button>
      <button class="off" onclick="setServo(0)">Fechar</button>
    </div>
  </div>
  <div class="card">
    <h2>&#9888; Alertas Ativos</h2>
    <div class="alert-box"><ul id="alert-list"><li style="color:#64748b">Sem alertas.</li></ul></div>
  </div>
</div>
<footer>Atualizacao a cada 3s &mdash; broker.hivemq.com</footer>
<script>
function cmd(a,v){
  fetch('/cmd?a='+a+'&v='+encodeURIComponent(v)).catch(()=>{});
}
function setServo(v){
  document.getElementById('sr').value=v;
  document.getElementById('sv').innerText=v;
  cmd('servo',v);
}
function setBadge(id, on){
  var e=document.getElementById(id);
  e.innerText=on?'ON':'OFF';
  e.className='badge '+(on?'on':'off');
}
async function refresh(){
  try{
    var d=await(await fetch('/status')).json();
    document.getElementById('t').innerText=d.temperature.toFixed(1)+' C';
    document.getElementById('h').innerText=d.humidity.toFixed(1)+' %';
    document.getElementById('l').innerText=d.ldr;
    document.getElementById('g').innerText=d.gas.toFixed(1)+' %';
    document.getElementById('m').innerText=d.motion?'SIM':'Nao';
    setBadge('r1b', d.relay1); setBadge('r2b', d.relay2);
    setBadge('r3b', d.relay3); setBadge('r4b', d.relay4);
    if(d.servo!==undefined){
      document.getElementById('sr').value=d.servo;
      document.getElementById('sv').innerText=d.servo;
    }
    var ul=document.getElementById('alert-list');
    ul.innerHTML=d.alerts&&d.alerts.length
      ?d.alerts.map(a=>'<li>'+a+'</li>').join('')
      :'<li style="color:#64748b">Sem alertas.</li>';
  }catch(e){}
}
setInterval(refresh,3000);refresh();
</script></body></html>"""

_server = None

def start():
    global _server
    _server = socket.socket()
    _server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _server.bind(("0.0.0.0", 80))
    _server.listen(1)
    _server.setblocking(False)
    print("[WEB] Servidor na porta 80")

def _parse(path):
    params, base = {}, path
    if "?" in path:
        base, qs = path.split("?", 1)
        for p in qs.split("&"):
            if "=" in p:
                k, v = p.split("=", 1)
                params[k] = v.replace("%20"," ").replace("%0A","\n").replace("+"," ")
    return base, params

def handle_requests():
    if not _server: return
    try:
        conn, _ = _server.accept()
        conn.settimeout(2.0)
        try:
            req  = conn.recv(512).decode()
            path = req.split(" ")[1] if " " in req else "/"
            base, params = _parse(path)

            if base == "/status":
                conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n")
                conn.send(json.dumps(_state).encode())

            elif base == "/cmd" and "a" in params:
                a, v = params["a"], params.get("v","")
                topic_map = {
                    "relay1": (config.TOPIC_RELAY1, 0),
                    "relay2": (config.TOPIC_RELAY2, 1),
                    "relay3": (config.TOPIC_RELAY3, 2),
                    "relay4": (config.TOPIC_RELAY4, 3),
                }
                if a in topic_map:
                    topic, idx = topic_map[a]
                    actuators.relay_from_str(idx, v)
                    mqtt_client.publish(topic, v)
                elif a == "servo":
                    actuators.servo_from_str(v)
                    mqtt_client.publish(config.TOPIC_SERVO, v)
                elif a == "oled":
                    actuators.oled_message(v)
                    mqtt_client.publish(config.TOPIC_OLED, v)
                conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nOK")
            else:
                conn.send(_HTML.encode())
        except: pass
        finally: conn.close()
    except OSError: pass