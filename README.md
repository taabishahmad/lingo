# Lingo — An Agent-Based Simulation of Emergent Shared Language Developed by Tabish Ahmad

A population of simple agents starts with **no common vocabulary**. Through
repeated pairwise interactions governed by one reinforcement rule, they
spontaneously converge on a shared language. Lingo implements the **Naming
Game** model and studies how the social network connecting agents (and how much
noise corrupts their messages) decides whether a single global language emerges
or the population splits into regional **dialects**.

This repository contains everything needed for the application half of the
project: the simulation engine, the experiments that produce the paper figures,
and an interactive real-time visualiser.

---

## What's inside

```
lingo_project/
├── lingo/                   # The simulation engine (Python package)
│   ├── agent.py             #   a single language learner + its word inventory
│   ├── networks.py          #   the three interaction topologies
│   ├── game.py              #   the Naming Game loop (the core engine)
│   └── metrics.py           #   distinct words, dialects, success rate
├── run_experiments.py       # Runs all 4 experiments → figures + data
├── web/                     # The interactive visualiser (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   ├── app.js               #   a faithful browser port of the engine
│   └── logo.png             #   ← PUT YOUR LOGO HERE (see "Adding your logo")
├── results/                 # Generated figures (PNG) — sample run included
├── data/                    # Generated raw data (CSV) — sample run included
└── requirements.txt
```

---

## Part 1 — Running the experiments (these produce your paper figures)

The experiment runner reproduces all four experiments from the proposal and
writes publication-quality figures to `results/` and the underlying numbers to
`data/`.

**1. Install Python 3.10 or newer** (check with `python --version`).

**2. Open the project folder in VS Code**, then open a terminal
(`Terminal → New Terminal`) and install the dependencies:

```bash
pip install -r requirements.txt
```

**3. Run the experiments:**

```bash
python run_experiments.py
```

You will see progress printed for each experiment, and afterwards `results/`
will contain four figures:

| File | Experiment |
|------|------------|
| `exp1_baseline_convergence.png` | A single language emerges (words spike, then collapse to consensus) |
| `exp2_convergence_vs_size.png`  | How convergence time grows with population size |
| `exp3_dialects_by_network.png`  | Dialects sustained by each network structure |
| `exp4_noise_effect.png`         | How communication noise erodes agreement |
| `exp5_network_noise_robustness.png` | **The contribution:** noise tolerance differs by network structure |
| `exp6_evolution_strategy.png` | **GA extension:** evolution selects against inventiveness, raising communicative success |

The matching `.csv` files in `data/` hold the raw numbers behind each figure, so
you can quote exact values or re-plot them in the report.

> Each experiment averages several independent runs and shows error bars, so the
> figures are honest and reproducible — exactly what a reviewer expects.

---

## Part 2 — Running the interactive visualiser

The visualiser shows every agent as a glowing dot whose **colour is the word it
currently prefers**. You watch colours merge into one (a global language) or
settle into regions (dialects), and you can change the population, network,
noise, and speed live.

It is plain HTML/CSS/JS and needs **no build step and no server**. Pick any one
of these:

**Option A — just open the file (simplest).**
Double-click `web/index.html`, or in VS Code right-click it and choose *Reveal in
File Explorer*, then open it in your browser.

**Option B — VS Code Live Server (nice for development).**
Install the *Live Server* extension, then right-click `web/index.html` →
*Open with Live Server*.

**Option C — serve it with Python.**
```bash
cd web
python -m http.server 8000
```
Then visit `http://localhost:8000` in your browser.

**Option D — serve it with XAMPP (optional).**
Copy the `web/` folder into XAMPP's `htdocs/` directory (e.g. rename it to
`lingo`), start **Apache** from the XAMPP control panel, and open
`http://localhost/lingo/`. *Note: Lingo is a self-contained simulation — it does
**not** use a database, so MySQL is not required. XAMPP is only one of several
ways to serve the page.*

### Things to try in the visualiser
- Start on **Fully connected** and watch every dot drift to a single colour — a
  global language.
- Switch to **Spatial grid** and tick *Show network connections* to watch
  coloured **dialect regions** form between neighbours.
- Push the **noise** slider up and watch agreement struggle to hold.

---

## Adding your logo

A placeholder appears in the top-left of the visualiser. To use your own logo:

1. Save your logo image as **`logo.png`**.
2. Place it inside the **`web/`** folder, right next to `index.html`.

That's it — the page detects the file and swaps it in automatically. A roughly
square image (for example 256×256 px) looks best. (If you prefer a different
filename or format, change the two `logo.png` references in `web/app.js` and the
`logo` element in `web/index.html`.)

---

## How the code maps to the proposal

| Proposal concept | Where it lives |
|------------------|----------------|
| Intelligent agents with word inventories | `lingo/agent.py` |
| Naming Game / reinforcement rule | `lingo/game.py` (`NamingGame.step`) |
| Interaction networks (fully connected, grid, small-world) | `lingo/networks.py` |
| Communication noise | `noise` parameter in `lingo/game.py` |
| Metrics (distinct words, success rate, dialects, convergence time) | `lingo/metrics.py` + history in `game.py` |
| All four planned experiments | `run_experiments.py` |
| Real-time visualisation with parameter sliders | `web/` |

The browser engine in `web/app.js` deliberately mirrors the Python rules in
`lingo/game.py`, so the live demo and the paper figures tell the same story.

---

## A note on reproducibility

The Python experiments use fixed random seeds, so re-running
`run_experiments.py` gives you the same figures every time. Change the seeds (or
the parameters near the top of each experiment function) to explore further.
