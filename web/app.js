/* Lingo — interactive visualiser.
   A faithful browser port of the Python Naming Game engine, drawn live on a
   canvas. The simulation rules here match lingo/game.py exactly so the demo
   and the paper experiments tell the same story. */

(() => {
  "use strict";

  // ---- Simulation engine (mirrors lingo/) --------------------------------

  let wordCounter = 0;
  function inventWord() {
    const a = String.fromCharCode(97 + Math.floor(Math.random() * 26));
    const b = String.fromCharCode(97 + Math.floor(Math.random() * 26));
    return a + b + wordCounter++;
  }

  // Build the edges that decide who may talk to whom.
  function buildNeighbours(type, n) {
    const nb = Array.from({ length: n }, () => new Set());
    const link = (a, b) => { if (a !== b) { nb[a].add(b); nb[b].add(a); } };

    if (type === "fully_connected") {
      for (let i = 0; i < n; i++)
        for (let j = i + 1; j < n; j++) link(i, j);
    } else if (type === "grid") {
      const cols = Math.ceil(Math.sqrt(n));
      for (let i = 0; i < n; i++) {
        const r = Math.floor(i / cols), c = i % cols;
        if (c + 1 < cols && i + 1 < n) link(i, i + 1);          // right
        if (i + cols < n) link(i, i + cols);                    // down
      }
    } else { // small_world: ring lattice (k=4) with a little rewiring
      const k = 4;
      for (let i = 0; i < n; i++)
        for (let j = 1; j <= k / 2; j++) link(i, (i + j) % n);
      for (let i = 0; i < n; i++) {
        if (Math.random() < 0.1) {
          const target = Math.floor(Math.random() * n);
          link(i, target);
        }
      }
    }
    return nb.map((s) => [...s]);
  }

  // Place agents in the viewport: a grid for the grid network, a ring otherwise.
  function layout(type, n, w, h) {
    const pos = [];
    const pad = 48;
    if (type === "grid") {
      const cols = Math.ceil(Math.sqrt(n));
      const rows = Math.ceil(n / cols);
      const sx = (w - 2 * pad) / Math.max(cols - 1, 1);
      const sy = (h - 2 * pad) / Math.max(rows - 1, 1);
      for (let i = 0; i < n; i++)
        pos.push({ x: pad + (i % cols) * sx, y: pad + Math.floor(i / cols) * sy });
    } else {
      const cx = w / 2, cy = h / 2, R = Math.min(w, h) / 2 - pad;
      for (let i = 0; i < n; i++) {
        const a = (2 * Math.PI * i) / n - Math.PI / 2;
        pos.push({ x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) });
      }
    }
    return pos;
  }

  class Simulation {
    constructor(n, meanings, network, noise) {
      this.n = n;
      this.meanings = meanings;
      this.noise = noise;
      this.network = network;
      this.neighbours = buildNeighbours(network, n);
      // inventory[agent][meaning] = array of known words
      this.inv = Array.from({ length: n }, () =>
        Array.from({ length: meanings }, () => []));
      this.steps = 0;
      this.recent = [];           // rolling window of recent outcomes
      this.window = Math.max(50, n);
      this.lastEvent = null;      // details of the most recent interaction
    }

    step() {
      const s = (Math.random() * this.n) | 0;
      const nb = this.neighbours[s];
      if (nb.length === 0) return;
      const h = nb[(Math.random() * nb.length) | 0];
      const m = (Math.random() * this.meanings) | 0;

      // Speaker produces a word (invents one if it knows none).
      const sWords = this.inv[s][m];
      let word;
      if (sWords.length === 0) { word = inventWord(); sWords.push(word); }
      else word = sWords[(Math.random() * sWords.length) | 0];

      // Noise may garble the word in transit.
      let sent = word;
      if (this.noise > 0 && Math.random() < this.noise) sent = inventWord();

      this.steps++;
      const hWords = this.inv[h][m];
      const known = hWords.includes(sent);
      if (known) {
        // Success: both collapse to the single agreed word.
        this.inv[s][m] = [sent];
        this.inv[h][m] = [sent];
        this._record(1);
      } else {
        // Failure: hearer files the word away.
        hWords.push(sent);
        this._record(0);
      }
      // Remember the last event so the UI can show what just happened.
      this.lastEvent = { s, h, m, word: sent, success: known };
    }

    _record(outcome) {
      this.recent.push(outcome);
      if (this.recent.length > this.window) this.recent.shift();
    }

    successRate() {
      if (!this.recent.length) return 0;
      return this.recent.reduce((a, b) => a + b, 0) / this.recent.length;
    }

    preferred(agent, meaning) {
      const w = this.inv[agent][meaning];
      return w.length ? w[0] : null;
    }

    distinctWords() {
      let total = 0;
      for (let m = 0; m < this.meanings; m++) {
        const set = new Set();
        for (let i = 0; i < this.n; i++)
          for (const w of this.inv[i][m]) set.add(w);
        total += set.size;
      }
      return total;
    }

    dialects() {
      const langs = new Set();
      for (let i = 0; i < this.n; i++) {
        let key = "";
        for (let m = 0; m < this.meanings; m++) key += "|" + this.preferred(i, m);
        langs.add(key);
      }
      return langs.size;
    }
  }

  // ---- Colour mapping: each word gets a stable, distinct hue --------------

  function wordColour(word) {
    if (!word) return "#3a3f4b"; // grey for "no word yet"
    let hash = 0;
    for (let i = 0; i < word.length; i++)
      hash = (hash * 31 + word.charCodeAt(i)) >>> 0;
    const hue = hash % 360;
    const sat = 60 + (hash % 25);
    const light = 55 + (hash % 15);
    return `hsl(${hue} ${sat}% ${light}%)`;
  }

  // ---- Wiring the UI ------------------------------------------------------

  const canvas = document.getElementById("canvas");
  const ctx = canvas.getContext("2d");
  const el = (id) => document.getElementById(id);

  const ui = {
    pop: el("pop"), meanings: el("meanings"), noise: el("noise"),
    speed: el("speed"), network: el("network"), viewMeaning: el("viewMeaning"),
    showEdges: el("showEdges"), play: el("playBtn"), reset: el("resetBtn"),
  };

  let sim, positions, running = true, viewMeaning = 0;
  let selectedAgent = null;     // which agent the inspector is showing
  let logBuffer = [];           // recent interactions, newest last
  let framesSinceLog = 0;
  let lastTextUpdate = 0;       // throttle for readable on-screen numbers

  function rebuild() {
    const n = +ui.pop.value;
    const meanings = +ui.meanings.value;
    const noise = +ui.noise.value / 100;
    const network = ui.network.value;

    sim = new Simulation(n, meanings, network, noise);
    positions = layout(network, n, canvas.width, canvas.height);

    // Refresh the "view meaning" dropdown to match the meaning count.
    ui.viewMeaning.innerHTML = "";
    for (let m = 0; m < meanings; m++) {
      const opt = document.createElement("option");
      opt.value = m; opt.textContent = `Meaning ${m + 1}`;
      ui.viewMeaning.appendChild(opt);
    }
    viewMeaning = 0;
    selectedAgent = null;
    logBuffer = [];
    renderInspector();
    renderLog();
    draw();
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Network connections (optional; skipped for dense fully-connected graphs).
    if (ui.showEdges.checked && !(sim.network === "fully_connected" && sim.n > 40)) {
      ctx.strokeStyle = "rgba(138,144,156,0.12)";
      ctx.lineWidth = 1;
      for (let i = 0; i < sim.n; i++)
        for (const j of sim.neighbours[i]) {
          if (j <= i) continue;
          ctx.beginPath();
          ctx.moveTo(positions[i].x, positions[i].y);
          ctx.lineTo(positions[j].x, positions[j].y);
          ctx.stroke();
        }
    }

    // Agents as glowing dots; colour = currently preferred word.
    const r = Math.max(4, Math.min(11, 90 / Math.sqrt(sim.n)));
    for (let i = 0; i < sim.n; i++) {
      const colour = wordColour(sim.preferred(i, viewMeaning));
      ctx.beginPath();
      ctx.arc(positions[i].x, positions[i].y, r, 0, 2 * Math.PI);
      ctx.fillStyle = colour;
      ctx.shadowColor = colour;
      ctx.shadowBlur = 8;
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    // Selected agent: draw its links to everyone it can talk to, then ring it.
    if (selectedAgent != null) {
      const p = positions[selectedAgent];
      ctx.strokeStyle = "rgba(224,164,88,0.55)";
      ctx.lineWidth = 1.2;
      for (const j of sim.neighbours[selectedAgent]) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(positions[j].x, positions[j].y);
        ctx.stroke();
      }
      ctx.beginPath();
      ctx.arc(p.x, p.y, r + 5, 0, 2 * Math.PI);
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }

  function updateStats() {
    el("stepStat").textContent = sim.steps.toLocaleString();
    el("wordStat").textContent = sim.distinctWords();
    const sr = sim.successRate();
    const srEl = el("successStat");
    srEl.textContent = Math.round(sr * 100) + "%";
    srEl.className = "v " + (sr >= 0.9 ? "good" : sr < 0.5 ? "warn" : "");
    const d = sim.dialects();
    const dEl = el("dialectStat");
    dEl.textContent = d;
    dEl.className = "v " + (d === 1 ? "good" : "");
  }

  // Show the selected agent's actual word memory -- "the language in its head".
  function renderInspector() {
    const box = document.getElementById("inspector");
    if (selectedAgent == null) {
      box.className = "inspector-empty";
      box.innerHTML =
        "Click any dot in the simulation to inspect that agent. Its actual " +
        "word memory — the language inside its head — appears here." +
        "<br /><br />Tip: press <b>Pause</b> first for a steady look.";
      return;
    }
    box.className = "";
    const degree = sim.neighbours[selectedAgent].length;
    let html =
      `<div class="insp-head"><span class="id">Agent ${selectedAgent}</span>` +
      `<span class="deg">${degree} neighbour${degree === 1 ? "" : "s"}</span></div>`;

    for (let m = 0; m < sim.meanings; m++) {
      const words = sim.inv[selectedAgent][m];
      const preferred = sim.preferred(selectedAgent, m);
      html += `<div class="insp-meaning"><div class="m-label">Meaning ${m + 1}</div><div class="chips">`;
      if (words.length === 0) {
        html += `<span class="chip none">no word yet</span>`;
      } else {
        for (const w of words) {
          const isPref = w === preferred;
          html +=
            `<span class="chip${isPref ? " preferred" : ""}">` +
            `<span class="swatch" style="background:${wordColour(w)}"></span>${w}</span>`;
        }
      }
      html += `</div></div>`;
    }
    box.innerHTML = html;
  }

  // Turn one interaction into a readable line of HTML for the feed.
  function formatEvent(e) {
    const verb = e.success
      ? `<span class="ok">understood → both now agree</span>`
      : `<span class="miss">didn't know it → learned</span>`;
    return (
      `<div class="entry"><span class="ag">Agent ${e.s}</span> said ` +
      `"<span class="w">${e.word}</span>" to <span class="ag">Agent ${e.h}</span> ` +
      `(meaning ${e.m + 1}): ${verb}</div>`
    );
  }

  function renderLog() {
    const box = document.getElementById("log");
    if (logBuffer.length === 0) {
      box.innerHTML = `<span style="color:var(--muted)">Waiting for interactions…</span>`;
      return;
    }
    box.innerHTML = logBuffer.slice(-10).reverse().map(formatEvent).join("");
  }

  function loop() {
    if (running && sim) {
      const stepsPerFrame = +ui.speed.value;
      let pick = null; // an event to log this frame (prefer the selected agent)
      for (let i = 0; i < stepsPerFrame; i++) {
        sim.step();
        const e = sim.lastEvent;
        if (selectedAgent != null && (e.s === selectedAgent || e.h === selectedAgent)) {
          pick = e; // capture interactions involving the inspected agent
        }
      }
      // Sample one line per few frames so the feed reads at a human pace.
      framesSinceLog++;
      if (pick) { logBuffer.push(pick); framesSinceLog = 0; }
      else if (framesSinceLog >= 4) { logBuffer.push(sim.lastEvent); framesSinceLog = 0; }
      if (logBuffer.length > 40) logBuffer = logBuffer.slice(-40);

      draw();
      // Refresh the text readouts only a few times a second, so the numbers
      // are calm and readable instead of an unreadable high-speed blur.
      const now = performance.now();
      if (now - lastTextUpdate > 200) {
        updateStats();
        renderLog();
        if (selectedAgent != null) renderInspector(); // memory updates live
        lastTextUpdate = now;
      }
    }
    requestAnimationFrame(loop);
  }

  // ---- Events -------------------------------------------------------------

  function bindSlider(input, label, fmt) {
    const update = () => { el(label).textContent = fmt(input.value); };
    input.addEventListener("input", update);
    update();
  }
  bindSlider(ui.pop, "popVal", (v) => v);
  bindSlider(ui.meanings, "meanVal", (v) => v);
  bindSlider(ui.noise, "noiseVal", (v) => v + "%");
  bindSlider(ui.speed, "speedVal", (v) => v);

  // Structural changes rebuild the whole simulation.
  [ui.pop, ui.meanings, ui.noise, ui.network].forEach((c) =>
    c.addEventListener("change", rebuild));

  ui.viewMeaning.addEventListener("change", () => {
    viewMeaning = +ui.viewMeaning.value; draw();
  });
  ui.showEdges.addEventListener("change", draw);

  // Click a dot to inspect that agent. Canvas is drawn at a fixed internal
  // size but displayed scaled, so map the click back into canvas coordinates.
  canvas.addEventListener("click", (ev) => {
    const rect = canvas.getBoundingClientRect();
    const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
    const y = (ev.clientY - rect.top) * (canvas.height / rect.height);
    let best = null, bestDist = Infinity;
    for (let i = 0; i < sim.n; i++) {
      const dx = positions[i].x - x, dy = positions[i].y - y;
      const d = dx * dx + dy * dy;
      if (d < bestDist) { bestDist = d; best = i; }
    }
    // Only select if the click landed reasonably close to a dot.
    selectedAgent = bestDist <= 18 * 18 ? best : null;
    renderInspector();
    draw();
  });

  ui.play.addEventListener("click", () => {
    running = !running;
    ui.play.textContent = running ? "Pause" : "Play";
  });
  ui.reset.addEventListener("click", rebuild);

  // Swap in the user's logo if they dropped one next to this file.
  (function tryLogo() {
    const img = new Image();
    img.onload = () => {
      const slot = document.getElementById("logo");
      slot.classList.remove("logo-fallback");
      slot.textContent = "";
      const out = document.createElement("img");
      out.src = "logo.png";
      out.className = "logo";
      out.alt = "Lingo logo";
      slot.replaceWith(out);
    };
    img.src = "logo.png";
  })();

  // ---- Go -----------------------------------------------------------------
  rebuild();
  loop();
})();
