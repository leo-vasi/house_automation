# web_server.py — Servidor Web embarcado no ESP32
# Permite controle dos atuadores via browser na mesma rede
import socket
import json
import actuators
import mqtt_client
import config

# ─── HTML da página web ───────────────────────────────────────────────────────
_HTML = """\
HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Casa Inteligente — ESP32</title>
<style>
  :root { --bg:#0f172a; --card:#1e293b; --acc:#38bdf8; --green:#22c55e;
          --red:#ef4444; --yellow:#facc15; --text:#e2e8f0; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--text); font-family:sans-serif;
         display:flex; flex-direction:column; align-items:center; padding:20px; }
  h1 { color:var(--acc); margin-bottom:20px; font-size:1.4rem; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
          gap:16px; width:100%; max-width:900px; }
  .card { background:var(--card); border-radius:12px; padding:16px; }
  .card h2 { font-size:0.85rem; text-transform:uppercase; letter-spacing:.08em;
              color:var(--acc); margin-bottom:12px; }
  .sensor-row { display:flex; justify-content:space-between; padding:6px 0;
                border-bottom:1px solid #334155; font-size:0.95rem; }
  .sensor-row:last-child { border:none; }
  .val { font-weight:700; color:var(--yellow); }
  .btn-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
  button { cursor:pointer; border:none; border-radius:8px; padding:8px 14px;
           font-size:0.85rem; font-weight:600; transition:.15s; }
  .btn-on  { background:var(--green); color:#000; }
  .btn-off { background:var(--red);   color:#fff; }
  .btn-blue{ background:var(--acc);   color:#000; }
  .btn-warn{ background:var(--yellow);color:#000; }
  input[type=range] { width:100%; margin:8px 0; accent-color:var(--acc); }
  .alert-box { background:#450a0a; border:1px solid var(--red);
               border-radius:8px; padding:10px; font-size:0.85rem; margin-top:8px; }
  #alerts-list { list-style:none; padding:0; }
  #alerts-list li { padding:3px 0; color:#fca5a5; }
  .status-ok  { color:var(--green); font-weight:700; }
  .status-bad { color:var(--red);   font-weight:700; }
  footer { margin-top:24px; font-size:0.75rem; color:#64748b; }
</style>
</head>
<body>
<h1>🏠 Casa Inteligente — ESP32</h1>
<div class="grid">

  <!-- SENSORES -->
  <div class="card">
    <h2>📊 Sensores em Tempo Real</h2>
    <div class="sensor-row"><span>🌡️ Temperatura</span><span class="val" id="v-temp">--</span></div>
    <div class="sensor-row"><span>💧 Umidade</span><span class="val" id="v-hum">--</span></div>
    <div class="sensor-row"><span>☀️ Luminosidade</span><span class="val" id="v-ldr">--</span></div>
    <div class="sensor-row"><span>🚨 Gás/Fumaça</span><span class="val" id="v-gas">--</span></div>
    <div class="sensor-row"><span>🚶 Movimento</span><span class="val" id="v-pir">--</span></div>
  </div>

  <!-- LED RGB -->
  <div class="card">
    <h2>💡 Iluminação (LED RGB)</h2>
    <p style="font-size:.8rem;color:#94a3b8;margin-bottom:8px">Controla a luz da sala</p>
    <div class="btn-row">
      <button class="btn-on"   onclick="cmd('rgb','white')">Branco</button>
      <button class="btn-warn" onclick="cmd('rgb','yellow')">Amarelo</button>
      <button class="btn-blue" onclick="cmd('rgb','blue')">Azul</button>
      <button         style="background:#a855f7;color:#fff" onclick="cmd('rgb','purple')">Roxo</button>
      <button class="btn-off"  onclick="cmd('rgb','off')">Desligar</button>
    </div>
  </div>

  <!-- SERVO -->
  <div class="card">
    <h2>🪟 Persiana / Janela (Servo)</h2>
    <p style="font-size:.8rem;color:#94a3b8;margin-bottom:8px">Ângulo: <span id="servo-val">0</span>°</p>
    <input type="range" id="servo-range" min="0" max="180" value="0"
           oninput="document.getElementById('servo-val').innerText=this.value"
           onchange="cmd('servo',this.value)">
    <div class="btn-row">
      <button class="btn-on"   onclick="cmd('servo','open');document.getElementById('servo-range').value=180;document.getElementById('servo-val').innerText=180">Abrir</button>
      <button class="btn-warn" onclick="cmd('servo','half');document.getElementById('servo-range').value=90;document.getElementById('servo-val').innerText=90">Meio</button>
      <button class="btn-off"  onclick="cmd('servo','close');document.getElementById('servo-range').value=0;document.getElementById('servo-val').innerText=0">Fechar</button>
    </div>
  </div>

  <!-- ALARME -->
  <div class="card">
    <h2>🔔 Alarme de Segurança</h2>
    <p style="font-size:.8rem;color:#94a3b8;margin-bottom:8px">
      Estado: <span id="alarm-state" class="status-ok">DESLIGADO</span>
    </p>
    <div class="btn-row">
      <button class="btn-off" onclick="cmd('alarm','on');setAlarmUI(true)">🔴 Ativar Alarme</button>
      <button class="btn-on"  onclick="cmd('alarm','off');setAlarmUI(false)">✅ Desativar</button>
    </div>
  </div>

  <!-- OLED -->
  <div class="card">
    <h2>🖥️ Mensagem no OLED</h2>
    <p style="font-size:.8rem;color:#94a3b8;margin-bottom:8px">Envie texto ao display (use \\n para nova linha)</p>
    <textarea id="oled-msg" rows="3"
      style="width:100%;background:#0f172a;color:#e2e8f0;border:1px solid #334155;
             border-radius:6px;padding:8px;font-size:0.85rem;resize:none"
      placeholder="Ex: Ola!\nBem-vindo!"></textarea>
    <div class="btn-row" style="margin-top:4px">
      <button class="btn-blue" onclick="sendOled()">Enviar ao OLED</button>
      <button class="btn-warn" onclick="cmd('oled','STATUS')">Restaurar Status</button>
    </div>
  </div>

  <!-- ALERTAS -->
  <div class="card">
    <h2>⚠️ Alertas Ativos</h2>
    <div class="alert-box">
      <ul id="alerts-list"><li style="color:#64748b">Nenhum alerta no momento.</li></ul>
    </div>
  </div>

</div>
<footer>ESP32 Home IoT — Atualização a cada 3s — Broker: broker.hivemq.com</footer>

<script>
function cmd(actuator, value) {
  fetch('/cmd?a=' + actuator + '&v=' + encodeURIComponent(value))
    .catch(e => console.error(e));
}

function sendOled() {
  const msg = document.getElementById('oled-msg').value;
  cmd('oled', msg);
}

function setAlarmUI(on) {
  const el = document.getElementById('alarm-state');
  el.innerText = on ? 'ATIVADO' : 'DESLIGADO';
  el.className = on ? 'status-bad' : 'status-ok';
}

async function updateSensors() {
  try {
    const r = await fetch('/status');
    const d = await r.json();
    document.getElementById('v-temp').innerText = d.temperature.toFixed(1) + ' °C';
    document.getElementById('v-hum').innerText  = d.humidity.toFixed(1)    + ' %';
    document.getElementById('v-ldr').innerText  = d.ldr;
    document.getElementById('v-gas').innerText  = d.gas.toFixed(1)         + ' %';
    document.getElementById('v-pir').innerText  = d.motion ? '🔴 SIM' : '🟢 Não';
    const ul = document.getElementById('alerts-list');
    if (d.alerts && d.alerts.length > 0) {
      ul.innerHTML = d.alerts.map(a => '<li>⚠️ ' + a + '</li>').join('');
    } else {
      ul.innerHTML = '<li style="color:#64748b">Nenhum alerta no momento.</li>';
    }
    if (d.alarm !== undefined) setAlarmUI(d.alarm);
    if (d.servo !== undefined) {
      document.getElementById('servo-val').innerText = d.servo;
      document.getElementById('servo-range').value = d.servo;
    }
  } catch(e) {}
}

setInterval(updateSensors, 3000);
updateSensors();
</script>
</body>
</html>
"""

