"""Build every figure and number in the paper from results/*.json.

    cd kyle_collusion && python paper/make_results.py

Writes paper/figures/*.pdf and paper/numbers.tex (LaTeX macros). Missing
experiments are skipped, so the script runs at any stage of the project.
"""

from __future__ import annotations

import glob
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "paper", "figures")
os.makedirs(FIG, exist_ok=True)

# Colour-blind-safe palette (Okabe-Ito), fixed per condition across figures.
C = {
    "strategic": "#0072B2",
    "myopic": "#E69F00",
    "none": "#009E73",
    "orders": "#CC79A7",
    "flow": "#56B4E9",
    "grey": "#7F7F7F",
}
plt.rcParams.update({
    "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 9, "legend.frameon": False, "figure.dpi": 150,
})

macros: dict[str, str] = {}


def load(pattern: str) -> list[dict]:
    out = []
    for f in sorted(glob.glob(os.path.join(RES, pattern))):
        r = json.load(open(f))
        r["_file"] = os.path.relpath(f, RES)
        out.append(r)
    return out


def pooled(runs: list[dict], key: str) -> tuple[float, float, int]:
    """Mean and 95% CI across all sessions of all runs (sessions are i.i.d.)."""
    vals = np.concatenate([np.asarray(r["per_session"][key], float) for r in runs])
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return float("nan"), float("nan"), 0
    return float(vals.mean()), float(1.96 * vals.std(ddof=1) / math.sqrt(len(vals))), len(vals)


def seed_spread(runs: list[dict], key: str) -> tuple[float, float]:
    """Mean and 95% CI across seeds (each seed's session mean is one draw)."""
    m = np.array([np.nanmean(r["per_session"][key]) for r in runs])
    if len(m) < 2:
        return float(m.mean()) if len(m) else float("nan"), float("nan")
    return float(m.mean()), float(2.0 * m.std(ddof=1) / math.sqrt(len(m)))


def impulse_pooled(runs: list[dict], key: str = "d_beta_rival"):
    """Event-weighted average impulse profile across runs."""
    runs = [r for r in runs if r.get("impulse") and r["impulse"]["n_events"]]
    if not runs:
        return None
    w = np.array([r["impulse"]["n_events"] for r in runs], float)
    m = np.array([r["impulse"][key] for r in runs])
    ci = np.array([r["impulse"][key + "_ci95"] for r in runs])
    mean = (w[:, None] * m).sum(0) / w.sum()
    # combine per-run CIs as independent estimates
    se = np.sqrt(((w[:, None] / w.sum()) ** 2 * (ci / 1.96) ** 2).sum(0))
    gains = np.array([r["impulse"]["cum_gain_dev"] for r in runs])
    gci = np.array([r["impulse"]["cum_gain_dev_ci95"] for r in runs])
    g = float((w * gains).sum() / w.sum())
    gse = float(np.sqrt(((w / w.sum()) ** 2 * (gci / 1.96) ** 2).sum()))
    dev0 = float((w * np.array([r["impulse"]["d_beta_dev"][0] for r in runs])).sum() / w.sum())
    return mean, 1.96 * se, g, 1.96 * gse, int(w.sum()), dev0


def fmt(x: float, d: int = 2) -> str:
    return "--" if not np.isfinite(x) else f"{x:.{d}f}"


def pm(m: float, c: float, d: int = 2) -> str:
    return f"{fmt(m, d)} \\pm {fmt(c, d)}"


def macro(name: str, value: str) -> None:
    macros[name] = value


# --------------------------------------------------------------- experiments
exp5 = load("exp5_controls/*.json")
exp4 = load("exp4/*.json")
exp6 = load("exp6_alpha/*.json")
exp3 = load("exp3/*.json")
exp7 = load("exp7_dou/*.json")
exp2 = load("exp2/*.json")


