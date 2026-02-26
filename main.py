from fastapi import FastAPI, Response
import os
import ssl
import threading
import time
import paho.mqtt.client as mqtt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"mensaje": "Backend Telemetria funcionando"}

@app.head("/")
def head_root():
    return Response(status_code=200)

@app.get("/health")
def health():
    return {"status": "ok"}

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")

latest_message = {
    "status": "No data yet",
    "topic": MQTT_TOPIC,
    "payload": None,
    "ts": None
}

def _mqtt_worker():
    if not all([MQTT_BROKER, MQTT_USER, MQTT_PASS, MQTT_TOPIC]):
        print("MQTT not configured: missing env vars.")
        return

    def on_connect(client, userdata, flags, rc):
        print("MQTT connected rc=", rc)
        client.subscribe(MQTT_TOPIC)

    def on_message(client, userdata, msg):
        latest_message["status"] = "ok"
        latest_message["topic"] = msg.topic
        latest_message["payload"] = msg.payload.decode(errors="replace")
        latest_message["ts"] = time.time()
        print("Mensaje recibido:", latest_message["payload"])

    while True:
        try:
            client = mqtt.Client(client_id=f"telemetria-backend-{int(time.time())}")
            client.username_pw_set(MQTT_USER, MQTT_PASS)
            client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print("MQTT error:", repr(e), "Reintentando en 5s...")
            time.sleep(5)

@app.on_event("startup")
def startup_event():
    threading.Thread(target=_mqtt_worker, daemon=True).start()

@app.get("/latest")
def latest():
    return latest_message

print("TEST MQTT")