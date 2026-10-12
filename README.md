# Control virtual para PC (Android → Xbox 360 virtual)

Tu Samsung A56 funciona como un gamepad Xbox 360 para Steam.

## Requisitos (Windows 10/11)

1. **ViGEmBus** instalado: https://github.com/nefarius/ViGEmBus/releases (reinicia el PC después).
2. Python 3.10+
3. Dependencias:

```
pip install -r requirements.txt
```

`requirements.txt`:

```
vgamepad
aiohttp
```

## Uso

1. En el PC: `python server.py`
2. Verás una URL como `http://192.168.1.50:8080`.
3. En el celular (Chrome, misma red Wi-Fi) abre esa URL. Toca una vez la pantalla para activar pantalla completa.
4. Abre Steam → Configuración → Mando, o prueba en https://hardwaretester.com/gamepad

Si no carga: permite Python en el Firewall de Windows (red privada) o abre el puerto 8080.

## Por cable (menor latencia, sin Wi-Fi)

1. Activa Depuración USB en el celular y conéctalo.
2. `adb reverse tcp:8080 tcp:8080`
3. En el celular abre `http://localhost:8080`

## Protocolo (mensajes JSON por WebSocket)

- `{"t":"btn","b":"A","d":1}` botón (d=1 presionado, 0 suelto)
- `{"t":"stick","s":"L","x":0.5,"y":-1}` stick, valores -1..1
- `{"t":"trig","s":"R","v":1}` gatillo, 0..1
- Servidor → celular: `{"t":"rumble","l":0-255,"s":0-255}` vibración

## Siguientes pasos

- Gatillos analógicos (deslizar en vez de on/off).
- Pasar a TypeScript / app nativa (Flutter o Kotlin) si quieres mejor multitouch.
