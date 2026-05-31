# HomeIoT - Sistema de Automação Residencial

> Sistema de automação residencial desenvolvido com ESP32 em MicroPython, simulado na plataforma Wokwi e integrado com MQTT, Node-RED e Google Sheets.

![MicroPython](https://img.shields.io/badge/MicroPython-v1.23.0-blue?logo=python)
![ESP32](https://img.shields.io/badge/ESP32-DevKit%20C%20v4-red)
![MQTT](https://img.shields.io/badge/MQTT-HiveMQ-purple)
![Node-RED](https://img.shields.io/badge/Node--RED-Dashboard%202.0-darkred?logo=nodered)
![Wokwi](https://img.shields.io/badge/Simulador-Wokwi-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

---

## Sobre o projeto

O HomeIoT simula uma residência inteligente utilizando um microcontrolador ESP32 programado em MicroPython. O sistema integra quatro sensores ambientais com quatro módulos de relay, um servo motor e um display OLED, formando uma solução completa de monitoramento e controle.

A comunicação externa é realizada via protocolo MQTT sobre Wi-Fi, permitindo telemetria em tempo real, controle remoto de atuadores, exibição de dados em dashboard Node-RED e registro histórico em Google Sheets. Alertas são enviados por e-mail automaticamente ao proprietário sempre que um limiar de segurança é ultrapassado.

O projeto foi desenvolvido e validado no Wokwi Web e posteriormente migrado para o Visual Studio Code com a extensão Wokwi, utilizando a ferramenta mpremote para upload dos arquivos ao simulador.

---

## Lógica de automação

Cada sensor monitora uma variável ambiental e aciona um relay automaticamente quando o valor ultrapassa um limiar configurável em `config.py`. A tabela abaixo resume as quatro regras implementadas:

| Relay | Sensor | Condição de Ativação | Carga Controlada | Parâmetro |
|---|---|---|---|---|
| Relay 1 | LDR (GPIO 33) | `ldr < 1000` | Luzes do andar | `LDR_MIN = 1000` |
| Relay 2 | PIR (GPIO 35) | `motion == True` | Alarme sonoro | Detecção digital |
| Relay 3 | Gas (GPIO 32) | `gas >= 60.0%` | Exaustor | `GAS_MAX = 60.0` |
| Relay 4 | DHT22 (GPIO 5) | `temperature >= 35.0 C` | Ar-condicionado | `TEMP_MAX = 35.0` |

O estado de cada relay é avaliado a cada 5 segundos. Se o sensor retornar à faixa normal, o relay é desativado automaticamente no próximo ciclo. Além da automação local, qualquer relay e o servo podem ser controlados remotamente via MQTT ou pelos botões da dashboard Node-RED.

---

## Arquitetura do sistema

```
Sensores (LDR, DHT22, PIR, Gas)
        |
        v
   ESP32 (MicroPython)
        |-- sensors.py     -> leitura e verificação de alertas
        |-- actuators.py   -> relays, servo e OLED
        |-- mqtt_client.py -> publish/subscribe MQTT
        |-- main.py        -> orquestrador principal
        |
        v
  Broker HiveMQ (público, porta 1883)
        |
        +--------> Node-RED Dashboard 2.0
        |               |-- Gauges de sensores em tempo real
        |               |-- Botões de controle dos relays
        |               |-- Slider do servo motor
        |               |-- Notificação e log de alertas
        |               |-- Envio de e-mail (node-red-node-email)
        |               |-- Registro no Google Sheets (a cada 2h)
        |
```

---

## Estrutura do repositório

```
homeiot/
├── diagram.json           # Esquema de hardware do Wokwi (componentes e conexões)
├── wokwi.toml             # Configuração do simulador (firmware, porta RFC2217)
├── config.py              # Constantes: Wi-Fi, MQTT, pinos GPIO e limiares
├── main.py                # Ponto de entrada: inicialização e loop principal
├── sensors.py             # Leitura dos quatro sensores e geração de alertas
├── actuators.py           # Controle dos relays, servo motor e display OLED
├── mqtt_client.py         # Conexão MQTT, publish e subscribe
├── ssd1306.py             # Driver do display OLED SSD1306 (MIT, micropython-lib)
├── nodered_flow.json      # Flow completo do Node-RED para importação
└── casa_inteligente_iot.js  # Webhook para registro no Google Sheets
```

---

## Hardware simulado

| Componente | ID Wokwi | Quantidade | Função |
|---|---|---|---|
| ESP32 DevKit C v4 | esp | 1 | Microcontrolador principal |
| Fotorresistor (LDR) | ldr1 | 1 | Medição de luminosidade |
| Sensor DHT22 | dht1 | 1 | Temperatura e umidade |
| Sensor PIR | pir1 | 1 | Detecção de movimento |
| Sensor de gás | gas1 | 1 | Concentração de gás (0-100%) |
| Módulo Relay | relay1-4 | 4 | Acionamento de cargas externas |
| Servo Motor | srv1 | 1 | Controle de posição angular |
| Display OLED SSD1306 | oled1 | 1 | Status local (128x64px, I2C) |
| Resistor 10k ohm | r1 | 1 | Pull-up para dados do DHT22 |

---

## Tópicos MQTT

Todos os tópicos utilizam o prefixo `11232100617/home/` para evitar colisões no broker público.

| Tópico | Direção | Formato |
|---|---|---|
| `11232100617/home/sensors` | Publish | JSON com todos os sensores e estados. Publicado a cada 10s. |
| `11232100617/home/alerts` | Publish | JSON `{"alerts": [...]}`. Publicado quando há alertas ativos. |
| `11232100617/home/actuators/relay1` | Sub/Pub | Texto: `on` ou `off` |
| `11232100617/home/actuators/relay2` | Sub/Pub | Texto: `on` ou `off` |
| `11232100617/home/actuators/relay3` | Sub/Pub | Texto: `on` ou `off` |
| `11232100617/home/actuators/relay4` | Sub/Pub | Texto: `on` ou `off` |
| `11232100617/home/actuators/servo` | Subscribe | Texto: `open`, `close`, `half` ou inteiro de 0 a 180 |
| `11232100617/home/actuators/oled` | Subscribe | Texto livre com `\n` para quebra de linha |

---

## Mapeamento de pinos (ESP32)

| GPIO | Periférico | Tipo de Sinal |
|---|---|---|
| 5 | DHT22 | Digital 1-wire (com pull-up 10k) |
| 16 | Relay 3 (IN) | Digital Output — LOW ativa, HIGH desativa |
| 17 | Relay 4 (IN) | Digital Output — LOW ativa, HIGH desativa |
| 18 | Relay 1 (IN) | Digital Output — LOW ativa, HIGH desativa |
| 19 | Relay 2 (IN) | Digital Output — LOW ativa, HIGH desativa |
| 21 | OLED SDA | I2C Data (400 kHz, endereço 0x3C) |
| 22 | OLED SCL | I2C Clock |
| 26 | Servo (PWM) | PWM 50 Hz — pulso de 600 us a 2400 us |
| 32 | Sensor de gás (AOUT) | ADC 12 bits, atenuação 11 dB |
| 33 | LDR (AO) | ADC 12 bits, atenuação 11 dB |
| 35 | PIR (OUT) | Digital Input — HIGH = movimento |

> **Atenção:** Os módulos relay utilizam lógica invertida. O pino em nível LOW ativa o relay. Todos os pinos de relay são inicializados em HIGH (desativado) no boot para evitar acionamentos indesejados.

---

## Pré-requisitos

- Visual Studio Code com a extensão **Wokwi** instalada e licença ativa
- Python 3.x instalado
- mpremote v1.23.0 instalado via pip
- Firmware MicroPython v1.23.0 para ESP32 (arquivo `.bin`)
- Node-RED instalado com o pacote `@flowfuse/node-red-dashboard` (Dashboard 2.0)
- Conta Google para configuração do Google Apps Script
- Conta Gmail com verificação em duas etapas ativa (para envio de alertas por e-mail)

---

## Configuração do ambiente

### 1. Firmware MicroPython

Acesse [micropython.org/download/ESP32_GENERIC](https://micropython.org/download/ESP32_GENERIC/) e baixe a versão **v1.23.0**:

```
ESP32_GENERIC-20241025-v1.23.0.bin
```

Coloque o arquivo `.bin` na raiz da pasta do projeto, junto com os demais arquivos.

### 2. Instalação do mpremote

```powershell
pip install mpremote==1.23.0
```

### 3. Configuração do wokwi.toml

O arquivo já está configurado no repositório. Verifique se o nome do firmware corresponde ao arquivo baixado. Caso a porta 4001 já esteja em uso no seu sistema, altere `rfc2217ServerPort` para outra porta disponível (ex: 4002) e ajuste os comandos mpremote nos passos seguintes.

```toml
[wokwi]
version = 1
firmware = "ESP32_GENERIC-20241025-v1.23.0.bin"
elf = ""
rfc2217ServerPort = 4001

[[net.forward]]
from = "localhost:9080"
to = "target:80"
```

### 4. Variáveis de configuração

Edite o arquivo `config.py` antes de iniciar a simulação. Os limiares de automação e as credenciais MQTT podem ser ajustados conforme necessário:

```python
WIFI_SSID     = "Wokwi-GUEST"   # rede virtual do Wokwi, não alterar
WIFI_PASSWORD = ""

MQTT_BROKER    = "broker.hivemq.com"
MQTT_PORT      = 1883
MQTT_CLIENT_ID = "11232100617_esp32"

# Limiares de automação
TEMP_MAX = 35.0   # graus Celsius — acima disso aciona o ar-condicionado
GAS_MAX  = 60.0   # percentual   — acima disso aciona o exaustor
LDR_MIN  = 1000   # valor ADC    — abaixo disso aciona as luzes do andar
```

---

## Executando a simulação no VS Code

### Passo 1 — Inicie o simulador

No VS Code, pressione `F1` e selecione **Wokwi: Start Simulator**. Aguarde cerca de 5 segundos até o boot do MicroPython aparecer no terminal do simulador.

### Passo 2 — Abra um terminal na pasta do projeto

```powershell
cd "C:\caminho\para\sua\pasta\homeiot"
```

Confirme que os arquivos estão presentes antes de continuar:

```powershell
dir *.py
```

### Passo 3 — Envie os arquivos para o ESP32 simulado

Execute os comandos abaixo um por vez. Mantenha a janela do simulador **visível** durante todo o processo. Minimizar a janela pausa a simulação e causa timeout nos comandos mpremote.

```powershell
python -m mpremote connect port:rfc2217://localhost:4001 fs cp ssd1306.py :ssd1306.py
python -m mpremote connect port:rfc2217://localhost:4001 fs cp config.py :config.py
python -m mpremote connect port:rfc2217://localhost:4001 fs cp sensors.py :sensors.py
python -m mpremote connect port:rfc2217://localhost:4001 fs cp actuators.py :actuators.py
python -m mpremote connect port:rfc2217://localhost:4001 fs cp mqtt_client.py :mqtt_client.py
python -m mpremote connect port:rfc2217://localhost:4001 fs cp main.py :main.py
```

Se algum comando retornar `could not enter raw repl`, aguarde mais alguns segundos e tente novamente. O ESP32 pode ainda estar no processo de boot.

### Passo 4 — Reinicie o ESP32 pelo REPL

```powershell
python -m mpremote connect port:rfc2217://localhost:4001 repl
```

Quando o REPL abrir, execute:

```python
import machine
machine.reset()
```

Pressione `Ctrl + ]` para sair do REPL. O `main.py` será executado automaticamente pelo bootloader a partir desse ponto.

### Passo 5 — Verifique o boot no terminal

O terminal do simulador deve exibir a sequência abaixo. Qualquer linha com `ERRO` indica qual módulo falhou ao carregar.

```
========================================
[BOOT] Casa Inteligente IoT
========================================
[BOOT] config OK
[BOOT] sensors OK
[BOOT] actuators OK
[BOOT] mqtt_client OK
[BOOT] web_server OK
[WiFi] Conectando...
[WiFi] Conectado IP: 10.13.37.3
[MQTT] Conectado
[WEB] Servidor na porta 80
[SETUP] Pronto
[SENS] T=24.0C H=40.0% LDR=1001 GAS=12.3% PIR=False
```

> **Importante:** O filesystem do Wokwi não persiste entre sessões. Os passos 2 a 4 devem ser repetidos sempre que o simulador for reiniciado.

---

## Configuração do Node-RED

### 1. Instale o Dashboard 2.0 e o nó de e-mail

```powershell
cd %USERPROFILE%\.node-red
npm install @flowfuse/node-red-dashboard
npm install node-red-node-email
```

Reinicie o Node-RED após a instalação.

### 2. Importe o flow

No Node-RED, acesse **Menu -> Import**, cole o conteúdo do arquivo `nodered_flow.json` e clique em **Import**. Em seguida, clique em **Deploy**.

### 3. Configure o nó de e-mail

Localize o nó **e-mail** no canvas e preencha os campos:

| Campo | Valor |
|---|---|
| To | endereço que receberá os alertas |
| Server | `smtp.gmail.com` |
| Port | `465` |
| Use secure connection | marcado |
| Userid | seu endereço Gmail |
| Password | senha de aplicativo gerada na conta Google |

Para gerar a senha de aplicativo: acesse **myaccount.google.com -> Segurança -> Senhas de app**. A verificação em duas etapas deve estar ativa. A senha gerada tem 16 caracteres e deve ser inserida sem espaços.

### 4. Configure o Google Sheets

Acesse [script.google.com](https://script.google.com) e crie um novo projeto vinculado a uma planilha Google Sheets. Cole o conteúdo de `google_apps_script.js` e implante como **App da Web** com as configurações:

- Executar como: **Eu**
- Quem tem acesso: **Qualquer pessoa**

Copie a URL gerada e substitua no nó **Envia ao Google Sheets** dentro do flow Node-RED.

### 5. Acesse o dashboard

```
http://localhost:1880/ui
```

---

## Testando o sistema

| Ação no simulador | Resultado esperado |
|---|---|
| Reduzir luminosidade no LDR (ADC < 1000) | Relay 1 ativa — luzes do andar ligadas |
| Clicar no sensor PIR | Relay 2 ativa imediatamente — alarme sonoro |
| Aumentar gás acima de 60% | Relay 3 ativa — exaustor ligado |
| Alterar temperatura para acima de 35 C no `diagram.json` | Relay 4 ativa — ar-condicionado |
| Clicar em botão de relay no Node-RED | Relay correspondente acionado no simulador |
| Mover slider do servo no Node-RED | Servo move para o ângulo definido |
| Qualquer alerta ativo | E-mail enviado automaticamente ao proprietário |
| Clicar no botão inject no Node-RED | Dados enviados ao Google Sheets imediatamente |

---

## Observações

- O broker HiveMQ público é utilizado sem autenticação e sem criptografia (porta 1883). Essa configuração é adequada para fins acadêmicos e de simulação, mas não deve ser utilizada em produção.
- O prefixo `11232100617/home/` nos tópicos MQTT oferece separação lógica em ambientes compartilhados, como brokers públicos utilizados em aulas, evitando colisão de mensagens entre projetos distintos.
- Os limiares de automação definidos em `config.py` são adequados para simulação no Wokwi. Em hardware físico, é necessário calibrar especialmente o valor de `LDR_MIN` de acordo com o divisor de tensão utilizado e as condições de iluminação do ambiente.
- Este projeto é uma demonstração acadêmica desenvolvida na disciplina de Internet das Coisas do curso de Bacharelado em Engenharia de Software da Universidade de Mogi das Cruzes.