def sel(runs, **kw):
    out = []
    for r in runs:
        ok = True
        for k, v in kw.items():
            if k == "gamma":
                g = r["agent_kwargs"].get("gamma", 0.95)
                ok &= abs(g - v) < 1e-9
            elif k == "alpha":
                ok &= abs(r["agent_kwargs"].get("alpha", 0.15) - v) < 1e-9
            elif k == "schedule":
                ok &= r["agent_kwargs"].get("alpha_schedule", "const") == v
            else:
                ok &= r["config"].get(k) == v
        if ok:
            out.append(r)
    return out


# ---------------------------------------------- Table 1 / Figure 1: xi = 0 core
core_rows = []  # (label, runs, colour)
if exp5:
    core_rows += [
        ("Remembers rivals ($\\gamma=0.95$)", sel(exp5, memory="residual", gamma=0.95), C["strategic"]),
        ("Remembers rivals, myopic ($\\gamma=0$)", sel(exp5, memory="residual", gamma=0.0), C["myopic"]),
        ("No memory ($\\gamma=0.95$)", sel(exp5, memory="none", gamma=0.95), C["none"]),
        ("No memory, myopic ($\\gamma=0$)", sel(exp5, memory="none", gamma=0.0), C["grey"]),
    ]
if exp4:
    core_rows.append(("Perfect monitoring ($\\gamma=0.95$)", sel(exp4, memory="orders"), C["orders"]))

core_rows = [row for row in core_rows if row[1]]
if core_rows:
    lines = [
        "\\begin{tabular}{lccccccc}",
        "\\toprule",
        "Condition & $\\Delta$ intensity & $\\Delta$ inform. & $\\Delta$ profit & "
        "Rival $\\Delta\\beta_1$ & $\\Delta\\beta_1/\\Delta\\beta^{\\mathrm{dev}}_0$ & Deviator gain & Markets \\\\",
        "\\midrule",
    ]
    for label, runs, _ in core_rows:
        di = pooled(runs, "delta_intensity")
        dinf = pooled(runs, "delta_info")
        dp = pooled(runs, "delta_profit")
        imp = impulse_pooled(runs)
        rv = pm(imp[0][1], imp[1][1], 3) if imp else "--"
        gn = pm(imp[2], imp[3], 3) if imp else "--"
        ratio = fmt(imp[0][1] / imp[5], 2) if imp and imp[5] else "--"
        lines.append(
            f"{label} & ${pm(*di[:2])}$ & ${pm(*dinf[:2])}$ & ${pm(*dp[:2])}$ & "
            f"${rv}$ & ${ratio}$ & ${gn}$ & {di[2]} \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_core.tex"), "w").write("\n".join(lines))

    fig, ax = plt.subplots(figsize=(6.2, 2.4))
    labels = [l.replace("$\\gamma=", "γ=").replace("$", "") for l, _, _ in core_rows]
    ys = np.arange(len(core_rows))[::-1]
    for y, (label, runs, col) in zip(ys, core_rows):
        m, c, _ = pooled(runs, "delta_intensity")
        ax.barh(y, m, xerr=c, color=col, height=0.6, capsize=2, error_kw={"lw": 0.8})
        ax.text(m + (0.03 if m >= 0 else -0.03), y, f"{m:.2f}", va="center",
                ha="left" if m >= 0 else "right", fontsize=8)
    ax.set_yticks(ys, labels)
    ax.axvline(0, color="k", lw=0.6)
    ax.axvline(1, color=C["grey"], lw=0.6, ls="--")
    ax.set_xlabel("Collusion index Δ (trading intensity):  0 = Nash,  1 = cartel")
    ax.set_xlim(min(-0.2, ax.get_xlim()[0]), 1.1)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_core.pdf"))
    plt.close(fig)

    r = sel(exp5, memory="residual", gamma=0.95)
    if r:
        m, c, n = pooled(r, "delta_intensity")
        macro("ResidDeltaInt", fmt(m))
        macro("ResidDeltaIntCI", fmt(c))
    r = sel(exp5, memory="residual", gamma=0.0)
    if r:
        m, c, n = pooled(r, "delta_intensity")
        macro("MyopicResidDeltaInt", fmt(m))
        macro("MyopicResidDeltaIntCI", fmt(c))
    r = sel(exp5, memory="none", gamma=0.95)
    if r:
        m, c, n = pooled(r, "delta_intensity")
        macro("NoneDeltaInt", fmt(m))
    r = sel(exp5, memory="none", gamma=0.0)
    if r:
        m, c, n = pooled(r, "delta_intensity")
        macro("MyopicNoneDeltaInt", fmt(m))
    r = sel(exp4, memory="orders")
    if r:
        m, c, n = pooled(r, "delta_intensity")
        macro("OrdersDeltaInt", fmt(m))
        imp = impulse_pooled(r)
        if imp:
            macro("OrdersRivalLagOne", fmt(imp[0][1], 3))
            macro("OrdersGain", fmt(imp[2], 3))
            macro("OrdersReactionPct", fmt(100 * imp[0][1] / imp[5], 0))

