from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/")
def root():
    return {"mensaje": "Backend Telemetria funcionando"}

# Render a veces hace HEAD /
@app.head("/")
def head_root():
    return Response(status_code=200)

@app.get("/health")
def health():
    return {"status": "ok"}