# Shelly Camera Pan-Tilt-Steuerung mit MicroPython

Eine browserbasierte Pan-Tilt-Steuerung für die Shelly Camera mit einem
XIAO ESP32-C6 und zwei SG90-Servomotoren.

Der ESP32 stellt eine responsive Webseite bereit, über die sich die Kamera
schwenken und neigen lässt. Das Kamerabild wird regelmäßig über die
Snapshot-Adresse der Shelly Camera aktualisiert. Häufig verwendete Blickwinkel
können zusammen mit einem Referenzbild dauerhaft als Presets gespeichert werden.

**Aktueller Stand: Version 1.0.0**

## Funktionen

- Steuerung von zwei SG90-Servomotoren über eine responsive Webseite
- Bedienung über vier Pfeiltasten sowie eine Zentrieren-Schaltfläche
- Gedrückthalten einer Pfeiltaste für eine fortlaufende Bewegung
- Konfigurierbare Winkelgrenzen für beide Achsen
- Automatisches Deaktivieren der Pfeiltasten an den Endpositionen
- Einstellbares Aktualisierungsintervall für das Kamerabild
- Mehrere benannte Kamerapositionen als Presets
- Snapshot als Referenzbild zu jedem Preset
- Persistente Speicherung der Presets und Bilder im Flash des ESP32
- Direktes Anfahren und Löschen gespeicherter Positionen
- Optionale Abschaltung des PWM-Signals gegen Servo-Summen im Stillstand
- Keine zusätzliche App und kein externer Server erforderlich

## Benötigte Hardware

- Seeed Studio XIAO ESP32-C6 oder ein vergleichbarer ESP32
- Shelly Camera mit erreichbarer Snapshot-Adresse
- Pan-Tilt-Bausatz mit zwei SG90-Servomotoren
- Breadboard und Breadboardkabel
- Externe, auf 5 V eingestellte Stromversorgung mit ausreichender Leistung
- USB-Kabel für Programmierung und Stromversorgung des ESP32

## Anschluss

| Funktion | Anschluss am XIAO ESP32-C6 |
| --- | --- |
| Pan-Servo, Schwenken | GPIO0 |
| Tilt-Servo, Neigen | GPIO1 |
| Gemeinsame Masse | GND |

### Schaltplan

Die folgende Abbildung zeigt den Anschluss der beiden Servomotoren am
XIAO ESP32-C6 sowie die externe Stromversorgung:

![Schaltung des XIAO ESP32-C6 mit zwei Servomotoren](<images/Schaltung - XIAO ESP32-C6 mit Servomotoren.webp>)

Die Signalleitungen der Servos werden direkt mit den konfigurierten GPIOs
verbunden. Die roten Leitungen der Servos kommen an den Pluspol der externen
5-V-Stromversorgung. Die braunen beziehungsweise schwarzen Leitungen werden
mit deren Minuspol verbunden.

> [!IMPORTANT]
> Der Minuspol der externen Stromversorgung muss zusätzlich mit GND des
> XIAO ESP32-C6 verbunden werden. Ohne diese gemeinsame Masse können die
> Steuersignale nicht zuverlässig ausgewertet werden.

> [!WARNING]
> Die beiden SG90-Servos dürfen nicht über den 5-V-Anschluss des XIAO versorgt
> werden. Beim Anlaufen oder Blockieren können sie deutlich mehr Strom aufnehmen,
> als der Mikrocontroller bereitstellen kann. Das kann zu Spannungseinbrüchen,
> unkontrollierten Bewegungen oder Neustarts führen. Ein regelbares Netzteil muss
> vor dem Anschluss auf 5 V eingestellt werden.

## Softwarevoraussetzungen

- MicroPython-Firmware für den XIAO ESP32-C6
- Thonny IDE oder ein vergleichbares MicroPython-Werkzeug
- MicroPython-Paket `requests` beziehungsweise `urequests`
- WLAN-Verbindung für ESP32 und Shelly Camera
- Moderner Webbrowser im selben Netzwerk

Das Paket `requests` wird benötigt, damit der ESP32 beim Speichern eines Presets
selbstständig einen Snapshot von der Shelly Camera herunterladen kann. Fehlt das
Paket in der verwendeten Firmware, kann es über die Paketverwaltung von Thonny
auf dem Mikrocontroller installiert werden.

## Projektstruktur

