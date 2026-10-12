"""
Servidor del control virtual.
- Sirve la interfaz web (index.html) al celular.
- Recibe inputs por WebSocket y los convierte en un gamepad Xbox 360 virtual (ViGEmBus).
- Reenvía la vibración del juego al celular.
"""
import asyncio
import json
import socket
from pathlib import Path

import vgamepad as vg
from aiohttp import web, WSMsgType

PORT = 8080
BASE = Path(__file__).parent

B = vg.XUSB_BUTTON
BUTTONS = {
    "A": B.XUSB_GAMEPAD_A,
    "B": B.XUSB_GAMEPAD_B,
    "X": B.XUSB_GAMEPAD_X,
    "Y": B.XUSB_GAMEPAD_Y,
    "LB": B.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB": B.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "BACK": B.XUSB_GAMEPAD_BACK,
    "START": B.XUSB_GAMEPAD_START,
    "L3": B.XUSB_GAMEPAD_LEFT_THUMB,
    "R3": B.XUSB_GAMEPAD_RIGHT_THUMB,
    "UP": B.XUSB_GAMEPAD_DPAD_UP,
    "DOWN": B.XUSB_GAMEPAD_DPAD_DOWN,
    "LEFT": B.XUSB_GAMEPAD_DPAD_LEFT,
    "RIGHT": B.XUSB_GAMEPAD_DPAD_RIGHT,
}

pad = vg.VX360Gamepad()
clients = set()
loop = None


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def reset_pad():
    pad.reset()
    pad.update()


def handle_message(msg):
    t = msg.get("t")
    if t == "btn":
        btn = BUTTONS.get(msg.get("b"))
        if btn is None:
            return
        if msg.get("d"):
            pad.press_button(button=btn)
        else:
            pad.release_button(button=btn)
    elif t == "stick":
        x = clamp(float(msg.get("x", 0)), -1.0, 1.0)
        y = clamp(float(msg.get("y", 0)), -1.0, 1.0)
        if msg.get("s") == "L":
            pad.left_joystick_float(x_value_float=x, y_value_float=y)
        else:
            pad.right_joystick_float(x_value_float=x, y_value_float=y)
    elif t == "trig":
        v = clamp(float(msg.get("v", 0)), 0.0, 1.0)
        if msg.get("s") == "L":
            pad.left_trigger_float(value_float=v)
        else:
            pad.right_trigger_float(value_float=v)
    pad.update()


async def broadcast(data):
    for ws in list(clients):
        try:
            await ws.send_str(data)
        except Exception:
            clients.discard(ws)


def on_rumble(client, target, large_motor, small_motor, led_number, user_data):
    # Se llama desde otro hilo -> lo pasamos al loop de asyncio
    # Si el loop ya se cerró (el servidor se está apagando), ignoramos la vibración
    if loop is None or loop.is_closed():
        return
    data = json.dumps({"t": "rumble", "l": large_motor, "s": small_motor})
    coro = broadcast(data)
    try:
        asyncio.run_coroutine_threadsafe(coro, loop)
    except RuntimeError:
        # El loop se cerró justo entre la comprobación y el envío.
        # Cerramos la corrutina para evitar el aviso "was never awaited".
        coro.close()


pad.register_notification(callback_function=on_rumble)


async def ws_handler(request):
    ws = web.WebSocketResponse(heartbeat=10)
    await ws.prepare(request)
    clients.add(ws)
    print("Celular conectado:", request.remote)
    try:
        async for m in ws:
            if m.type == WSMsgType.TEXT:
                try:
                    handle_message(json.loads(m.data))
                except Exception as e:
                    print("Mensaje inválido:", e)
    finally:
        clients.discard(ws)
        reset_pad()  # evita botones "pegados" si se corta la conexión
        print("Celular desconectado")
    return ws


async def index(request):
    return web.FileResponse(BASE / "index.html")


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


async def main():
    global loop
    loop = asyncio.get_running_loop()
    app = web.Application()
    app.add_routes([web.get("/", index), web.get("/ws", ws_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    print("=" * 50)
    print("Control virtual listo.")
    print(f"En el celular abre:  http://{local_ip()}:{PORT}")
    print(f"(o por cable con ADB: http://localhost:{PORT})")
    print("=" * 50)
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        reset_pad()
