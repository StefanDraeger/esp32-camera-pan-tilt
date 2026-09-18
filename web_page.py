try:
    import ujson as json
except ImportError:
    import json


def render(snapshot_url, refresh_seconds):
    """Erzeugt die komplette Bedienoberflaeche."""
    safe_url = json.dumps(snapshot_url)
    return """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Pan-Tilt-Kamerasteuerung</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #0d1218; color: #edf3f8; }
    main { width: min(760px, calc(100%% - 24px)); margin: 20px auto 36px; }
    h1 { margin: 0 0 6px; font-size: clamp(1.4rem, 5vw, 2rem); }
    .sub { margin: 0 0 18px; color: #aebbc8; }
    .card { background: #171f29; border: 1px solid #2d3948; border-radius: 16px;
            padding: 14px; box-shadow: 0 14px 36px #0005; }
    .camera { position: relative; min-height: 220px; display: grid; place-items: center;
              overflow: hidden; background: #050708; border-radius: 11px; }
    .camera img { display: block; width: 100%%; height: auto; max-height: 62vh;
                  object-fit: contain; }
    .camera .error { position: absolute; padding: 14px; text-align: center;
                     color: #ffbd72; display: none; }
    .status { display: flex; justify-content: space-between; gap: 12px;
              flex-wrap: wrap; margin: 12px 2px 0; color: #aebbc8; font-size: .92rem; }
    .controls { display: grid; grid-template-columns: repeat(3, 74px);
                justify-content: center; gap: 10px; margin: 22px 0; }
    button { min-height: 58px; border: 0; border-radius: 13px; background: #263445;
             color: #fff; font-size: 1.55rem; font-weight: 700; cursor: pointer;
             touch-action: manipulation; user-select: none; }
    button:hover { background: #33475d; }
    button:active { transform: scale(.96); background: #13a89e; }
    button:disabled { background: #1b242e; color: #667483; cursor: not-allowed;
                      opacity: .55; transform: none; }
    .up { grid-column: 2; }
    .left { grid-column: 1; grid-row: 2; }
    .center { grid-column: 2; grid-row: 2; font-size: .78rem; }
    .right { grid-column: 3; grid-row: 2; }
    .down { grid-column: 2; grid-row: 3; }
    .settings { display: flex; align-items: center; justify-content: center;
                gap: 10px; flex-wrap: wrap; padding-top: 4px; }
    input { width: 92px; padding: 10px; border-radius: 9px; border: 1px solid #44546a;
            background: #0f151d; color: #fff; font: inherit; }
    .message { min-height: 1.4em; margin-top: 10px; text-align: center; color: #8cded8; }
    .preset-save { display: grid; grid-template-columns: 1fr auto; gap: 10px;
                   margin: 8px 0 16px; }
    .preset-save input { width: 100%%; }
    .preset-save button, .preset-card button { min-height: 44px; padding: 8px 12px;
                                               font-size: .9rem; }
    .preset-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                   gap: 12px; margin-bottom: 16px; }
    .preset-empty { grid-column: 1 / -1; text-align: center; color: #8493a3;
                    padding: 12px; }
    .preset-card { overflow: hidden; border: 1px solid #344255; border-radius: 11px;
                   background: #10171f; }
    .preset-card img { display: block; width: 100%%; aspect-ratio: 16 / 9;
                       object-fit: cover; background: #080b0f; }
    .preset-content { padding: 10px; }
    .preset-content h3 { margin: 0 0 4px; font-size: 1rem; }
    .preset-coordinates { color: #aebbc8; font-size: .86rem; }
    .preset-buttons { display: grid; grid-template-columns: 1fr auto; gap: 8px;
                      margin-top: 10px; }
    .preset-delete { background: #62313a; }
  </style>
</head>
<body>
  <main>
    <h1>Pan-Tilt-Kamerasteuerung</h1>
    <p class="sub">Shelly Camera mit XIAO ESP32-C6</p>

    <section class="card">
      <div class="camera">
        <img id="cameraImage" alt="Snapshot der Shelly Camera" referrerpolicy="no-referrer">
        <div id="cameraError" class="error">Das Kamerabild konnte nicht geladen werden.</div>
      </div>
      <div class="status">
        <span id="position">Pan: --° · Tilt: --°</span>
        <span id="lastUpdate">Noch nicht aktualisiert</span>
      </div>

      <div class="controls" aria-label="Kamerasteuerung">
        <button class="up" data-direction="up" aria-label="Nach oben">▲</button>
        <button class="left" data-direction="left" aria-label="Nach links">◀</button>
        <button class="center" data-direction="center">ZENTRIEREN</button>
        <button class="right" data-direction="right" aria-label="Nach rechts">▶</button>
        <button class="down" data-direction="down" aria-label="Nach unten">▼</button>
      </div>

      <div class="preset-save">
        <input id="presetName" type="text" maxlength="40" placeholder="Name, z. B. Eingang">
        <button id="savePreset" type="button">POSITION + BILD SPEICHERN</button>
      </div>
      <div id="presetList" class="preset-list"></div>

      <div class="settings">
        <label for="refreshSeconds">Bild aktualisieren alle</label>
        <input id="refreshSeconds" type="number" min="1" max="60" step="1" value="%d">
        <span>Sekunden</span>
      </div>
      <div id="message" class="message"></div>
    </section>
  </main>

  <script>
    const snapshotUrl = %s;
    const image = document.getElementById('cameraImage');
    const imageError = document.getElementById('cameraError');
    const intervalInput = document.getElementById('refreshSeconds');
    const position = document.getElementById('position');
    const lastUpdate = document.getElementById('lastUpdate');
    const message = document.getElementById('message');
    const presetName = document.getElementById('presetName');
    const savePreset = document.getElementById('savePreset');
    const presetList = document.getElementById('presetList');
    let refreshTimer;
    let holdTimer;
    let holdDirection;
    let currentState;
    let renderedPresetsSignature = '';

    function updateControls(state) {
      if (!state.controls) return;
      for (const [direction, enabled] of Object.entries(state.controls)) {
        const button = document.querySelector(`[data-direction="${direction}"]`);
        if (button) button.disabled = !enabled;
      }

      // Beim Erreichen einer Grenze keine weiteren Wiederholungen senden.
      if (holdDirection && state.controls[holdDirection] === false) {
        clearInterval(holdTimer);
        holdDirection = undefined;
      }
    }

    function showState(state) {
      currentState = state;
      position.textContent = `Pan: ${state.pan}° · Tilt: ${state.tilt}°`;
      updateControls(state);
      const presets = state.presets || [];
      const signature = JSON.stringify(presets);
      if (signature !== renderedPresetsSignature) {
        renderPresets(presets);
        renderedPresetsSignature = signature;
      }
    }

    function renderPresets(presets) {
      presetList.replaceChildren();
      if (!presets.length) {
        const empty = document.createElement('div');
        empty.className = 'preset-empty';
        empty.textContent = 'Noch keine Position gespeichert.';
        presetList.appendChild(empty);
        return;
      }

      for (const preset of presets) {
        const card = document.createElement('article');
        card.className = 'preset-card';

        if (preset.image) {
          const preview = document.createElement('img');
          preview.src = `/images/position_${preset.id}.jpg?_=${Date.now()}`;
          preview.alt = `Kamerabild: ${preset.name}`;
          card.appendChild(preview);
        }

        const content = document.createElement('div');
        content.className = 'preset-content';
        const title = document.createElement('h3');
        title.textContent = preset.name;
        const coordinates = document.createElement('div');
        coordinates.className = 'preset-coordinates';
        coordinates.textContent = `Pan: ${preset.pan}° · Tilt: ${preset.tilt}°`;

        const buttons = document.createElement('div');
        buttons.className = 'preset-buttons';
        const goButton = document.createElement('button');
        goButton.type = 'button';
        goButton.textContent = 'ANFAHREN';
        goButton.addEventListener('click', () => presetAction('go', preset.id));
        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.className = 'preset-delete';
        deleteButton.textContent = 'LÖSCHEN';
        deleteButton.addEventListener('click', () => presetAction('delete', preset.id));

        buttons.append(goButton, deleteButton);
        content.append(title, coordinates, buttons);
        card.appendChild(content);
        presetList.appendChild(card);
      }
    }

    async function presetAction(action, id) {
      savePreset.disabled = true;
      try {
        let url = '/preset/' + action;
        if (action === 'save') {
          url += '?name=' + encodeURIComponent(presetName.value.trim());
        } else {
          url += '?id=' + encodeURIComponent(id);
        }
        const response = await fetch(url, { cache: 'no-store' });
        const state = await response.json();
        if (!response.ok) throw new Error(state.message || 'HTTP ' + response.status);
        showState(state);
        message.textContent = state.message || '';
        if (action === 'save') {
          presetName.value = '';
          refreshImage();
        }
      } catch (error) {
        message.textContent = error.message || 'Preset-Aktion fehlgeschlagen';
      } finally {
        savePreset.disabled = false;
        if (currentState) showState(currentState);
      }
    }

    function refreshImage() {
      const separator = snapshotUrl.includes('?') ? '&' : '?';
      imageError.style.display = 'none';
      image.src = snapshotUrl + separator + '_=' + Date.now();
    }

    image.addEventListener('load', () => {
      lastUpdate.textContent = 'Aktualisiert: ' + new Date().toLocaleTimeString();
      imageError.style.display = 'none';
    });
    image.addEventListener('error', () => {
      imageError.style.display = 'block';
    });

    function setRefreshTimer() {
      let seconds = Number(intervalInput.value);
      seconds = Math.max(1, Math.min(60, Number.isFinite(seconds) ? seconds : 2));
      intervalInput.value = seconds;
      clearInterval(refreshTimer);
      refreshTimer = setInterval(refreshImage, seconds * 1000);
      localStorage.setItem('panTiltRefreshSeconds', seconds);
    }

    async function move(direction) {
      try {
        const response = await fetch('/move?direction=' + encodeURIComponent(direction), {
          cache: 'no-store'
        });
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const state = await response.json();
        showState(state);
        message.textContent = state.message || '';
        if (direction !== 'center') refreshImage();
      } catch (error) {
        message.textContent = 'Steuerbefehl fehlgeschlagen';
      }
    }

    document.querySelectorAll('[data-direction]').forEach(button => {
      const direction = button.dataset.direction;
      button.addEventListener('pointerdown', event => {
        event.preventDefault();
        move(direction);
        if (direction !== 'center') {
          holdDirection = direction;
          holdTimer = setInterval(() => move(direction), 220);
        }
      });
      ['pointerup', 'pointercancel', 'pointerleave'].forEach(name => {
        button.addEventListener(name, () => {
          clearInterval(holdTimer);
          holdDirection = undefined;
        });
      });
    });

    intervalInput.addEventListener('change', setRefreshTimer);
    savePreset.addEventListener('click', () => presetAction('save'));
    const savedInterval = Number(localStorage.getItem('panTiltRefreshSeconds'));
    if (savedInterval >= 1 && savedInterval <= 60) intervalInput.value = savedInterval;
    setRefreshTimer();
    refreshImage();
    fetch('/state').then(response => response.json()).then(state => {
      showState(state);
    }).catch(() => {});
  </script>
</body>
</html>""" % (refresh_seconds, safe_url)