```text
xiao-pan-tilt-micropython/
├── config.py       # WLAN, Kamera-URL, Pins und Bewegungsgrenzen
├── main.py         # WLAN, Webserver, Steuerung und Preset-Verwaltung
├── servo.py        # PWM-Ansteuerung der Servomotoren
├── web_page.py     # HTML, CSS und JavaScript der Bedienoberfläche
├── VERSION         # Versionsnummer des eingefrorenen Stands
└── README.md
```

Nach dem ersten Speichern einer Kameraposition entstehen auf dem ESP32 zusätzlich:

```text
/
├── presets.json
└── images/
    ├── position_1.jpg
    ├── position_2.jpg
    └── ...
```

## Konfiguration

Vor dem Übertragen der Dateien müssen in `config.py` mindestens WLAN und
Snapshot-Adresse angepasst werden:

```python
WIFI_SSID = "DEIN-WLAN-NAME"
WIFI_PASSWORD = "DEIN-WLAN-PASSWORT"

CAMERA_SNAPSHOT_URL = "http://192.168.178.186/camera/0/snapshot"
```

Die aktuelle Pinbelegung und die mechanisch ermittelten Winkelgrenzen lauten:

```python
PAN_PIN = 0
TILT_PIN = 1

PAN_MIN = 0
PAN_MAX = 170
PAN_CENTER = 90

TILT_MIN = 0
TILT_MAX = 140
TILT_CENTER = 0

MOVE_STEP = 5
```

Die Werte müssen bei einem anderen Pan-Tilt-Bausatz gegebenenfalls an dessen
mechanische Grenzen angepasst werden. Fährt ein Servo gegen einen Anschlag,
ist die Bewegung sofort zu stoppen und der Bereich zu verkleinern.

### Summen im Stillstand reduzieren

Standardmäßig wird das PWM-Signal 300 Millisekunden nach einer Bewegung
abgeschaltet:

```python
SERVO_RELEASE_AFTER_MOVE = True
SERVO_SETTLE_MS = 300
```

Das unterbindet bei vielen SG90-Servos das Summen im Stillstand. Nach dem
Abschalten hält der Servo seine Position allerdings nicht mehr aktiv gegen
äußere Kräfte. Sinkt die Kamera ab, kann die Funktion deaktiviert werden:

```python
SERVO_RELEASE_AFTER_MOVE = False
```

Starkes dauerhaftes Brummen kann außerdem auf einen mechanischen Anschlag,
eine schwergängige Halterung, ungeeignete Pulsbreiten oder eine instabile
Stromversorgung hinweisen.

## Installation

1. Eine passende MicroPython-Firmware auf den XIAO ESP32-C6 flashen.
2. Falls erforderlich, `requests` oder `urequests` über Thonny installieren.
3. WLAN-Zugangsdaten und Snapshot-Adresse in `config.py` eintragen.
4. `config.py`, `main.py`, `servo.py` und `web_page.py` in das
   Hauptverzeichnis des ESP32 übertragen.
5. Den Mikrocontroller neu starten.
6. Die im Terminal ausgegebene IP-Adresse im Browser öffnen.

Beispiel:

```text
WLAN verbunden
IP-Adresse: http://192.168.178.120
Webserver gestartet
```

## Bedienung

Die Pfeiltasten bewegen die Kamera in den vier Richtungen. Eine Taste kann
gedrückt gehalten werden, um mehrere Bewegungsschritte auszuführen. Sobald eine
konfigurierte Grenze erreicht ist, wird die betreffende Schaltfläche automatisch
deaktiviert. Über `ZENTRIEREN` fährt die Kamera zu den in `config.py`
hinterlegten Startpositionen.

Das Intervall unterhalb der Steuerung legt fest, wie häufig der Browser einen
neuen Snapshot lädt. Die Einstellung wird im lokalen Speicher des Browsers
gesichert.

### Kameraposition speichern

1. Kamera mit den Pfeiltasten ausrichten.
2. Einen Namen wie `Eingang`, `Werkbank` oder `3D-Drucker` eintragen.
3. `POSITION + BILD SPEICHERN` auswählen.

Der ESP32 speichert die aktuellen Winkel in `presets.json` und lädt gleichzeitig
einen Snapshot in das Verzeichnis `images`. Kann das Bild nicht geladen werden,
bleibt die Position trotzdem gespeichert und die Webseite zeigt einen Hinweis.

Gespeicherte Positionen erscheinen sofort als Karten mit Name, Koordinaten und
Referenzbild. Über `ANFAHREN` werden die gespeicherten Winkel angesteuert. Beim
Anfahren bleiben die Vorschaubilder geladen; nur Positionsanzeige und Tastenstatus
werden aktualisiert. `LÖSCHEN` entfernt sowohl den JSON-Eintrag als auch das Bild.

