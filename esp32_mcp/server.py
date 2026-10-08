# -*- coding: utf-8 -*-
"""ESP32 MCP Server —— 让 AI agent 直接控制/读取 ESP32 物联网设备
模式：ESP32 烧录配套 MicroPython 固件（暴露轻量 REST），本 server 通过 HTTP 调用。
传输：stdio（本地）+ HTTP/SSE（远程 agent 用）。环境变量 ESP32_HOST 指向设备地址。
"""
import os
import json
import urllib.request
from typing import Optional
from fastmcp import FastMCP

mcp = FastMCP("esp32-control")

ESP32_HOST = os.environ.get("ESP32_HOST", "http://192.168.4.1")
TIMEOUT = 8


def _call(path: str, payload: Optional[dict] = None) -> dict:
    url = f"{ESP32_HOST}{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


@mcp.tool()
def esp32_status() -> dict:
    """Get ESP32 device status: online, chip, firmware, free heap, uptime."""
    return _call("/api/status")


@mcp.tool()
def gpio_set(pin: int, level: int) -> dict:
    """Set an ESP32 GPIO pin high (1) or low (0). Args: pin (GPIO number), level (0 or 1)."""
    if level not in (0, 1):
        raise ValueError("level must be 0 or 1")
    return _call("/api/gpio", {"pin": int(pin), "level": int(level)})


@mcp.tool()
def gpio_read(pin: int) -> dict:
    """Read the current digital level (0/1) of an ESP32 GPIO pin. Args: pin."""
    return _call("/api/gpio/read", {"pin": int(pin)})


@mcp.tool()
def adc_read(pin: int) -> dict:
    """Read analog value from an ESP32 ADC-capable pin (e.g. 32-39 on ESP32, returns mV). Args: pin."""
    return _call("/api/adc", {"pin": int(pin)})


@mcp.tool()
def esp32_send_command(command: str) -> dict:
    """Send a raw AT/application command to the ESP32 and return its response. Args: command string."""
    return _call("/api/cmd", {"cmd": command})


@mcp.tool()
def esp32_reboot() -> dict:
    """Reboot the ESP32 device remotely."""
    return _call("/api/reboot")


if __name__ == "__main__":
    mcp.run()