# ------------------------------------------ Figure 2: deviation impulse (xi=0)
irf_rows = [(l, r, c) for l, r, c in core_rows if impulse_pooled(r)]
if irf_rows:
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.3))
    for label, runs, col in irf_rows:
        mean, ci, *_ = impulse_pooled(runs)
        k = np.arange(len(mean))[:9]
        lab = label.replace("$\\gamma=", "γ=").replace("$", "")
        axes[0].errorbar(k, mean[:9], yerr=ci[:9], color=col, marker="o", ms=3, lw=1, capsize=2, label=lab)
        dm, dci, *_ = impulse_pooled(runs, "d_profit_dev")
        axes[1].errorbar(k, dm[:9], yerr=dci[:9], color=col, marker="o", ms=3, lw=1, capsize=2)
    for ax in axes:
        ax.axhline(0, color="k", lw=0.6)
        ax.set_xlabel("Periods after the deviation")
    axes[0].set_ylabel("Rivals' change in intensity")
    axes[1].set_ylabel("Deviator's change in profit")
    axes[0].legend(fontsize=6.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_deviation.pdf"))
    plt.close(fig)

# -------------------------------------------- Figure 3: learning-rate effects
alpha_pts = {}
for mem in ("residual", "none"):
    pts = []
    for a in (0.05, 0.15, 0.3):
        runs = sel(exp6, memory=mem, alpha=a) if a != 0.15 else sel(exp5, memory=mem, gamma=0.95)
        if a != 0.15:
            runs = [r for r in runs if "alpha" in r["agent_kwargs"]]
        if runs:
            m, c, _ = pooled(runs, "delta_intensity")
            pts.append((a, m, c))
    if pts:
        alpha_pts[mem] = pts
visits = {mem: sel(exp3, memory=mem, schedule="visits") for mem in ("residual", "none", "flow")}
if alpha_pts:
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for mem, col, lab in (("residual", C["strategic"], "remembers rivals"), ("none", C["none"], "no memory")):
        if mem not in alpha_pts:
            continue
        a, m, c = zip(*alpha_pts[mem])
        ax.errorbar(a, m, yerr=c, color=col, marker="o", ms=4, lw=1.2, capsize=2, label=f"constant α, {lab}")
        if visits.get(mem):
            vm, vc, _ = pooled(visits[mem], "delta_intensity")
            ax.errorbar([0.34], [vm], yerr=[vc], color=col, marker="s", ms=4, mfc="white", capsize=2)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xlabel("Step size α   (open squares: decaying step size)")
    ax.set_ylabel("Δ intensity")
    ax.legend(fontsize=6.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_alpha.pdf"))
    plt.close(fig)
    for mem, pts in alpha_pts.items():
        for a, m, c in pts:
            tag = {"residual": "Resid", "none": "None"}[mem] + {0.05: "Low", 0.15: "Mid", 0.3: "High"}[a]
            macro(f"Alpha{tag}", fmt(m))
for mem, runs in visits.items():
    if runs:
        m, c, _ = pooled(runs, "delta_intensity")
        macro("Visits" + mem.capitalize(), fmt(m))

# -------------------------------------------------- Figure 4: Dou regime
if exp7:
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4), sharey=False)
    rows = []
    for ax, xi in zip(axes, (0.0, 500.0)):
        for gam, mem, col, lab in ((0.95, "price", C["strategic"], "γ=0.95, remembers price"),
                                   (0.0, "price", C["myopic"], "γ=0 (myopic placebo)"),
                                   (0.95, "none", C["none"], "γ=0.95, no memory")):
            runs = [r for r in sel(exp7, memory=mem, gamma=gam) if abs(r["config"]["xi"] - xi) < 1e-9]
            if not runs:
                continue
            r = runs[0]
            m, c, _ = pooled(runs, "delta_intensity")
            shocks = {round(s["shock_devs"], 3): s for s in r.get("noise_shocks", [])}
            sh = shocks.get(1.0)
            imp = impulse_pooled(runs)
            rows.append((xi, lab, m, c, sh, imp))
            if sh:
                k = np.arange(len(sh["d_beta_all"]))[:6]
                scale = r["benchmarks"]["beta_nash"]
                ax.errorbar(k, np.array(sh["d_beta_all"][:6]) / scale,
                            yerr=np.array(sh["d_beta_all_ci95"][:6]) / scale,
                            color=col, marker="o", ms=3, lw=1, capsize=2, label=lab)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_title(f"ξ = {int(xi)}")
        ax.set_xlabel("Periods after a 1-deviation noise shock")
    axes[0].set_ylabel("Change in intensity / β$^N$")
    axes[1].legend(fontsize=6.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_dou.pdf"))
    plt.close(fig)

    lines = ["\\begin{tabular}{llccc}", "\\toprule",
             "$\\xi$ & Learners & $\\Delta$ intensity & Shock response $\\Delta\\beta_1/\\beta^N$ & "
             "Rival $\\Delta\\beta_1/\\beta^N$ after deviation \\\\", "\\midrule"]
    for xi, lab, m, c, sh, imp in rows:
        s1 = "--"
        scale = None
        runs = [r for r in exp7 if abs(r["config"]["xi"] - xi) < 1e-9]
        if runs:
            scale = runs[0]["benchmarks"]["beta_nash"]
        if sh and scale:
            s1 = pm(sh["d_beta_all"][1] / scale, sh["d_beta_all_ci95"][1] / scale, 3)
        d1 = pm(imp[0][1] / scale, imp[1][1] / scale, 3) if imp and scale else "--"
        lab_tex = lab.replace("γ", "$\\gamma$")
        lines.append(f"{int(xi)} & {lab_tex} & ${pm(m, c)}$ & ${s1}$ & ${d1}$ \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_dou.tex"), "w").write("\n".join(lines))

    for xi, lab, m, c, sh, imp in rows:
        key = ("Kyle" if xi == 0 else "Dou") + {"γ=0.95, remembers price": "Strat",
                                              "γ=0 (myopic placebo)": "Myopic",
                                              "γ=0.95, no memory": "None"}[lab]
        macro(key + "DeltaInt", fmt(m))
        runs = [r for r in exp7 if abs(r["config"]["xi"] - xi) < 1e-9]
        if sh and runs:
            macro(key + "Shock", fmt(sh["d_beta_all"][1] / runs[0]["benchmarks"]["beta_nash"], 3))

# ----------------------------------------------------------- misc numbers
if exp3:
    r = sel(exp3, memory="residual", schedule="const")
    if r:
        m, c, _ = pooled(r, "order_shift_onpath")
        macro("ConstShift", fmt(m))
    r = sel(exp3, memory="residual", schedule="visits")
    if r:
        m, c, _ = pooled(r, "order_shift_onpath")
        macro("VisitsShift", fmt(m))

with open(os.path.join(ROOT, "paper", "numbers.tex"), "w") as fh:
    fh.write("% generated by paper/make_results.py -- do not edit\n")
    for k, v in sorted(macros.items()):
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    fh.write("\\providecommand{\\ResultsSummarySentence}{}\n")
    fh.write("\\providecommand{\\ResidDeltaInt}{--}\n")
print(f"wrote {len(macros)} macros; figures: {sorted(os.listdir(FIG))}")
