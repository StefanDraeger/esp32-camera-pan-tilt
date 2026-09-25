import gc
import os
import socket
import time
import network

try:
    import ujson as json
except ImportError:
    import json

import config
from servo import Servo
from web_page import render

try:
    import requests
except ImportError:
    try:
        import urequests as requests
    except ImportError:
        requests = None


PRESETS_FILE = "/presets.json"
PRESETS_TEMP_FILE = "/presets.tmp"
IMAGES_DIR = "/images"


def file_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def ensure_images_directory():
    if not file_exists(IMAGES_DIR):
        os.mkdir(IMAGES_DIR)


def load_presets():
    try:
        with open(PRESETS_FILE, "r") as file:
            data = json.load(file)
        result = []
        for item in data:
            result.append({
                "id": int(item["id"]),
                "name": str(item["name"]),
                "pan": max(config.PAN_MIN, min(config.PAN_MAX, int(item["pan"]))),
                "tilt": max(config.TILT_MIN, min(config.TILT_MAX, int(item["tilt"]))),
                "image": item.get("image"),
            })
        return result
    except (OSError, KeyError, TypeError, ValueError):
        return []


ensure_images_directory()
saved_presets = load_presets()


pan_servo = Servo(
    config.PAN_PIN,
    config.PAN_MIN,
    config.PAN_MAX,
    config.PAN_CENTER,
    config.SERVO_MIN_US,
    config.SERVO_MAX_US,
)

tilt_servo = Servo(
    config.TILT_PIN,
    config.TILT_MIN,
    config.TILT_MAX,
    config.TILT_CENTER,
    config.SERVO_MIN_US,
    config.SERVO_MAX_US,
)


def release_servos_after_movement():
    if config.SERVO_RELEASE_AFTER_MOVE:
        time.sleep_ms(config.SERVO_SETTLE_MS)
        pan_servo.release()
        tilt_servo.release()


sweep_active = False
sweep_direction = 1
sweep_next_step_ms = 0
sweep_interval_ms = config.SWEEP_INTERVAL_MS


def toggle_sweep():
    global sweep_active, sweep_direction, sweep_next_step_ms
    sweep_active = not sweep_active
    if sweep_active:
        sweep_direction = 1 if pan_servo.angle < config.PAN_MAX else -1
        sweep_next_step_ms = time.ticks_add(time.ticks_ms(), sweep_interval_ms)
        message = "Sweep gestartet"
    else:
        release_servos_after_movement()
        message = "Sweep gestoppt"
    return current_state(message), 200


def set_sweep_interval(value):
    global sweep_interval_ms
    try:
        value = int(value)
    except (TypeError, ValueError):
        return current_state("Ungueltiger Sweep-Takt"), 400

    sweep_interval_ms = max(
        config.SWEEP_INTERVAL_MIN_MS, min(config.SWEEP_INTERVAL_MAX_MS, value)
    )
    return current_state("Sweep-Takt auf %d ms gesetzt" % sweep_interval_ms), 200


def step_sweep():
    global sweep_direction, sweep_next_step_ms
    if not sweep_active:
        return

    now = time.ticks_ms()
    if time.ticks_diff(sweep_next_step_ms, now) > 0:
        return

    sweep_next_step_ms = time.ticks_add(now, sweep_interval_ms)
    angle = pan_servo.move(sweep_direction * config.SWEEP_STEP_DEGREES)
    if angle >= config.PAN_MAX:
        sweep_direction = -1
    elif angle <= config.PAN_MIN:
        sweep_direction = 1


def connect_wifi():
    if config.WIFI_SSID == "DEIN-WLAN-NAME":
        raise RuntimeError("Bitte zuerst die WLAN-Daten in config.py eintragen.")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Verbinde mit WLAN", end="")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        timeout = time.ticks_add(time.ticks_ms(), 20000)

        while not wlan.isconnected():
            if time.ticks_diff(timeout, time.ticks_ms()) <= 0:
                raise RuntimeError("WLAN-Verbindung fehlgeschlagen.")
            print(".", end="")
            time.sleep_ms(300)

    print("\nWLAN verbunden")
    print("IP-Adresse: http://%s" % wlan.ifconfig()[0])
    return wlan


