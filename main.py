"""
DATN Smart Light Control System - Mock API Server
==================================================

FastAPI server để giao tiếp với Gateway ESP32
Hỗ trợ 3 endpoints chính:
1. POST /devices/register - Đăng ký gateway
2. POST /devices/report - Nhận dữ liệu từ nodes
3. GET /devices/{mac}/next-command - Gửi lệnh điều khiển

Version: 3.1 (CORS ENABLED)
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware  # THÊM DÒNG NÀY
from typing import Dict, List
import time

app = FastAPI(title="DATN Smart Light Mock API")

# BẬT CORS CHO PHÉP LOCALHOST (và mọi nơi)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev: cho phép tất cả
    # allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],  # Production: chỉ local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")


# ============================================================
# DATABASE (In-memory storage)
# ============================================================

registered_gateways: Dict[str, dict] = {}
node_status: Dict[str, dict] = {}
command_queue: Dict[str, List[dict]] = {}


# ============================================================
# 1. REGISTER DEVICE
# ============================================================
@app.post("/devices/register")
async def register_device(request: Request):
    data = await request.json()
    mac = data.get("mac", "UNKNOWN")
    
    registered_gateways[mac] = {
        "mac": mac,
        "registered_at": time.time(),
        "last_seen": time.time()
    }
    
    if mac not in command_queue:
        command_queue[mac] = []
    
    print("=" * 60)
    print(f"GATEWAY REGISTERED: {mac}")
    print(f"   Total Gateways: {len(registered_gateways)}")
    print("=" * 60)
    
    return {"ok": True, "deviceId": mac}


# ============================================================
# 2. REPORT STATUS
# ============================================================
@app.post("/devices/report")
async def report_status(request: Request):
    data = await request.json()
    gw_id = data.get("gw_id", "UNKNOWN")
    devices = data.get("devices", [])
    
    print("\n" + "=" * 60)
    print(f"STATUS REPORT from {gw_id}")
    print("=" * 60)
    
    for device in devices:
        device_id = device.get("deviceId", "UNKNOWN")
        node_status[device_id] = {
            "brightness": device.get("brightness", 0),
            "lux": device.get("lux", 0),
            "current": device.get("current", 0.0),
            "timestamp": time.time(),
            "gateway": gw_id
        }
        
        print(f"  {device_id}:")
        print(f"     Brightness: {device.get('brightness')}%")
        print(f"     Light: {device.get('lux')} lux")
        print(f"     Current: {device.get('current')} A")
    
    print("=" * 60 + "\n")
    
    return {"ok": True}


# ============================================================
# 3. GET NEXT COMMAND
# ============================================================
@app.get("/devices/{device_mac}/next-command")
async def get_command(device_mac: str):
    print("\n" + "-" * 60)
    print(f"GET COMMAND request from: {device_mac}")
    
    if device_mac in command_queue and len(command_queue[device_mac]) > 0:
        commands = command_queue[device_mac]
        command_queue[device_mac] = []
        
        print(f"   Sending {len(commands)} command(s)")
        for cmd in commands:
            print(f"      {cmd['deviceId']}: brightness={cmd['brightness']}%")
        print("-" * 60 + "\n")
        
        return {"ok": True, "devices": commands}
    else:
        print("   No commands")
        print("-" * 60 + "\n")
        return {"ok": True, "devices": []}


# ============================================================
# TEST ENDPOINTS
# ============================================================
@app.post("/test/send-command")
async def test_send_command(request: Request):
    data = await request.json()
    gateway_mac = data.get("gateway_mac")
    commands = data.get("commands", [])
    
    if gateway_mac not in command_queue:
        command_queue[gateway_mac] = []
    
    command_queue[gateway_mac].extend(commands)
    
    print("\n" + "TEST COMMAND ADDED for {gateway_mac}:")
    for cmd in commands:
        print(f"  {cmd['deviceId']}: {cmd['brightness']}%")
    print("TEST COMMAND ADDED" + "\n")
    
    return {"ok": True, "message": f"Added {len(commands)} command(s)"}


@app.get("/test/status")
async def test_status():
    return {
        "ok": True,
        "registered_gateways": list(registered_gateways.keys()),
        "node_status": node_status,
        "command_queues": {k: len(v) for k, v in command_queue.items()}
    }


# ============================================================
# DASHBOARD
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ============================================================
# STARTUP
# ============================================================
@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 60)
    print("DATN Smart Light Mock API Server - CORS ENABLED")
    print("=" * 60)
    print("Endpoints:")
    print("   POST   /devices/register")
    print("   POST   /devices/report")
    print("   GET    /devices/{mac}/next-command")
    print("\nTest:")
    print("   POST   /test/send-command")
    print("   GET    /test/status")
    print("   GET    / (Dashboard)")
    print("=" * 60 + "\n")