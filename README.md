# ESP32 MCP Server

Control and read ESP32 IoT devices directly from AI agents (Claude, Cursor, any MCP client).

- `esp32.status` — online / chip / free heap / uptime
- `esp32.gpio_set` — set a GPIO high/low
- `esp32.gpio_read` — read a digital pin
- `esp32.adc_read` — read analog voltage (mV)
- `esp32.send_command` — raw AT/application command
- `esp32.reboot` — reboot the device

## Architecture

```
AI agent (Claude/Cursor)  →  this MCP server (Python)  →  ESP32 REST API  →  device
```

The ESP32 runs a tiny MicroPython firmware (`esp32_firmware/main.py`) exposing a
lightweight REST API on port 80. The MCP server talks to it over HTTP — works
locally and remotely.

## Quick start

### 1. Flash the ESP32 firmware

1. Install [MicroPython](https://micropython.org/download/ESP32_GENERIC/) on your ESP32.
2. Upload `esp32_firmware/main.py` as `main.py` (Thonny or `mpremote`).
3. Power on — the device opens a WiFi AP named `ESP32-MCP` (password `12345678`)
   or you can set STA mode inside the firmware to join your network.

### 2. Run the MCP server

```bash
pip install esp32-mcp
export ESP32_HOST=http://192.168.4.1     # device address (AP default)
esp32-mcp                                  # stdio transport (local MCP client)
```

For remote agents, run with HTTP transport:

```bash
uv run esp32-mcp --transport http --port 8000
```

### 3. Add to your AI client

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "esp32": {
      "command": "esp32-mcp",
      "env": { "ESP32_HOST": "http://192.168.4.1" }
    }
  }
}
```

**Cursor**: Settings → MCP → Add server → `esp32-mcp` with env `ESP32_HOST`.

Then just ask: *"turn GPIO 2 on"*, *"what's the ADC reading on pin 34?"*,
*"reboot the device"*.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `ESP32_HOST` | `http://192.168.4.1` | ESP32 REST endpoint |
| `ESP32_TIMEOUT` | 8 | request timeout (s) |

## Safety

- GPIO outputs are limited to pins `2, 4, 5, 18, 19` by default (edit `GPIO_OUT`
  in the firmware to change).
- The firmware only listens on its own network; change the AP password before
  exposing to the internet.

## License

MIT
