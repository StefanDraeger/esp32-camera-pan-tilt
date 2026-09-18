"""Konfiguration fuer die Pan-Tilt-Kamerasteuerung."""

# WLAN-Zugangsdaten
WIFI_SSID = "DEIN-WLAN-NAME"
WIFI_PASSWORD = "DEIN-WLAN-PASSWORT"

# Snapshot-Adresse der Shelly Camera
CAMERA_SNAPSHOT_URL = "http://192.168.178.186/camera/0/snapshot"

# Anschluss der beiden Servos
# Pan/Schwenken an GPIO0, Tilt/Neigen an GPIO1
PAN_PIN = 0
TILT_PIN = 1

# Bewegungsgrenzen und Startpositionen in Grad
PAN_MIN = 0
PAN_MAX = 170
PAN_CENTER = 90

TILT_MIN = 0
TILT_MAX = 140
TILT_CENTER = 0

# Grad pro Tastendruck / Bewegungsschritt
MOVE_STEP = 5

# Aktualisierungsintervall des Snapshots in Sekunden
DEFAULT_REFRESH_SECONDS = 2

# Pulsbreiten des SG90. Bei Bedarf vorsichtig an den Servo anpassen.
SERVO_MIN_US = 500
SERVO_MAX_US = 2500

# PWM nach einer Bewegung abschalten, damit die Servos im Stillstand nicht
# dauerhaft summen. Ohne PWM halten sie ihre Position nicht aktiv gegen Last.
SERVO_RELEASE_AFTER_MOVE = True
SERVO_SETTLE_MS = 300