def current_state(message=""):
    presets = []
    for preset in saved_presets:
        image_available = bool(preset["image"] and file_exists(
            IMAGES_DIR + "/" + preset["image"]
        ))
        presets.append({
            "id": preset["id"],
            "name": preset["name"],
            "pan": preset["pan"],
            "tilt": preset["tilt"],
            "image": image_available,
        })

    return {
        "pan": pan_servo.angle,
        "tilt": tilt_servo.angle,
        "message": message,
        "presets": presets,
        "sweep": sweep_active,
        "sweepIntervalMs": sweep_interval_ms,
        "controls": {
            "right": not sweep_active and pan_servo.angle > config.PAN_MIN,
            "left": not sweep_active and pan_servo.angle < config.PAN_MAX,
            "center": not sweep_active,
            "up": tilt_servo.angle > config.TILT_MIN,
            "down": tilt_servo.angle < config.TILT_MAX,
        },
    }


def save_presets_file():
    with open(PRESETS_TEMP_FILE, "w") as file:
        json.dump(saved_presets, file)
    if file_exists(PRESETS_FILE):
        os.remove(PRESETS_FILE)
    os.rename(PRESETS_TEMP_FILE, PRESETS_FILE)


def save_snapshot(target_path):
    if requests is None:
        raise RuntimeError("Das MicroPython-Paket requests ist nicht installiert")

    response = None
    try:
        response = requests.get(config.CAMERA_SNAPSHOT_URL)
        if response.status_code != 200:
            raise RuntimeError("Kamera antwortet mit HTTP %s" % response.status_code)

        temp_path = target_path + ".tmp"
        with open(temp_path, "wb") as image_file:
            while True:
                chunk = response.raw.read(1024)
                if not chunk:
                    break
                image_file.write(chunk)

        if file_exists(target_path):
            os.remove(target_path)
        os.rename(temp_path, target_path)
    finally:
        if response:
            response.close()
        temp_path = target_path + ".tmp"
        if file_exists(temp_path):
            os.remove(temp_path)


def save_current_position(name=""):
    next_id = max([item["id"] for item in saved_presets] or [0]) + 1
    name = str(name).strip()[:40] or "Position %d" % next_id
    image_name = "position_%d.jpg" % next_id
    preset = {
        "id": next_id,
        "name": name,
        "pan": pan_servo.angle,
        "tilt": tilt_servo.angle,
        "image": image_name,
    }

    try:
        save_snapshot(IMAGES_DIR + "/" + image_name)
        message = "Position und Kamerabild gespeichert"
    except Exception as error:
        print("Snapshot konnte nicht gespeichert werden:", error)
        preset["image"] = None
        message = "Position gespeichert, Kamerabild fehlgeschlagen"

    saved_presets.append(preset)
    save_presets_file()
    return current_state(message), 200


def find_preset(preset_id):
    try:
        preset_id = int(preset_id)
    except (TypeError, ValueError):
        return None
    for preset in saved_presets:
        if preset["id"] == preset_id:
            return preset
    return None


def move_to_saved_position(preset_id):
    if sweep_active:
        return current_state("Sweep aktiv, zuerst stoppen"), 409

    preset = find_preset(preset_id)
    if preset is None:
        return current_state("Gespeicherte Position nicht gefunden"), 404

    pan_servo.write(preset["pan"])
    tilt_servo.write(preset["tilt"])
    release_servos_after_movement()
    return current_state("%s angefahren" % preset["name"]), 200


def delete_saved_position(preset_id):
    preset = find_preset(preset_id)
    if preset is None:
        return current_state("Gespeicherte Position nicht gefunden"), 404

    if preset["image"]:
        image_path = IMAGES_DIR + "/" + preset["image"]
        if file_exists(image_path):
            os.remove(image_path)
    saved_presets.remove(preset)
    save_presets_file()
    return current_state("%s geloescht" % preset["name"]), 200


def move_camera(direction):
    if sweep_active and direction in ("left", "right", "center"):
        return current_state("Sweep aktiv, zuerst stoppen"), 409

    if direction == "left":
        pan_servo.move(config.MOVE_STEP)
        message = "Nach links bewegt"
    elif direction == "right":
        pan_servo.move(-config.MOVE_STEP)
        message = "Nach rechts bewegt"
    elif direction == "up":
        tilt_servo.move(-config.MOVE_STEP)
        message = "Nach oben bewegt"
    elif direction == "down":
        tilt_servo.move(config.MOVE_STEP)
        message = "Nach unten bewegt"
    elif direction == "center":
        pan_servo.write(config.PAN_CENTER)
        tilt_servo.write(config.TILT_CENTER)
        message = "Kamera zentriert"
    else:
        return current_state("Unbekannte Richtung"), 400

    release_servos_after_movement()
    return current_state(message), 200