## Persistente Speicherung

Alle Presets bleiben nach einem Neustart erhalten. Eine mögliche
`presets.json` sieht so aus:

```json
[
  {
    "id": 1,
    "name": "Eingang",
    "pan": 35,
    "tilt": 60,
    "image": "position_1.jpg"
  },
  {
    "id": 2,
    "name": "Werkbank",
    "pan": 125,
    "tilt": 90,
    "image": "position_2.jpg"
  }
]
```

Die IDs werden fortlaufend vergeben. Die JSON-Datei sollte nicht während eines
Schreibvorgangs manuell bearbeitet werden.

## HTTP-Endpunkte

| Endpunkt | Funktion |
| --- | --- |
| `/` | Bedienoberfläche |
| `/state` | Aktueller Zustand, Grenzen und Presets als JSON |
| `/move?direction=left` | Kamera nach links bewegen |
| `/move?direction=right` | Kamera nach rechts bewegen |
| `/move?direction=up` | Kamera nach oben bewegen |
| `/move?direction=down` | Kamera nach unten bewegen |
| `/move?direction=center` | Kamera zentrieren |
| `/preset/save?name=Eingang` | Position und Snapshot speichern |
| `/preset/go?id=1` | Gespeicherte Position anfahren |
| `/preset/delete?id=1` | Position und Referenzbild löschen |
| `/images/position_1.jpg` | Gespeichertes Referenzbild ausliefern |

## Kamerabild und RTSP

Moderne Browser können einen RTSP-Stream normalerweise nicht direkt wiedergeben.
Dieses Projekt verwendet deshalb die Snapshot-Adresse der Shelly Camera:

```text
http://KAMERA-IP/camera/0/snapshot
```

Das Bild wird vom Browser in einem einstellbaren Intervall neu geladen. Ein
flüssiges Livebild kann weiterhin über das Webfrontend der Shelly Camera oder
die Shelly Smart Control App aufgerufen werden.

## Fehlerbehebung

### Das Kamerabild wird nicht angezeigt

- Snapshot-Adresse direkt im Browser testen.
- Prüfen, ob ESP32, Browser und Kamera dasselbe Netzwerk erreichen können.
- IP-Adresse der Kamera in `config.py` kontrollieren.
- Prüfen, ob die Kamera eine Anmeldung verlangt.

### Die Position wird gespeichert, das Bild jedoch nicht

- `requests` beziehungsweise `urequests` auf dem ESP32 installieren.
- Snapshot-Adresse und Netzwerkverbindung prüfen.
- Im seriellen Terminal nach der Meldung
  `Snapshot konnte nicht gespeichert werden` suchen.
- Freien Flash-Speicher des ESP32 kontrollieren.

### Ein Servo bewegt sich in die falsche Richtung

In `main.py` bei der betreffenden Richtung das Vorzeichen von
`config.MOVE_STEP` tauschen.

### Der ESP32 startet bei einer Bewegung neu

In der Regel ist die Servostromversorgung zu schwach oder die gemeinsame Masse
fehlt. Beide Servos müssen extern mit 5 V versorgt werden. Der Minuspol der
externen Versorgung muss mit GND des ESP32 verbunden sein.

### Der Servo fährt gegen den Anschlag oder brummt stark

Die Werte `PAN_MIN`, `PAN_MAX`, `TILT_MIN` und `TILT_MAX` verkleinern.
Die Pulsbreiten `SERVO_MIN_US` und `SERVO_MAX_US` nicht vergrößern, wenn der
Servo bereits am mechanischen Anschlag steht.

## Grenzen der Version 1.0.0

- Die Webseite besitzt keine Benutzeranmeldung und sollte nur in einem
  vertrauenswürdigen lokalen Netzwerk verwendet werden.
- Es wird ein periodisch aktualisiertes Standbild und kein Videostream angezeigt.
- Die Zahl der Presets wird nur durch den verfügbaren Flash-Speicher begrenzt.
- Sehr häufiges Speichern und Löschen verursacht Schreibzugriffe auf den Flash.
- Die Steuerung verwendet einen einfachen, synchronen Webserver.

## Autor und weiterführende Informationen

Projekt von **Stefan Draeger**.

Weitere Projekte rund um ESP32, Arduino, MicroPython und Smart Home:
[draeger-it.blog](https://draeger-it.blog/)
