from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

registered_gateways = {}
node_status = {}
command_queue = {}

@app.post("/devices/register")
async def register(request: Request):
    data = await request.json()
    mac = data.get("mac")
    registered_gateways[mac] = {"registered_at": time.time()}
    command_queue[mac] = []
    print(f"GATEWAY REGISTERED: {mac}")
    return {"ok": True, "deviceId": mac}

@app.post("/devices/report")
async def report(request: Request):
    data = await request.json()
    gw_id = data.get("gw_id")
    for dev in data.get("devices", []):
        node_status[dev["deviceId"]] = dev
    print(f"REPORT from {gw_id}: {len(data.get('devices', []))} nodes")
    return {"ok": True}

@app.get("/devices/{mac}/next-command")
async def get_command(mac: str):
    if mac in command_queue and command_queue[mac]:
        cmds = command_queue[mac]
        command_queue[mac] = []
        return {"ok": True, "devices": cmds}
    return {"ok": True, "devices": []}

@app.post("/test/send-command")
async def test_send(request: Request):
    data = await request.json()
    mac = data.get("gateway_mac")
    cmds = data.get("commands", [])
    if mac not in command_queue:
        command_queue[mac] = []
    command_queue[mac].extend(cmds)
    print(f"QUEUED {len(cmds)} commands for {mac}")
    return {"ok": True}

@app.get("/test/status")
async def status():
    return {
        "ok": True,
        "registered_gateways": list(registered_gateways.keys()),
        "node_status": node_status
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})