def send_all(client, data):
    if isinstance(data, str):
        data = data.encode("utf-8")

    sent = 0
    while sent < len(data):
        count = client.send(data[sent:])
        if not count:
            raise OSError("Verbindung beim Senden geschlossen")
        sent += count


def send_response(client, body="", status="200 OK", content_type="text/html; charset=utf-8"):
    if isinstance(body, str):
        body = body.encode("utf-8")

    header = (
        "HTTP/1.1 %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %d\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n\r\n"
    ) % (status, content_type, len(body))

    send_all(client, header)
    send_all(client, body)


def send_file_response(client, path, content_type):
    size = os.stat(path)[6]
    header = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %d\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n\r\n"
    ) % (content_type, size)
    send_all(client, header)

    with open(path, "rb") as file:
        while True:
            chunk = file.read(1024)
            if not chunk:
                break
            send_all(client, chunk)


def parse_request(request):
    first_line = request.split("\r\n", 1)[0]
    parts = first_line.split(" ")
    if len(parts) < 2:
        return "/", {}

    target = parts[1]
    if "?" not in target:
        return target, {}

    path, query_string = target.split("?", 1)
    query = {}
    for pair in query_string.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            query[url_decode(key)] = url_decode(value)
    return path, query


def url_decode(value):
    value = value.replace("+", " ")
    result = bytearray()
    index = 0
    while index < len(value):
        if value[index] == "%" and index + 2 < len(value):
            try:
                result.append(int(value[index + 1:index + 3], 16))
                index += 3
                continue
            except ValueError:
                pass
        result.extend(value[index].encode("utf-8"))
        index += 1
    return result.decode("utf-8", "replace")


HTTP_STATUS_TEXT = {
    200: "200 OK",
    400: "400 Bad Request",
    404: "404 Not Found",
    409: "409 Conflict",
    500: "500 Internal Server Error",
}


def status_text(status_code):
    return HTTP_STATUS_TEXT.get(status_code, "500 Internal Server Error")


def run_server():
    address = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(address)
    server.listen(3)
    server.settimeout(config.SWEEP_POLL_SECONDS)
    print("Webserver gestartet")

    page = render(
        config.CAMERA_SNAPSHOT_URL,
        config.DEFAULT_REFRESH_SECONDS,
        sweep_interval_ms,
    )

    while True:
        step_sweep()

        client = None
        try:
            client, remote = server.accept()
        except OSError:
            continue

        try:
            client.settimeout(3)
            request = client.recv(2048).decode("utf-8", "ignore")
            path, query = parse_request(request)

            if path == "/":
                send_response(client, page)
            elif path == "/move":
                state, status_code = move_camera(query.get("direction", ""))
                send_response(client, json.dumps(state), status_text(status_code), "application/json")
            elif path == "/sweep/toggle":
                state, status_code = toggle_sweep()
                send_response(client, json.dumps(state), status_text(status_code), "application/json")
            elif path == "/sweep/interval":
                state, status_code = set_sweep_interval(query.get("ms"))
                send_response(client, json.dumps(state), status_text(status_code), "application/json")
            elif path == "/state":
                send_response(client, json.dumps(current_state()), "200 OK", "application/json")
            elif path == "/preset/save":
                state, status_code = save_current_position(query.get("name", ""))
                send_response(client, json.dumps(state), status_text(status_code), "application/json")
            elif path == "/preset/go":
                state, status_code = move_to_saved_position(query.get("id"))
                send_response(client, json.dumps(state), status_text(status_code), "application/json")
            elif path == "/preset/delete":
                state, status_code = delete_saved_position(query.get("id"))
                send_response(client, json.dumps(state), status_text(status_code), "application/json")
            elif path.startswith("/images/"):
                image_name = path[len("/images/"):]
                allowed = any(item["image"] == image_name for item in saved_presets)
                image_path = IMAGES_DIR + "/" + image_name
                if allowed and file_exists(image_path):
                    send_file_response(client, image_path, "image/jpeg")
                else:
                    send_response(client, "Kein Bild gespeichert", "404 Not Found", "text/plain")
            elif path == "/favicon.ico":
                send_response(client, "", "204 No Content", "text/plain")
            else:
                send_response(client, "Nicht gefunden", "404 Not Found", "text/plain; charset=utf-8")
        except Exception as error:
            print("HTTP-Fehler:", error)
        finally:
            if client:
                client.close()
            gc.collect()


release_servos_after_movement()
connect_wifi()
run_server()
