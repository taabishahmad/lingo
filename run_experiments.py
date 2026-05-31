"""Run every experiment in the proposal and export paper-ready figures + data.

    python run_experiments.py

Produces, in results/ and data/:
    1. exp1_baseline_convergence   -- distinct words and success rate over time
    2. exp2_convergence_vs_size    -- convergence time against population size
    3. exp3_dialects_by_network    -- surviving dialects per network structure
    4. exp4_noise_effect           -- final agreement against noise level
"""

from __future__ import annotations

import csv
import os
import statistics

import matplotlib

matplotlib.use("Agg")  # render to files, no display needed
import matplotlib.pyplot as plt

from lingo import NamingGame
from lingo.evolution import EvolutionaryNamingGame
from lingo.networks import NETWORK_TYPES

RESULTS_DIR = "results"
DATA_DIR = "data"

# A consistent, clean look across every figure.
plt.rcParams.update(
    {
        "figure.dpi": 130,
        "savefig.dpi": 160,
        "font.size": 11,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)
PALETTE = {"fully_connected": "#2a6f97", "grid": "#e07a5f", "small_world": "#81b29a"}
LABELS = {
    "fully_connected": "Fully connected",
    "grid": "Spatial grid",
    "small_world": "Small-world",
}


def _save(fig, name: str) -> None:
    path = os.path.join(RESULTS_DIR, f"{name}.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  saved {path}")


def _write_csv(name: str, header: list[str], rows: list[list]) -> None:
    path = os.path.join(DATA_DIR, f"{name}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"  saved {path}")


# --- Experiment 1: baseline convergence -------------------------------------

def experiment_baseline():
    print("Experiment 1: baseline convergence (fully connected)")
    game = NamingGame(50, num_meanings=3, network_type="fully_connected", seed=42)
    game.run(max_steps=200_000)
    h = game.history

    fig, ax1 = plt.subplots(figsize=(7, 4.2))
    ax1.plot(h["step"], h["distinct_words"], color="#2a6f97", lw=2,
             label="Distinct words")
    ax1.set_xlabel("Interactions")
    ax1.set_ylabel("Number of distinct words", color="#2a6f97")
    ax1.tick_params(axis="y", labelcolor="#2a6f97")

    ax2 = ax1.twinx()
    ax2.plot(h["step"], h["success_rate"], color="#e07a5f", lw=2, ls="--",
             label="Success rate")
    ax2.set_ylabel("Communication success rate", color="#e07a5f")
    ax2.tick_params(axis="y", labelcolor="#e07a5f")
    ax2.set_ylim(0, 1.05)
    ax2.grid(False)

    plt.title("Baseline: a single language emerges (N = 50)")
    _save(fig, "exp1_baseline_convergence")
    _write_csv(
        "exp1_baseline_convergence",
        ["step", "distinct_words", "success_rate", "dialects"],
        list(zip(h["step"], h["distinct_words"], h["success_rate"], h["dialects"])),
    )


# --- Experiment 2: convergence time vs population size -----------------------

def experiment_convergence_vs_size(trials: int = 5):
    print("Experiment 2: convergence time vs population size")
    sizes = [10, 25, 50, 100, 150, 200]
    means, errors, rows = [], [], []
    for n in sizes:
        times = []
        for t in range(trials):
            game = NamingGame(n, num_meanings=1, network_type="fully_connected",
                              seed=100 + t)
            game.run(max_steps=500_000)
            conv = game.convergence_step() or game.step_count
            times.append(conv)
        means.append(statistics.mean(times))
        errors.append(statistics.pstdev(times))
        rows.append([n, round(statistics.mean(times), 1), round(statistics.pstdev(times), 1)])
        print(f"  N={n:4d} -> mean convergence {means[-1]:.0f} interactions")

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.errorbar(sizes, means, yerr=errors, marker="o", color="#2a6f97",
                capsize=4, lw=2)
    ax.set_xlabel("Population size (N)")
    ax.set_ylabel("Interactions to converge")
    ax.set_title(f"Convergence time grows with population (mean of {trials} runs)")
    _save(fig, "exp2_convergence_vs_size")
    _write_csv("exp2_convergence_vs_size",
               ["population_size", "mean_convergence_steps", "std_dev"], rows)


# --- Experiment 3: dialect formation across network types -------------------

def experiment_dialects(trials: int = 5):
    print("Experiment 3: dialect formation across network structures")
    # Measure at a fixed interaction budget so spatial structure is visible
    # before the slow networks have time to fully mix into one language.
    # Fully connected has long since reached a single language at this budget;
    # the restricted networks are still fragmented into regional dialects.
    n = 100
    budget = 20_000
    results, rows = {}, []
    for net in NETWORK_TYPES:
        counts = []
        for t in range(trials):
            game = NamingGame(n, num_meanings=3, network_type=net, seed=200 + t)
            game.run(max_steps=budget, stop_on_convergence=False)
            counts.append(game.history["dialects"][-1])
        results[net] = (statistics.mean(counts), statistics.pstdev(counts))
        rows.append([net, round(statistics.mean(counts), 2), round(statistics.pstdev(counts), 2)])
        print(f"  {net:16s} -> mean {results[net][0]:.2f} surviving dialects")

    fig, ax = plt.subplots(figsize=(7, 4.2))
    names = list(NETWORK_TYPES)
    ax.bar([LABELS[x] for x in names],
           [results[x][0] for x in names],
           yerr=[results[x][1] for x in names],
           color=[PALETTE[x] for x in names], capsize=5, width=0.6)
    ax.set_ylabel("Surviving dialects")
    ax.set_title(f"Restricted networks sustain dialects (N = {n}, {budget:,} interactions)")
    _save(fig, "exp3_dialects_by_network")
    _write_csv("exp3_dialects_by_network",
               ["network_type", "mean_dialects", "std_dev"], rows)


# --- Experiment 4: effect of noise ------------------------------------------

def experiment_noise(trials: int = 5):
    print("Experiment 4: effect of communication noise")
    noise_levels = [0.0, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3]
    means, errors, rows = [], [], []
    for noise in noise_levels:
        finals = []
        for t in range(trials):
            game = NamingGame(50, num_meanings=1, network_type="fully_connected",
                              noise=noise, seed=300 + t)
            game.run(max_steps=120_000, stop_on_convergence=False)
            finals.append(game.history["success_rate"][-1])
        means.append(statistics.mean(finals))
        errors.append(statistics.pstdev(finals))
        rows.append([noise, round(statistics.mean(finals), 3), round(statistics.pstdev(finals), 3)])
        print(f"  noise={noise:.2f} -> final agreement {means[-1]:.2f}")

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.errorbar(noise_levels, means, yerr=errors, marker="s", color="#e07a5f",
                capsize=4, lw=2)
    ax.set_xlabel("Communication noise level")
    ax.set_ylabel("Final agreement (success rate)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Self-organisation tolerates noise up to a breaking point")
    _save(fig, "exp4_noise_effect")
    _write_csv("exp4_noise_effect",
               ["noise_level", "mean_final_agreement", "std_dev"], rows)


# --- Experiment 5: network structure x noise (the focused contribution) -----

def experiment_robustness(trials: int = 8):
    print("Experiment 5: noise robustness by network structure")
    # Each network is run to (near) convergence at a fair fixed budget, so
    # differences in final agreement reflect noise tolerance, not speed.
    budget = 80_000
    noise_levels = [0.0, 0.03, 0.06, 0.09, 0.12, 0.15, 0.2, 0.25, 0.3, 0.35]
    curves = {net: {"mean": [], "err": []} for net in NETWORK_TYPES}
    rows = []

    for net in NETWORK_TYPES:
        for noise in noise_levels:
            finals = []
            for t in range(trials):
                game = NamingGame(100, num_meanings=1, network_type=net,
                                  noise=noise, seed=400 + t)
                game.run(max_steps=budget, stop_on_convergence=False)
                finals.append(game.history["success_rate"][-1])
            m = statistics.mean(finals)
            e = statistics.pstdev(finals)
            curves[net]["mean"].append(m)
            curves[net]["err"].append(e)
            rows.append([net, noise, round(m, 3), round(e, 3)])
        print(f"  {net:16s} swept {len(noise_levels)} noise levels")

    # The headline result: do different structures break down at different
    # noise levels? Report the critical noise where agreement falls below 0.5.
    def critical_noise(net):
        for noise, m in zip(noise_levels, curves[net]["mean"]):
            if m < 0.5:
                return noise
        return None

    print("  Critical noise (agreement < 0.5):")
    for net in NETWORK_TYPES:
        cn = critical_noise(net)
        print(f"    {net:16s} -> {cn if cn is not None else '>0.35'}")

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for net in NETWORK_TYPES:
        ax.errorbar(noise_levels, curves[net]["mean"], yerr=curves[net]["err"],
                    marker="o", capsize=3, lw=2, color=PALETTE[net],
                    label=LABELS[net])
    ax.axhline(0.5, color="#888", ls=":", lw=1)
    ax.text(0.005, 0.44, "breakdown line", color="#888", fontsize=9, ha="left")
    ax.set_xlabel("Communication noise level")
    ax.set_ylabel("Final agreement (success rate)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Noise tolerance depends on network structure (N = 100)")
    ax.legend(frameon=False)
    _save(fig, "exp5_network_noise_robustness")
    _write_csv("exp5_network_noise_robustness",
               ["network_type", "noise_level", "mean_final_agreement", "std_dev"], rows)


# --- Experiment 6: evolution of communication strategy (GA extension) -------

def experiment_evolution(trials: int = 6, generations: int = 50):
    print("Experiment 6: evolution of communication strategy")
    inv_runs, fit_runs = [], []
    for t in range(trials):
        ga = EvolutionaryNamingGame(num_agents=80, interactions_per_generation=5000,
                                    seed=500 + t)
        h = ga.evolve(generations=generations)
        inv_runs.append(h["inventiveness"])
        fit_runs.append(h["fitness"])
    gens = list(range(generations))
    inv_mean = [statistics.mean(r[g] for r in inv_runs) for g in gens]
    inv_err = [statistics.pstdev(r[g] for r in inv_runs) for g in gens]
    fit_mean = [statistics.mean(r[g] for r in fit_runs) for g in gens]
    print(f"  inventiveness: gen 0 = {inv_mean[0]:.2f} -> gen {generations-1} = {inv_mean[-1]:.2f}")
    print(f"  fitness:       gen 0 = {fit_mean[0]:.2f} -> gen {generations-1} = {fit_mean[-1]:.2f}")

    fig, ax1 = plt.subplots(figsize=(7.2, 4.4))
    ax1.plot(gens, inv_mean, color="#e07a5f", lw=2, label="Inventiveness (evolved trait)")
    ax1.fill_between(gens,
                     [m - e for m, e in zip(inv_mean, inv_err)],
                     [m + e for m, e in zip(inv_mean, inv_err)],
                     color="#e07a5f", alpha=0.15)
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Mean inventiveness", color="#e07a5f")
    ax1.tick_params(axis="y", labelcolor="#e07a5f")
    ax1.set_ylim(0, 1.0)

    ax2 = ax1.twinx()
    ax2.plot(gens, fit_mean, color="#2a6f97", lw=2, ls="--", label="Communicative success")
    ax2.set_ylabel("Mean communicative success", color="#2a6f97")
    ax2.tick_params(axis="y", labelcolor="#2a6f97")
    ax2.set_ylim(0, 1.05)
    ax2.grid(False)

    plt.title("Evolution selects against inventiveness (mean of %d runs)" % trials)
    _save(fig, "exp6_evolution_strategy")
    _write_csv("exp6_evolution_strategy",
               ["generation", "mean_inventiveness", "inventiveness_std", "mean_success"],
               list(zip(gens, [round(x, 4) for x in inv_mean],
                        [round(x, 4) for x in inv_err],
                        [round(x, 4) for x in fit_mean])))


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Running Lingo experiments. Figures -> results/, data -> data/\n")
    experiment_baseline()
    experiment_convergence_vs_size()
    experiment_dialects()
    experiment_noise()
    experiment_robustness()
    experiment_evolution()
    print("\nAll experiments complete.")


if __name__ == "__main__":
    main()
