"""
Regenerates every figure in figures/ from phi_model.py.

    python model/make_figures.py

Writes PNG files and figures/results.json (the numbers quoted in the paper).
Runs in about a minute on a laptop.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import kendalltau

sys.path.insert(0, os.path.dirname(__file__))
from phi_model import (Params, reaction, fixed_points, fold_gain, held_region, disc,
                       outcome, simulate, simulate_mean_field, early_warning)

OUT = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(OUT, exist_ok=True)

INK = "#18202E"
MUTED = "#5A6476"
LINE = "#D3D9E2"
ACCENT = "#4A3FCF"
SIGNAL = "#B9690F"
CRIT = "#B93A27"
SOFT = "#E5E8F6"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9.5,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.titlesize": 10.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "legend.frameon": False,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

RESULTS: dict = {}
P0 = Params()
K, G = P0.kappa, P0.gamma


def save(fig, name):
    fig.savefig(os.path.join(OUT, name))
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------------------
# Figure 1: the reaction terms in three regimes
# ---------------------------------------------------------------------------

def fig_reaction():
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 2.8), sharey=True)
    phi = np.linspace(0, 2.4, 400)
    cases = [(-1.2, "a · Noise too high: no seed"),
             (-0.8, "b · Controllable window"),
             (0.2, "c · Rest unstable")]
    for ax, (r, title) in zip(axes, cases):
        f = reaction(phi, r, K, G)
        ax.axhline(0, color=LINE, lw=1)
        ax.fill_between(phi, f, 0, where=f > 0, color=SIGNAL, alpha=0.12, lw=0)
        ax.fill_between(phi, f, 0, where=f < 0, color=ACCENT, alpha=0.08, lw=0)
        ax.plot(phi, f, color=ACCENT, lw=2)
        fp = fixed_points(r, K, G)
        for key, face, label in [("rest", INK, "rest"), ("threshold", "white", "threshold"),
                                 ("seed", SIGNAL, "seed")]:
            x = fp[key]
            if x is None:
                continue
            if key == "threshold" and x < 1e-6:
                label = "rest, unstable"
            ax.plot([x], [0], "o", ms=7, mfc=face, mec=INK, mew=1.3, zorder=5)
            ax.annotate(label, (x, 0), xytext=(0, 9), textcoords="offset points",
                        ha="center", fontsize=8.5, color=INK)
        ax.set_title(title, fontsize=9.5)
        if r == -0.8:
            ax.annotate("", xy=(0.12, -0.35), xytext=(0.48, -0.35),
                        arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.2))
            ax.annotate("", xy=(1.38, -0.35), xytext=(0.62, -0.35),
                        arrowprops=dict(arrowstyle="-|>", color=SIGNAL, lw=1.2))
            ax.text(0.22, -0.6, "drains", ha="center", fontsize=8, color=ACCENT)
            ax.text(1.05, -0.6, "grows to seed", ha="center", fontsize=8, color=SIGNAL)
        ax.set_xlabel("Φ (state intensity)")
        ax.text(0.98, 0.04, f"r = αI − β = {r:+.1f}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=8.5, color=MUTED)
        ax.set_ylim(-1.6, 1.6)
    axes[0].set_ylabel("dΦ/dt from the reaction terms\n(above 0 grows, below 0 drains)")
    fig.suptitle("Figure 1 · The reaction terms decide whether a seed state can exist",
                 x=0.01, ha="left", fontsize=11, fontweight="bold", y=1.04)
    save(fig, "fig1_reaction_terms.png")


# ---------------------------------------------------------------------------
# Figure 2: the control map (hysteresis) and the ceiling
# ---------------------------------------------------------------------------

def fig_control():
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.2, 3.4), gridspec_kw={"width_ratios": [1.35, 1]})
    rf = fold_gain(K, G)
    r = np.linspace(-1.6, 0.6, 600)
    seed = np.full_like(r, np.nan)
    thr = np.full_like(r, np.nan)
    for i, ri in enumerate(r):
        disc_ = K**2 + 4 * G * ri
        if disc_ >= 0:
            seed[i] = (K + np.sqrt(disc_)) / (2 * G)
            m = (K - np.sqrt(disc_)) / (2 * G)
            if m > 0:
                thr[i] = m
    a.axvspan(rf, 0, color=SOFT, lw=0)
    a.text(-0.48, 2.55, "controllable window\n(rest and seed coexist)", ha="center",
           va="top", fontsize=8.5, color=ACCENT)
    a.plot(r[r < 0], np.zeros((r < 0).sum()), color=INK, lw=2, label="rest (stable)")
    a.plot(r[r >= 0], np.zeros((r >= 0).sum()), color=INK, lw=1.3, ls="--")
    a.plot(r, thr, color=INK, lw=1.3, ls="--", label="threshold (unstable)")
    a.plot(r, seed, color=SIGNAL, lw=2.4, label="seed (stable)")
    # hysteresis arrows
    a.annotate("", xy=(0.02, 1.95), xytext=(0.02, 0.08),
               arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.6))
    a.text(0.06, 0.9, "entry without\na spark (r > 0)", fontsize=8, color=ACCENT)
    a.annotate("", xy=(rf - 0.02, 0.06), xytext=(rf - 0.02, 0.97),
               arrowprops=dict(arrowstyle="-|>", color=CRIT, lw=1.6))
    a.text(rf - 0.06, 0.45, "off switch:\nexit below\nr = −κ²/4γ", fontsize=8, color=CRIT, ha="right")
    a.annotate("", xy=(-0.55, 1.62), xytext=(-0.55, 0.42),
               arrowprops=dict(arrowstyle="-|>", color=SIGNAL, lw=1.4, ls="-"))
    a.text(-0.51, 0.95, "spark above\nthreshold", fontsize=8, color=SIGNAL)
    a.set_xlim(-1.6, 0.6)
    a.set_ylim(-0.1, 2.6)
    a.set_xlabel("net gain inside the held region, r = αI − β")
    a.set_ylabel("Φ at equilibrium")
    a.legend(loc="upper left", fontsize=8)
    a.set_title("a · Entry, hold and exit are separate controls")

    rr = np.linspace(-1.2, 1.0, 400)
    for g, col, lab in [(1.0, SIGNAL, "γ = 1"), (0.6, ACCENT, "γ = 0.6"), (0.35, MUTED, "γ = 0.35")]:
        d = K**2 + 4 * g * rr
        y = np.where(d >= 0, (K + np.sqrt(np.clip(d, 0, None))) / (2 * g), np.nan)
        b.plot(rr, y, color=col, lw=2, label=f"seed level, {lab}")
    b.annotate("", xy=(0.55, 7.8), xytext=(0.55, 6.6),
               arrowprops=dict(arrowstyle="-|>", color=CRIT, lw=1.6))
    b.text(0.48, 7.2, "γ = 0, the equation as first\nwritten: no plateau at all,\nΦ grows without limit",
           fontsize=8, color=CRIT, ha="right", va="center")
    b.set_ylim(0, 8)
    b.set_xlabel("net gain r")
    b.set_ylabel("plateau Φ")
    b.legend(loc="lower right", fontsize=8)
    b.set_title("b · γ is the ceiling that makes the plateau safe")
    fig.suptitle("Figure 2 · The control map: a threshold to enter, a ceiling to hold, a fold to exit",
                 x=0.01, ha="left", fontsize=11, fontweight="bold", y=1.04)
    save(fig, "fig2_control_map.png")
    RESULTS["fold_gain"] = rf
    RESULTS["default_fixed_points"] = fixed_points(P0.r, K, G)


# ---------------------------------------------------------------------------
# Figure 3: size, shape and spark on the body map
# ---------------------------------------------------------------------------

def fig_space():
    n = 120
    p = P0
    seed_level = fixed_points(p.r, K, G)["seed"]

    radii = list(range(4, 21, 1))
    rad_out = []
    for rad in radii:
        m = held_region(n, rad, "round")
        v, held = outcome(p, m, np.where(m, 1.6, 0.0), T=150)
        rad_out.append((rad, v, held))

    shapes = ["round", "stretched", "scattered"]
    shape_out = {}
    masks = {}
    for sh in shapes:
        m = held_region(n, 14, sh)
        masks[sh] = m
        v, held = outcome(p, m, np.where(m, 1.6, 0.0), T=150)
        shape_out[sh] = (int(m.sum()), v, held)

    sparks = list(range(1, 11))
    m14 = held_region(n, 14, "round")
    spark_out = []
    for sp in sparks:
        v, held = outcome(p, m14, np.where(disc(n, sp) & m14, 1.6, 0.0), T=220)
        spark_out.append((sp, v, held))

    fig = plt.figure(figsize=(9.2, 3.3))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.1, 1.1], wspace=0.5)
    a = fig.add_subplot(gs[0])
    xs = [x for x, _, _ in rad_out]
    ys = [v for _, v, _ in rad_out]
    cols = [SIGNAL if h else MUTED for _, _, h in rad_out]
    a.plot(xs, ys, color=LINE, lw=1, zorder=1)
    a.scatter(xs, ys, c=cols, s=28, zorder=2)
    crit_r = next((x for x, _, h in rad_out if h), None)
    if crit_r:
        a.axvline(crit_r - 0.5, color=INK, lw=1, ls=":")
        a.text(crit_r - 0.2, seed_level * 0.15, f"minimum\nradius ≈ {crit_r}", fontsize=8)
    a.axhline(seed_level, color=SIGNAL, lw=1, ls="--")
    a.text(20, seed_level + 0.04, "seed level", fontsize=8, ha="right", color=SIGNAL)
    a.set_xlabel("radius of a round held region")
    a.set_ylabel("mean Φ inside after release")
    a.set_title("a · Too narrow leaks")

    b = fig.add_subplot(gs[1])
    vals = [shape_out[s][1] for s in shapes]
    bars = b.bar(range(3), vals, color=[SIGNAL if shape_out[s][2] else MUTED for s in shapes], width=0.6)
    b.set_xticks(range(3), ["round", "stretched", "5 patches"])
    b.set_ylabel("mean Φ inside after release")
    b.set_title("b · Same area, different shape")
    for i, s in enumerate(shapes):
        ins = b.inset_axes([i / 3 + 0.04, 0.72, 0.24, 0.24])
        ins.imshow(masks[s], cmap="Greys", interpolation="nearest")
        ins.set_xticks([]); ins.set_yticks([])
        for sp in ins.spines.values():
            sp.set_color(LINE)
    b.set_ylim(0, max(vals) * 1.6 + 0.1)
    for i, s_ in enumerate(shapes):
        if not shape_out[s_][2]:
            b.text(i, 0.05, "drained\nto rest", ha="center", va="bottom", fontsize=8, color=MUTED)

    c = fig.add_subplot(gs[2])
    xs = [x for x, _, _ in spark_out]
    ys = [v for _, v, _ in spark_out]
    c.plot(xs, ys, color=LINE, lw=1, zorder=1)
    c.scatter(xs, ys, c=[SIGNAL if h else MUTED for _, _, h in spark_out], s=28, zorder=2)
    crit_s = next((x for x, _, h in spark_out if h), None)
    if crit_s:
        c.axvline(crit_s - 0.5, color=INK, lw=1, ls=":")
        c.text(crit_s - 0.2, seed_level * 0.15, f"minimum\nspark ≈ {crit_s}", fontsize=8)
    c.set_xlabel("radius of the initial spark")
    c.set_ylabel("mean Φ inside at the end")
    c.set_title("c · A spark must be big enough")
    fig.suptitle("Figure 3 · On the body map, size, roundness and spark size decide whether the seed holds\n"
                 "orange = seed held, grey = drained back to rest  (r = −0.8, κ = 2, γ = 1, D = 1, outside gain −1.5)",
                 x=0.01, ha="left", fontsize=10.5, fontweight="bold", y=1.1)
    save(fig, "fig3_size_shape_spark.png")
    RESULTS["minimum_radius"] = crit_r
    RESULTS["shapes_equal_area"] = {s: {"cells": shape_out[s][0], "mean_phi": round(shape_out[s][1], 3),
                                        "held": shape_out[s][2]} for s in shapes}
    RESULTS["minimum_spark_radius"] = crit_s


# ---------------------------------------------------------------------------
# Figure 4: one controllable session in the model
# ---------------------------------------------------------------------------

def session_schedule(t):
    # minutes on a session clock, mapped to the protocol steps
    if t < 25:      # gate, settle and count: noise falls
        return -1.35 + (0.65 * t / 25)
    if t < 45:      # spark, feed the loop, spread, hold
        return -0.70
    if t < 46.5:    # half-effort check: drive drops a little
        return -0.85
    if t < 52:
        return -0.70
    if t < 55:      # release test: no driving at all
        return -0.92
    return -1.60    # off switch: eyes open, move, talk


def fig_session():
    T = 62
    t, seed_run = simulate_mean_field(session_schedule, K, G, eta=0.01, T=T, dt=0.01,
                                      kick=[(27.0, 0.75)], rng=3)
    _, no_spark = simulate_mean_field(session_schedule, K, G, eta=0.01, T=T, dt=0.01, rng=3)
    _, small_spark = simulate_mean_field(session_schedule, K, G, eta=0.01, T=T, dt=0.01,
                                         kick=[(27.0, 0.3)], rng=3)
    r = np.array([session_schedule(x) for x in t])

    fig, (a, b) = plt.subplots(2, 1, figsize=(9.2, 4.6), sharex=True,
                               gridspec_kw={"height_ratios": [2.2, 1]})
    spans = [(0, 25, "1–2 · gate,\nsettle, count"), (25, 45, "3–6 · spark, feed,\nspread, hold"),
             (45, 46.5, ""), (46.5, 52, ""), (52, 55, "7 · release\ntest"), (55, T, "8 · off\nswitch")]
    for i, (x0, x1, lab) in enumerate(spans):
        if i % 2 == 0:
            a.axvspan(x0, x1, color=SOFT, lw=0, alpha=0.7)
            b.axvspan(x0, x1, color=SOFT, lw=0, alpha=0.7)
        if lab:
            a.text((x0 + x1) / 2, 2.05, lab, ha="center", va="top", fontsize=8, color=MUTED)
    a.text(45.75, 1.15, "half-effort\ncheck", ha="center", fontsize=7.5, color=MUTED)
    a.plot(t, no_spark, color=MUTED, lw=1.4, label="same session, no spark: stays at rest")
    a.plot(t, small_spark, color=ACCENT, lw=1.4, label="spark below threshold: fades")
    a.plot(t, seed_run, color=SIGNAL, lw=2.2, label="spark above threshold: seed, plateau, stored, switched off")
    a.set_ylabel("Φ")
    a.set_ylim(-0.1, 2.1)
    a.legend(loc="center left", fontsize=8, bbox_to_anchor=(0.0, 0.55))
    a.set_title("a · The state")
    b.plot(t, r, color=INK, lw=1.6)
    b.axhline(fold_gain(K, G), color=CRIT, lw=1, ls="--")
    b.text(0.5, fold_gain(K, G) + 0.04, "fold: below this no seed can exist", color=CRIT, fontsize=8)
    b.axhline(0, color=LINE, lw=1)
    b.set_ylabel("net gain r")
    b.set_xlabel("session time (minutes, illustrative)")
    b.set_title("b · What the practitioner controls")
    fig.suptitle("Figure 4 · A full session in the model: entry by spark, plateau at the ceiling, storage, deliberate exit",
                 x=0.01, ha="left", fontsize=11, fontweight="bold", y=1.02)
    save(fig, "fig4_session.png")
    i_rel_end = np.searchsorted(t, 54.9)
    i_plateau = np.searchsorted(t, 44.0)
    RESULTS["session"] = {
        "plateau_phi": round(float(seed_run[i_plateau]), 3),
        "phi_end_of_release": round(float(seed_run[i_rel_end]), 3),
        "phi_after_off_switch": round(float(seed_run[-1]), 3),
        "release_retention": round(float(seed_run[i_rel_end] / seed_run[i_plateau]), 3),
    }


# ---------------------------------------------------------------------------
# Figure 5: early-warning signals, gain-driven onset vs spark-driven onset
# ---------------------------------------------------------------------------

RAMP, PRE, WINDOW, ETA_EWS, SAMPLE_DT = 900.0, 250.0, 120, 0.01, 0.5


def gain_schedule(tt):
    """Net gain rises slowly from -0.6 through 0 over RAMP time units."""
    return -0.6 + 0.7 * min(tt, RAMP) / RAMP


def ews_runs(kind, n_runs=30, rng0=100):
    dt = 0.02
    T = RAMP + 40.0
    aligned_var, aligned_ac, taus_var, taus_ac, onset_gain = [], [], [], [], []
    grid = np.arange(-PRE, -1.0, SAMPLE_DT)
    for k in range(n_runs):
        rng = np.random.default_rng(rng0 + k)
        if kind == "gain":
            t, phi = simulate_mean_field(gain_schedule, K, G, eta=ETA_EWS, T=T, dt=dt, rng=rng)
        else:
            tk = RAMP * (0.6 + 0.3 * rng.random())
            t, phi = simulate_mean_field(lambda tt: -0.6, K, G, eta=ETA_EWS, T=T, dt=dt,
                                         kick=[(tk, 0.9)], rng=rng)
        step = int(round(SAMPLE_DT / dt))
        ts, xs = t[::step], phi[::step]
        on_idx = np.argmax(xs > 0.5)
        if xs[on_idx] <= 0.5:
            continue
        t_on = ts[on_idx]
        if t_on < PRE + WINDOW * SAMPLE_DT:
            continue
        var, ac = early_warning(xs, WINDOW)
        sel = (ts >= t_on - PRE) & (ts < t_on - 1.0)
        rel = ts[sel] - t_on
        v, a = var[sel], ac[sel]
        ok = ~np.isnan(v) & ~np.isnan(a)
        if ok.sum() < 10:
            continue
        taus_var.append(kendalltau(rel[ok], v[ok])[0])
        taus_ac.append(kendalltau(rel[ok], a[ok])[0])
        aligned_var.append(np.interp(grid, rel, v))
        aligned_ac.append(np.interp(grid, rel, a))
        if kind == "gain":
            onset_gain.append(gain_schedule(t_on))
    return (grid, np.array(aligned_var), np.array(aligned_ac), np.array(taus_var),
            np.array(taus_ac), np.array(onset_gain))


def fig_early_warning():
    g1, v1, a1, tv1, ta1, og = ews_runs("gain")
    g2, v2, a2, tv2, ta2, _ = ews_runs("spark")
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.1))
    # example traces
    rng = np.random.default_rng(7)
    t, phi = simulate_mean_field(gain_schedule, K, G, eta=ETA_EWS, T=RAMP + 40, dt=0.02, rng=rng)
    t2, phi2 = simulate_mean_field(lambda tt: -0.6, K, G, eta=ETA_EWS, T=RAMP + 40, dt=0.02,
                                   kick=[(700.0, 0.9)], rng=np.random.default_rng(8))
    ax = axes[0]
    ax.plot(t, phi, color=ACCENT, lw=1, label="gain rises slowly")
    ax.plot(t2, phi2, color=SIGNAL, lw=1, label="spark at fixed gain")
    ax.set_xlabel("time")
    ax.set_ylabel("Φ")
    ax.set_title("a · Two ways to reach onset")
    ax.legend(fontsize=8, loc="upper left")
    for ax, data, lab in [(axes[1], (v1, v2), "variance"), (axes[2], (a1, a2), "lag-1 autocorrelation")]:
        for arr, col, name in [(data[0], ACCENT, "gain-driven"), (data[1], SIGNAL, "spark-driven")]:
            if len(arr) == 0:
                continue
            m = np.nanmean(arr, axis=0)
            lo, hi = np.nanpercentile(arr, [25, 75], axis=0)
            gg = g1 if col == ACCENT else g2
            ax.fill_between(gg, lo, hi, color=col, alpha=0.15, lw=0)
            ax.plot(gg, m, color=col, lw=1.8, label=name)
        ax.set_xlabel("time before onset")
        ax.set_title(f"{'b' if lab == 'variance' else 'c'} · Rolling {lab}")
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle("Figure 5 · Early warning: fluctuations slow down and grow before a gain-driven onset, not before a spark-driven one\n"
                 f"30 simulated runs each, η = {ETA_EWS}, sampled every {SAMPLE_DT}, {int(WINDOW * SAMPLE_DT)}-unit windows; mean with interquartile band. Compare trends, not levels.",
                 x=0.01, ha="left", fontsize=10.5, fontweight="bold", y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, "fig5_early_warning.png")
    RESULTS["early_warning"] = {
        "gain_driven": {"runs": int(len(tv1)), "median_onset_gain": round(float(np.median(og)), 3), "median_tau_variance": round(float(np.median(tv1)), 3),
                        "median_tau_ac1": round(float(np.median(ta1)), 3),
                        "share_tau_variance_positive": round(float(np.mean(tv1 > 0)), 3),
                        "share_tau_ac1_positive": round(float(np.mean(ta1 > 0)), 3)},
        "spark_driven": {"runs": int(len(tv2)), "median_tau_variance": round(float(np.median(tv2)), 3),
                         "median_tau_ac1": round(float(np.median(ta2)), 3),
                         "share_tau_variance_positive": round(float(np.mean(tv2 > 0)), 3),
                         "share_tau_ac1_positive": round(float(np.mean(ta2 > 0)), 3)},
    }


if __name__ == "__main__":
    fig_reaction()
    fig_control()
    fig_space()
    fig_session()
    fig_early_warning()
    with open(os.path.join(OUT, "results.json"), "w") as fh:
        json.dump(RESULTS, fh, indent=2, default=lambda o: None if o is None else float(o))
    print(json.dumps(RESULTS, indent=2, default=lambda o: None if o is None else float(o)))
