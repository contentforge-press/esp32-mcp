# -*- coding: utf-8 -*-
"""ESP32 设备端固件（MicroPython）—— 为 esp32-control MCP server 提供 REST 接口
烧录到 ESP32 后：设备启动 AP 模式（或连 WiFi），监听 80 端口。
工具：Thonny 或 mpremote 上传本文件为 main.py。
"""
import json
import gc
import machine
import network
import socket
import time
import sys

# ---- 配置 ----
AP_SSID = "ESP32-MCP"
AP_PASS = "12345678"
# 也可改为 STA 模式连家里 WiFi：
# STA_SSID, STA_PASS = "your_wifi", "your_password"

GPIO_OUT = (2, 4, 5, 18, 19)   # 默认可输出引脚
ADC_PINS = (32, 33, 34, 35, 36, 39)


def boot_network():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=AP_SSID, password=AP_PASS, channel=6)
    ap.active(True)
    for _ in range(20):
        if ap.active() and ap.ifconfig()[0] != "0.0.0.0":
            break
        time.sleep(0.2)
    print("AP:", ap.ifconfig())


def status():
    gc.collect()
    return {
        "online": True,
        "chip": sys.platform,
        "free_heap": gc.mem_free(),
        "alloc_heap": gc.mem_alloc(),
        "uptime_s": int(time.ticks_ms() / 1000),
        "ip": network.WLAN(network.AP_IF).ifconfig()[0],
    }


def handle(path, body):
    if path == "/api/status":
        return 200, status()
    if path == "/api/gpio" and body:
        pin, level = int(body.get("pin", -1)), int(body.get("level", -1))
        if pin not in GPIO_OUT or level not in (0, 1):
            return 400, {"error": "invalid pin/level"}
        p = machine.Pin(pin, machine.Pin.OUT)
        p.value(level)
        return 200, {"ok": True, "pin": pin, "level": level}
    if path == "/api/gpio/read" and body:
        pin = int(body.get("pin", -1))
        try:
            p = machine.Pin(pin, machine.Pin.IN)
            return 200, {"pin": pin, "level": p.value()}
        except Exception as e:
            return 400, {"error": str(e)}
    if path == "/api/adc" and body:
        pin = int(body.get("pin", -1))
        if pin not in ADC_PINS:
            return 400, {"error": "pin not ADC-capable"}
        adc = machine.ADC(machine.Pin(pin))
        adc.atten(machine.ADC.ATTN_11DB)
        return 200, {"pin": pin, "mv": adc.read_uv() // 1000}
    if path == "/api/cmd" and body:
        cmd = str(body.get("cmd", ""))
        return 200, {"cmd": cmd, "echo": f"received:{cmd}"}
    if path == "/api/reboot":
        machine.reset()
    return 404, {"error": "not found"}


def serve():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 80))
    s.listen(2)
    print("HTTP ready on :80")
    while True:
        try:
            conn, addr = s.accept()
            req = conn.recv(1024).decode(errors="ignore")
            head = req.split("\r\n\r\n")[0]
            first = head.split(" ")[0] if head else ""
            path = first.split("?")[0] if first else "/"
            body = {}
            if "\r\n\r\n" in req:
                raw = req.split("\r\n\r\n")[1]
                if raw:
                    try:
                        body = json.loads(raw)
                    except Exception:
                        body = {}
            code, payload = handle(path, body)
            resp = json.dumps(payload)
            conn.sendall(
                f"HTTP/1.1 {code} OK\r\nContent-Type: application/json\r\n"
                f"Content-Length: {len(resp)}\r\nConnection: close\r\n\r\n{resp}"
            )
            conn.close()
        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass


boot_network()
serve()