# ─── Estado compartilhado (atualizado pelo main.py) ───────────────────────────
_shared_state = {}

def update_state(data, alerts):
    """Chamado pelo main.py para manter estado atualizado."""
    global _shared_state
    _shared_state = {
        "temperature": data.get("temperature", 0),
        "humidity":    data.get("humidity", 0),
        "ldr":         data.get("ldr", 0),
        "gas":         data.get("gas", 0),
        "motion":      data.get("motion", False),
        "alerts":      alerts,
        "alarm":       actuators.get_alarm_state(),
        "servo":       actuators.get_servo_angle(),
    }

# ─── Servidor socket ──────────────────────────────────────────────────────────
_server = None

def start():
    global _server
    _server = socket.socket()
    _server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _server.bind(("0.0.0.0", 80))
    _server.listen(1)
    _server.setblocking(False)
    print("[WEB] Servidor iniciado na porta 80")

def _parse_query(path):
    """Extrai parâmetros ?a=...&v=... da URL."""
    if "?" not in path:
        return {}, path
    base, qs = path.split("?", 1)
    params = {}
    for part in qs.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v.replace("%20", " ").replace("%0A", "\n")
    return params, base

def handle_requests():
    """Chame no loop principal. Non-blocking."""
    global _server
    if _server is None:
        return
    try:
        conn, addr = _server.accept()
        conn.settimeout(2.0)
        try:
            req = conn.recv(512).decode()
            first_line = req.split("\r\n")[0]
            method, path, _ = first_line.split(" ")
            params, base = _parse_query(path)

            if base == "/status":
                body = json.dumps(_shared_state)
                conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n")
                conn.send(body.encode())

            elif base == "/cmd" and "a" in params and "v" in params:
                actuator = params["a"]
                value    = params["v"]
                # Executa localmente E publica via MQTT (bidirecional)
                if actuator == "rgb":
                    actuators.rgb_from_str(value)
                    mqtt_client.publish(config.TOPIC_RGB, value)
                elif actuator == "servo":
                    actuators.servo_from_str(value)
                    mqtt_client.publish(config.TOPIC_SERVO, value)
                elif actuator == "alarm":
                    actuators.alarm_from_str(value)
                    mqtt_client.publish(config.TOPIC_ALARM, value)
                elif actuator == "oled":
                    if value != "STATUS":
                        actuators.oled_message(value)
                    mqtt_client.publish(config.TOPIC_OLED, value)

                conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nOK")

            else:
                conn.send(_HTML.encode())

        except Exception as e:
            print(f"[WEB] Erro ao processar request: {e}")
        finally:
            conn.close()
    except OSError:
        pass  # Sem conexões pendentes (non-blocking)
