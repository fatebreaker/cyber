"""Build every figure and number in the paper from results/*.json.

    python paper/make_results.py   # from the repository root

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
import matplotlib.ticker  # noqa: E402,F401
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
    # Show at least one significant digit of the CI instead of a misleading "0.00".
    if np.isfinite(c) and 0 < c < 0.5 * 10 ** (-d):
        return f"{fmt(m, d + 1)} \\pm {fmt(c, d + 1)}"
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
    top = max(pooled(r, "delta_intensity")[0] for _, r, _ in core_rows)
    ax.set_xlim(min(-0.2, ax.get_xlim()[0]), max(1.1, top + 0.2))
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_core.pdf"))
    plt.close(fig)

    for key, runs in (("Resid", sel(exp5, memory="residual", gamma=0.95)),
                      ("MyopicResid", sel(exp5, memory="residual", gamma=0.0)),
                      ("None", sel(exp5, memory="none", gamma=0.95)),
                      ("MyopicNone", sel(exp5, memory="none", gamma=0.0)),
                      ("Orders", sel(exp4, memory="orders"))):
        if not runs:
            continue
        for metric, tag in (("delta_intensity", "Int"), ("delta_info", "Info"), ("delta_profit", "Profit")):
            m, c, n = pooled(runs, metric)
            macro(f"{key}Delta{tag}", fmt(m))
            macro(f"{key}Delta{tag}CI", fmt(c))
        lo = min(np.nanmean(r["per_session"]["delta_intensity"]) for r in runs)
        hi = max(np.nanmean(r["per_session"]["delta_intensity"]) for r in runs)
        macro(f"{key}SeedRange", f"{lo:.2f}--{hi:.2f}")
        macro(f"{key}Markets", str(sum(len(r["per_session"]["delta_intensity"]) for r in runs)))
        imp = impulse_pooled(runs)
        if imp:
            macro(f"{key}RivalLagOne", fmt(imp[0][1], 3))
            macro(f"{key}RivalLagOneCI", fmt(imp[1][1], 3))
            macro(f"{key}Gain", fmt(imp[2], 3))
            macro(f"{key}GainCI", fmt(imp[3], 3))
            if imp[5]:
                macro(f"{key}ReactionPct", fmt(100 * imp[0][1] / imp[5], 0))
        sh = pooled(runs, "order_shift_onpath")
        macro(f"{key}Shift", fmt(sh[0]))
    r = sel(exp5, memory="residual", gamma=0.95)
    if r:
        m, c, n = pooled(r, "delta_intensity")
        macro("ResidDeltaInt", fmt(m))

# ------------------------------------------ Figure 2: deviation impulse (xi=0)
irf_rows = [(l, r, c) for l, r, c in core_rows if impulse_pooled(r)]
if irf_rows:
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.8))
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
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0.16, 1, 1))
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
        ax.errorbar(a, m, yerr=c, color=col, marker="o", ms=4, lw=1.2, capsize=2, label=lab)
    ax.axhline(0, color="k", lw=0.6)
    ax.axhline(1, color=C["grey"], lw=0.6, ls="--")
    ax.set_xlabel("Step size α  (γ = 0.95)")
    ax.set_ylabel("Δ intensity")
    ax.legend(fontsize=6.5, loc="lower right")
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

# -------------------------------------------------- Dou regime (exp7, exp10-12)
exp10 = load("exp10_shared/*.json")
exp11 = load("exp11_dou_gridprice/*.json")
exp12 = load("exp12_dou_seeds/*.json")
exp13 = load("exp13_seeds/*.json")


def tag_of(r):
    return os.path.basename(r["_file"])[:-5]


def dou_runs(xi, gamma, memory="price", shared=False, binning=None):
    """Runs for one Dou-regime cell. At xi = 500 the price state uses grid
    binning (exp11/12, pooled over seeds) unless binning='noise' asks for the
    original noise-unit runs (exp7/exp10)."""
    def match(r):
        return (abs(r["config"]["xi"] - xi) < 1e-9 and r["config"]["memory"] == memory
                and abs(r["agent_kwargs"].get("gamma", 0.95) - gamma) < 1e-9
                and bool(r["agent_kwargs"].get("shared", False)) == shared)
    def binning_of(r):
        return r["config"].get("price_bins", "noise")
    if memory == "price" and xi == 500.0 and binning != "noise":
        return [r for r in exp11 + exp12 + exp13 if match(r) and binning_of(r) == "grid"]
    pool = (exp10 if shared else exp7) + exp13
    return [r for r in pool if match(r) and (memory != "price" or binning_of(r) == "noise")
            and r["config"].get("sigma_u") == 0.1]


def shock_pooled(runs, devs, lag=1):
    """Event-weighted response at `lag` to a shock of `devs` deviation units,
    as a percentage of beta^N, combined across runs."""
    ms, ses, ws = [], [], []
    for r in runs:
        bn = r["benchmarks"]["beta_nash"]
        for sh in r.get("noise_shocks", []):
            if abs(sh["shock_devs"] - devs) < 1e-9:
                ms.append(100 * sh["d_beta_all"][lag] / bn)
                ses.append(100 * sh["d_beta_all_ci95"][lag] / bn / 1.96)
                ws.append(sh["n_events"])
    if not ms:
        return float("nan"), float("nan")
    w = np.array(ws, float) / sum(ws)
    return float((w * ms).sum()), float(1.96 * np.sqrt((w**2 * np.array(ses) ** 2).sum()))


def shock_profile(runs, devs, K=6):
    prof = [shock_pooled(runs, devs, lag=k) for k in range(K)]
    return np.array([p[0] for p in prof]), np.array([p[1] for p in prof])


def rival_pct(runs):
    imp = impulse_pooled(runs)
    if not imp:
        return float("nan"), float("nan"), float("nan"), float("nan")
    bn = runs[0]["benchmarks"]["beta_nash"]
    return 100 * imp[0][1] / bn, 100 * imp[1][1] / bn, imp[2], imp[3]


DOU_ROWS = [  # (xi, gamma, memory, label, macro key)
    (0.0, 0.95, "price", "$\\gamma=0.95$, remembers price", "KyleStrat"),
    (0.0, 0.0, "price", "$\\gamma=0$ (myopic placebo)", "KyleMyopic"),
    (0.0, 0.95, "none", "$\\gamma=0.95$, no memory", "KyleNone"),
    (500.0, 0.95, "price", "$\\gamma=0.95$, remembers price", "DouStrat"),
    (500.0, 0.0, "price", "$\\gamma=0$ (myopic placebo)", "DouMyopic"),
    (500.0, 0.95, "none", "$\\gamma=0.95$, no memory", "DouNone"),
]
if exp7:
    lines_t = ["\\begin{tabular}{llccccc}", "\\toprule",
               "$\\xi$ & Separate Q-tables & $\\Delta$ intensity & $\\Delta$ profit & Shock response & "
               "Rival reaction & Seeds \\\\", "\\midrule"]
    for xi, g, mem, lab, key in DOU_ROWS:
        runs = dou_runs(xi, g, mem)
        if not runs:
            continue
        di, dp = pooled(runs, "delta_intensity"), pooled(runs, "delta_profit")
        s1 = shock_pooled(runs, 1.0)
        rv = rival_pct(runs)
        macro(key + "DeltaInt", fmt(di[0]))
        macro(key + "Shock", fmt(s1[0], 2))
        macro(key + "ShockCI", fmt(s1[1], 2))
        macro(key + "Rival", fmt(rv[0], 2))
        macro(key + "RivalCI", fmt(rv[1], 2))
        lines_t.append(f"{int(xi)} & {lab} & ${pm(*di[:2])}$ & ${pm(*dp[:2])}$ & ${pm(*s1)}$ & "
                       f"${pm(rv[0], rv[1])}$ & {len(runs)} \\\\")
    lines_t += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_dou.tex"), "w").write("\n".join(lines_t))

    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.5))
    for ax, xi in zip(axes, (0.0, 500.0)):
        for g, mem, col, lab in ((0.95, "price", C["strategic"], "γ=0.95, remembers price"),
                                 (0.0, "price", C["myopic"], "γ=0 (myopic placebo)"),
                                 (0.95, "none", C["none"], "γ=0.95, no memory")):
            runs = dou_runs(xi, g, mem)
            if not runs:
                continue
            m, c = shock_profile(runs, 1.0)
            ax.errorbar(np.arange(len(m)), m, yerr=c, color=col, marker="o", ms=3, lw=1, capsize=2, label=lab)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_title(f"ξ = {int(xi)}")
        ax.set_xlabel("Periods after a 1-deviation noise shock")
    axes[0].set_ylabel("Intensity change (% of β$^N$)")
    axes[1].legend(fontsize=6.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_dou.pdf"))
    plt.close(fig)

# --------------------------------------- Figure: deviation detectability (theory)
import sys  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "src"))
from kylecollusion.theory import deviation_gap, kyle_benchmarks  # noqa: E402

xis = np.logspace(-1, 4, 200)
fig, ax = plt.subplots(figsize=(3.4, 2.4))
for I, col in ((2, C["strategic"]), (3, C["myopic"]), (5, C["none"])):
    snr = [deviation_gap(kyle_benchmarks(I, 1.0, 0.1, xi=x, theta=0.1)) / 0.1 for x in xis]
    ax.loglog(xis, snr, color=col, lw=1.4, label=f"I = {I}")
    ax.axhline((I - 1) / (2 * I), color=col, lw=0.6, ls=":")
ax.axhline(1.0, color="k", lw=0.6)
ax.text(0.12, 1.25, "deviation = 1 noise sd", fontsize=7)
ax.axvline(500, color=C["grey"], lw=0.6, ls="--")
ax.text(430, 2e3, "Dou et al.\nξ = 500", fontsize=7, color=C["grey"], ha="right")
ax.set_xlabel("Information-insensitive investors ξ")
ax.set_ylabel("Deviation signal-to-noise")
ax.legend(fontsize=7, loc="upper left")
ax.set_ylim(0.1, 3e4)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_snr.pdf"))
plt.close(fig)

# -------------------------------------- Figure: single-trader pruning mechanism
mech_f = os.path.join(RES, "mechanism", "single_trader.json")
mech_g = os.path.join(RES, "mechanism", "single_trader_gamma.json")
if os.path.exists(mech_f):
    mech = json.load(open(mech_f))
    has_g = os.path.exists(mech_g)
    fig, axes = plt.subplots(1, 2 if has_g else 1, figsize=(6.4 if has_g else 3.4, 2.4), squeeze=False)
    ax = axes[0, 0]
    a_arr = np.array(mech["alphas"])
    short = 1 - np.array([mech["results"][f"taken_{x}"]["mean"] for x in mech["alphas"]])
    c_fit = float((np.sqrt(a_arr) * short).sum() / a_arr.sum())  # least squares through origin
    resid = short - c_fit * np.sqrt(a_arr)
    r2 = 1 - (resid**2).sum() / ((short - short.mean()) ** 2).sum()
    macro("MechSqrtCoef", fmt(c_fit))
    macro("MechSqrtRsq", fmt(r2, 3))
    for upd, col, lab in (("taken", C["strategic"], "standard Q-learning"),
                          ("counterfactual", C["none"], "counterfactual updates")):
        m = [mech["results"][f"{upd}_{x}"]["mean"] for x in mech["alphas"]]
        c = [mech["results"][f"{upd}_{x}"]["ci95"] for x in mech["alphas"]]
        ax.errorbar(mech["alphas"], m, yerr=c, color=col, marker="o", ms=4, lw=1.2, capsize=2, label=lab)
    xs = np.geomspace(a_arr.min(), a_arr.max(), 100)
    ax.plot(xs, 1 - c_fit * np.sqrt(xs), color=C["grey"], lw=0.8, ls="--", label=f"1 − {c_fit:.2f}√α")
    ax.axhline(1.0, color="k", lw=0.6)
    ax.set_xscale("log")
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xticks(mech["alphas"], [str(x) for x in mech["alphas"]])
    ax.set_xlabel("Step size α  (γ = 0)")
    ax.set_ylabel("Learned / optimal intensity")
    ax.set_title("(a) step size")
    ax.legend(fontsize=6.5)
    for upd, tag in (("taken", "Taken"), ("counterfactual", "Cf")):
        for x, name in zip(mech["alphas"], ("A", "B", "C", "D", "E")):
            macro(f"Mech{tag}{name}", fmt(mech["results"][f"{upd}_{x}"]["mean"]))
    if has_g:
        mg = json.load(open(mech_g))
        ax = axes[0, 1]
        g = [float(x) for x in mg["gammas"]]
        m = [mg["results"][str(x)]["mean"] for x in mg["gammas"]]
        c = [mg["results"][str(x)]["ci95"] for x in mg["gammas"]]
        ax.errorbar(g, m, yerr=c, color=C["strategic"], marker="o", ms=4, lw=1.2, capsize=2)
        ax.axhline(1.0, color="k", lw=0.6)
        ax.set_xlabel(f"Discount factor γ  (α = {mg['alpha']})")
        ax.set_title("(b) discount factor")
        ax.set_ylim(axes[0, 0].get_ylim())
        for x, name in zip(mg["gammas"], ("A", "B", "C", "D")):
            macro(f"MechGamma{name}", fmt(mg["results"][str(x)]["mean"]))
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_mechanism.pdf"))
    plt.close(fig)

# ------------------------------------------ interventions (exp9) and deep RL (exp8)
exp9 = load("exp9_interventions/*.json")
exp8 = load("exp8_deep/*.json")
NAMES = {
    "random35": "RandomMem", "random35_myopic": "RandomMemMyopic",
    "counterfactual_residual": "CfResid", "counterfactual_none": "CfNone",
    "counterfactual_residual_myopic": "CfResidMyopic",
    "opaque_residual": "Opaque", "passive2_residual": "Passive",
    "dqn_g095": "Dqn", "dqn_g0": "DqnMyopic", "ppo_g095": "Ppo", "ppo_g0": "PpoMyopic",
}
design_rows = []
groups: dict[str, list] = {}
for r in exp9 + exp8 + [x for x in exp13 if os.path.basename(x["_file"])[:-5] in NAMES]:
    groups.setdefault(os.path.basename(r["_file"])[:-5], []).append(r)
for tag, grp in groups.items():
    key = NAMES.get(tag)
    if not key:
        continue
    r = grp  # list of seeds
    for metric, t in (("delta_intensity", "Int"), ("delta_profit", "Profit"), ("delta_info", "Info")):
        m, c, _ = pooled(r, metric)
        macro(f"{key}Delta{t}", fmt(m))
        macro(f"{key}Delta{t}CI", fmt(c))
    imp = impulse_pooled(r)
    if imp:
        macro(f"{key}RivalLagOne", fmt(imp[0][1], 3))
        macro(f"{key}RivalLagOneCI", fmt(imp[1][1], 3))
        macro(f"{key}Gain", fmt(imp[2], 3))
        macro(f"{key}GainCI", fmt(imp[3], 3))
    design_rows.append((tag, key, r, imp))

LABELS = {
    "random35": "Random memory, 35 states", "random35_myopic": "Random memory, myopic",
    "counterfactual_residual": "Counterfactual updates, residual memory",
    "counterfactual_none": "Counterfactual updates, no memory",
    "counterfactual_residual_myopic": "Counterfactual updates, residual, myopic",
    "opaque_residual": "Reduced transparency (disclosure noise $2\\sigma_u$)",
    "passive2_residual": "Two passive Nash traders",
    "dqn_g095": "DQN", "dqn_g0": "DQN, myopic", "ppo_g095": "PPO", "ppo_g0": "PPO, myopic",
}
if design_rows:
    order = list(LABELS)
    design_rows.sort(key=lambda x: order.index(x[0]) if x[0] in order else 99)
    lines = ["\\begin{tabular}{lcccc}", "\\toprule",
             "Treatment ($\\xi=0$, $I=2$) & $\\Delta$ intensity & $\\Delta$ profit & Rival $\\Delta\\beta_1$ & Deviator gain \\\\",
             "\\midrule"]
    for tag, key, r, imp in design_rows:
        di = pooled(r, "delta_intensity")
        dp = pooled(r, "delta_profit")
        rv = pm(imp[0][1], imp[1][1], 3) if imp else "--"
        gn = pm(imp[2], imp[3], 3) if imp else "--"
        lines.append(f"{LABELS.get(tag, tag)} & ${pm(*di[:2])}$ & ${pm(*dp[:2])}$ & ${rv}$ & ${gn}$ \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_design.tex"), "w").write("\n".join(lines))

# ------------------------------------------------- Figure: interventions
bars = []
base = sel(exp5, memory="residual", gamma=0.95)
if base:
    bars.append(("Baseline: remembers rivals", base, C["strategic"], "baseline"))
by_tag = groups  # tag -> list of seeds
for tag, lab, grp in (("opaque_residual", "Reduced transparency", "information"),
                      ("random35", "Uninformative random memory", "information"),
                      ("counterfactual_residual", "Counterfactual updates", "learning"),
                      ("counterfactual_none", "Counterfactual, no memory", "learning")):
    if tag in by_tag:
        col = {"information": C["flow"], "market": C["grey"], "learning": C["none"]}[grp]
        bars.append((lab, by_tag[tag], col, grp))
vis = sel(exp3, memory="residual", schedule="visits")
if vis:
    bars.append(("Decaying step sizes", vis, C["myopic"], "learning"))
if len(bars) > 1:
    fig, ax = plt.subplots(figsize=(6.2, 2.5))
    ys = np.arange(len(bars))[::-1]
    for y, (lab, runs, col, grp) in zip(ys, bars):
        m, c, _ = pooled(runs, "delta_intensity")
        ax.barh(y, m, xerr=c, color=col, height=0.6, capsize=2, error_kw={"lw": 0.8})
        ax.text(m + (0.03 if m >= 0 else -0.03), y, f"{m:.2f}", va="center",
                ha="left" if m >= 0 else "right", fontsize=8)
    ax.set_yticks(ys, [b[0] for b in bars])
    ax.axvline(0, color="k", lw=0.6)
    ax.axvline(1, color=C["grey"], lw=0.6, ls="--")
    ax.set_xlim(-0.85, 1.15)
    ax.set_xlabel("Collusion index Δ (trading intensity):  0 = Nash,  1 = cartel")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C["flow"], label="information"),
                       Patch(color=C["none"], label="learning rule"), Patch(color=C["myopic"], label="step-size schedule")],
              fontsize=6.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_design.pdf"))
    plt.close(fig)

pas_runs = by_tag.get("passive2_residual")
if pas_runs:
    a = np.concatenate([np.array(x["per_session"]["agg_intensity"]) for x in pas_runs])
    p = np.concatenate([np.array(x["per_session"]["profit"]) for x in pas_runs])
    b = pas_runs[0]["benchmarks"]
    macro("PassiveAgg", fmt(a.mean()))
    macro("PassiveAggNash", fmt(b["agg_nash"]))
    macro("PassiveAggColl", fmt(b["agg_coll"]))
    macro("PassiveProfitPct", fmt(100 * (1 - p.mean() / b["profit_nash"]), 0))

# ---------------------------------------------- shared tables (exp10-12)
SHARED_ROWS = [
    (0.0, 0.95, "$\\gamma=0.95$", "SharedKyleStrat"),
    (0.0, 0.0, "$\\gamma=0$ (myopic placebo)", "SharedKyleMyopic"),
    (500.0, 0.95, "$\\gamma=0.95$", "SharedDouStrat"),
    (500.0, 0.0, "$\\gamma=0$ (myopic placebo)", "SharedDouMyopic"),
]
if exp10 or exp11:
    lines_t = ["\\begin{tabular}{llcccccc}", "\\toprule",
               "$\\xi$ & Shared Q-table & $\\Delta$ intensity & \\multicolumn{3}{c}{Shock response (\\% of $\\beta^N$)} & Rival reaction & Seeds \\\\",
               " & & & 0.05 & 0.25 & 1 & (\\% of $\\beta^N$) & \\\\", "\\midrule"]
    for xi, g, lab, key in SHARED_ROWS:
        runs = dou_runs(xi, g, "price", shared=True)
        if not runs:
            continue
        di = pooled(runs, "delta_intensity")
        cells = []
        for dv, nm in ((0.05, "Small"), (0.25, "Mid"), (1.0, "Large")):
            m, c = shock_pooled(runs, dv)
            cells.append(pm(m, c))
            macro(f"{key}Shock{nm}", fmt(m, 2))
            macro(f"{key}Shock{nm}CI", fmt(c, 2))
        rv = rival_pct(runs)
        macro(f"{key}DeltaInt", fmt(di[0]))
        macro(f"{key}Rival", fmt(rv[0], 2))
        macro(f"{key}RivalCI", fmt(rv[1], 2))
        macro(f"{key}Gain", fmt(rv[2], 2))
        lines_t.append(f"{int(xi)} & {lab} & ${pm(*di[:2])}$ & ${cells[0]}$ & ${cells[1]}$ & ${cells[2]}$ & "
                       f"${pm(rv[0], rv[1])}$ & {len(runs)} \\\\")
    lines_t += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_shared.tex"), "w").write("\n".join(lines_t))

    fig, ax = plt.subplots(figsize=(3.6, 2.5))
    for xi, g, col, ls, lab in ((500.0, 0.0, C["myopic"], "-", "ξ=500, myopic (γ=0)"),
                                (500.0, 0.95, C["strategic"], "-", "ξ=500, γ=0.95"),
                                (0.0, 0.0, C["myopic"], ":", "ξ=0, myopic (γ=0)"),
                                (0.0, 0.95, C["strategic"], ":", "ξ=0, γ=0.95")):
        runs = dou_runs(xi, g, "price", shared=True)
        if not runs:
            continue
        xs = [0.05, 0.25, 1.0]
        mc = [shock_pooled(runs, x) for x in xs]
        ax.errorbar(xs, [m for m, _ in mc], yerr=[c for _, c in mc], color=col, ls=ls, marker="o",
                    ms=4, lw=1.2, capsize=2, label=lab)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xscale("log")
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xticks([0.05, 0.25, 1.0], ["0.05", "0.25", "1"])
    ax.set_xlabel("Noise shock (deviation units)")
    ax.set_ylabel("Lag-1 intensity change\n(% of β$^N$)")
    ax.legend(fontsize=6.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_shared.pdf"))
    plt.close(fig)

    # Appendix: price-state binning robustness at xi = 500
    lines_t = ["\\begin{tabular}{llcccc}", "\\toprule",
               "Learners ($\\xi=500$) & Price state & $\\Delta$ intensity & Shock response (1 dev.) & Rival reaction & Seeds \\\\",
               "\\midrule"]
    for shared, g, lab in ((False, 0.95, "Separate, $\\gamma=0.95$"), (False, 0.0, "Separate, $\\gamma=0$"),
                           (True, 0.95, "Shared, $\\gamma=0.95$"), (True, 0.0, "Shared, $\\gamma=0$")):
        for binning, bl in (("noise", "noise units"), ("grid", "grid range")):
            runs = dou_runs(500.0, g, "price", shared=shared, binning=binning)
            if not runs:
                continue
            di = pooled(runs, "delta_intensity")
            s1 = shock_pooled(runs, 1.0)
            rv = rival_pct(runs)
            lines_t.append(f"{lab} & {bl} & ${pm(*di[:2])}$ & ${pm(*s1)}$ & ${pm(rv[0], rv[1])}$ & {len(runs)} \\\\")
    lines_t += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_binning.tex"), "w").write("\n".join(lines_t))


if exp8:
    lines = ["\\begin{tabular}{lcccc}", "\\toprule",
             "Learner (residual memory) & $\\Delta$ intensity & $\\Delta$ informativeness & Rival $\\Delta\\beta_1$ & Deviator gain \\\\",
             "\\midrule"]
    tabq = [("Tabular Q, $\\gamma=0.95$", sel(exp5, memory="residual", gamma=0.95)),
            ("Tabular Q, $\\gamma=0$", sel(exp5, memory="residual", gamma=0.0))]
    deep = [(f"{lab}", [r for r in exp8 if os.path.basename(r["_file"])[:-5] == tag])
            for tag, lab in (("dqn_g095", "DQN, $\\gamma=0.95$"), ("dqn_g0", "DQN, $\\gamma=0$"),
                             ("ppo_g095", "PPO, $\\gamma=0.95$"), ("ppo_g0", "PPO, $\\gamma=0$"))]
    for lab, runs in tabq + deep:
        if not runs:
            continue
        di, dinf = pooled(runs, "delta_intensity"), pooled(runs, "delta_info")
        imp = impulse_pooled(runs)
        rv = pm(imp[0][1], imp[1][1], 3) if imp else "--"
        gn = pm(imp[2], imp[3], 3) if imp else "--"
        lines.append(f"{lab} & ${pm(*di[:2])}$ & ${pm(*dinf[:2])}$ & ${rv}$ & ${gn}$ \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_deep.tex"), "w").write("\n".join(lines))

# ------------------------------------------------ Appendix: robustness table
exp1 = load("exp1/q_*.json")
rob = []
for label, runs in (
    ("Residual, $1.5\\times10^6$ periods, $\\beta=4\\times10^{-6}$", sel(exp1, memory="residual")),
    ("Residual, $6\\times10^6$, $\\beta=10^{-6}$, seed 0", [r for r in sel(exp5, memory="residual", gamma=0.95) if r["seed"] == 0]),
    ("Residual, $6\\times10^6$, $\\beta=10^{-6}$, seed 1", [r for r in sel(exp5, memory="residual", gamma=0.95) if r["seed"] == 1]),
    ("Residual, $6\\times10^6$, $\\beta=10^{-6}$, seed 2", [r for r in sel(exp5, memory="residual", gamma=0.95) if r["seed"] == 2]),
    ("Residual, $1.5\\times10^7$, $\\beta=4\\times10^{-7}$", sel(exp4, memory="residual")),
    ("Flow, $1.5\\times10^6$, $\\beta=4\\times10^{-6}$", sel(exp1, memory="flow")),
    ("Flow, $6\\times10^6$, $\\beta=10^{-6}$", sel(exp2, memory="flow")),
    ("No memory, $1.5\\times10^6$, $\\beta=4\\times10^{-6}$", sel(exp1, memory="none")),
    ("No memory, $6\\times10^6$, $\\beta=10^{-6}$ (3 seeds)", sel(exp5, memory="none", gamma=0.95)),
    ("No memory, $1.5\\times10^7$, $\\beta=4\\times10^{-7}$", sel(exp4, memory="none")),
):
    if runs:
        rob.append((label, pooled(runs, "delta_intensity"), pooled(runs, "delta_info")))
if rob:
    lines = ["\\begin{tabular}{lcc}", "\\toprule",
             "Configuration ($\\gamma=0.95$, $\\alpha=0.15$) & $\\Delta$ intensity & $\\Delta$ informativeness \\\\",
             "\\midrule"]
    for label, di, dinf in rob:
        lines.append(f"{label} & ${pm(*di[:2])}$ & ${pm(*dinf[:2])}$ \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_robust.tex"), "w").write("\n".join(lines))

# ---------------------------------------- three traders (exp14)
exp14 = {tag_of(r): r for r in load("exp14_three_traders/*.json")}
for tag, key in (("residual_g095", "Three"), ("residual_g0", "ThreeMyopic"),
                 ("none_g095", "ThreeNone"), ("counterfactual_residual", "ThreeCf")):
    if tag in exp14:
        r = [exp14[tag]]
        m, c, _ = pooled(r, "delta_intensity")
        macro(f"{key}DeltaInt", fmt(m))
        macro(f"{key}DeltaIntCI", fmt(c))
        imp = impulse_pooled(r)
        if imp:
            macro(f"{key}RivalLagOne", fmt(imp[0][1], 3))
            macro(f"{key}RivalLagOneCI", fmt(imp[1][1], 3))
            macro(f"{key}Gain", fmt(imp[2], 3))
            macro(f"{key}GainCI", fmt(imp[3], 3))

# ---------------------------------------- Dou-scale runs (exp15, 2e8 periods)
exp15 = {tag_of(r): r for r in load("exp15_long/*.json")}
for tag, key in (("shared_g095_200M", "LongShared"), ("shared_g0_200M", "LongSharedMyopic"),
                 ("separate_g095_200M", "LongSep"), ("separate_g0_200M", "LongSepMyopic")):
    if tag in exp15:
        r = [exp15[tag]]
        m, c, _ = pooled(r, "delta_intensity")
        macro(f"{key}DeltaInt", fmt(m))
        macro(f"{key}DeltaIntCI", fmt(c))
        for devs, sfx in ((0.25, "ShockMid"), (1.0, "ShockLarge")):
            sm, sc = shock_pooled(r, devs)
            macro(f"{key}{sfx}", fmt(sm))
            macro(f"{key}{sfx}CI", fmt(sc))
        rv = rival_pct(r)
        macro(f"{key}Rival", fmt(rv[0]))
        macro(f"{key}RivalCI", fmt(rv[1]))
        macro(f"{key}Gain", fmt(rv[2]))
        if "policy_change_onpath" in r[0]["summary"]:
            macro(f"{key}PolicyChange", fmt(r[0]["summary"]["policy_change_onpath"]["mean"], 3))

# ------------------------------------- Figure: sustainability of collusion
sus_f = os.path.join(RES, "theory", "sustain.json")
if os.path.exists(sus_f):
    sus = json.load(open(sus_f))
    ds = np.array(sus["deltas"])
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4), sharey=True)
    for ax, key, title in ((axes[0], "xi0", "Standard Kyle market (ξ = 0)"),
                           (axes[1], "xi500", "Dou et al. calibration (ξ = 500)")):
        d = sus[key]
        ax.plot(ds, d["any"], color=C["grey"], lw=1.2, ls="--", label="any punishment (necessary)")
        ax.plot(ds, d["grim"], color=C["strategic"], lw=1.4, label="Nash reversion, grim")
        ax.plot(ds, d["T1"], color=C["myopic"], lw=1.4, label="Nash reversion, one period")
        ax.axvline(0.95, color="k", lw=0.5, ls=":")
        ax.set_title(title)
        ax.set_xlabel("Discount factor δ")
        ax.set_ylim(-0.03, 1.05)
    axes[0].set_ylabel("Most collusive sustainable Δ")
    axes[1].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_sustain.pdf"))
    plt.close(fig)
    i95 = sus["deltas"].index(0.95)
    macro("SusKyleGrim", fmt(sus["xi0"]["grim"][i95]))
    macro("SusKyleAny", fmt(sus["xi0"]["any"][i95]))
    macro("SusDouGrim", fmt(sus["xi500"]["grim"][i95]))
    macro("SusDouTOne", fmt(sus["xi500"]["T1"][i95]))
    macro("SusDouTOneMax", fmt(sus["xi500"]["T1"][-1]))
    first = [d for d, x in zip(sus["deltas"], sus["xi500"]["grim"]) if x >= 0.999]
    macro("SusDouGrimDelta", fmt(first[0]) if first else "--")

# ------------------------------- Table: diagnostics outside the Kyle market
sys.path.insert(0, os.path.join(ROOT, "src"))
from kylecollusion.quotes import QuoteConfig, quote_benchmarks  # noqa: E402

_qb = quote_benchmarks(QuoteConfig())
macro("QuoteAN", fmt(_qb["p_nash"]))
macro("QuoteAM", fmt(_qb["p_mono"]))

def _val_rows(market, rows):
    out = []
    for tag, label in rows:
        f = os.path.join(RES, market, f"{tag}.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f))
        b = r["bench"]
        span_p = b["p_mono"] - b["p_nash"]
        span_pi = b["pi_mono"] - b["pi_nash"]
        devs = r["deviation"]
        riv = np.mean([d["d_price_rival"][1] for d in devs]) / span_p
        rivc = np.mean([d["d_price_rival_ci95"][1] for d in devs]) / span_p
        gain = np.mean([d["cum_gain_dev"] for d in devs]) / span_pi
        gainc = np.mean([d["cum_gain_dev_ci95"] for d in devs]) / span_pi
        dp = r["delta"]
        da = r.get("delta_best_ask")
        verdict = "punishment" if (riv + rivc < 0 and gain + gainc < 0) else "no punishment"
        out.append((label, dp, da, (riv, rivc), (gain, gainc), verdict))
    return out


val_b = _val_rows("bertrand", (("baseline", "Baseline ($\\gamma=0.95$, memory)"),
                               ("myopic", "Myopic ($\\gamma=0$)"),
                               ("nomemory", "No memory"),
                               ("random", "Uninformative memory"),
                               ("noise", "Noisy profits ($\\sigma=0.1$)"),
                               ("noise_myopic", "Noisy profits, myopic"),
                               ("counterfactual", "Counterfactual updates")))
val_q = _val_rows("quotes", (("baseline", "Baseline ($\\gamma=0.95$, memory)"),
                             ("myopic", "Myopic ($\\gamma=0$)"),
                             ("nomemory", "No memory"),
                             ("random", "Uninformative memory"),
                             ("counterfactual", "Counterfactual updates"),
                             ("counterfactual_nomemory", "Counterfactual, no memory")))
if val_b or val_q:
    lines = ["\\begin{tabular}{lccccl}", "\\toprule",
             "Learners & $\\Delta$ profit & $\\Delta$ best ask & Rival price response & Deviator gain & Verdict \\\\",
             "\\midrule"]
    for title, rows in (("\\emph{Logit Bertrand (Calvano et al.)}", val_b),
                        ("\\emph{Dealers under adverse selection}", val_q)):
        if not rows:
            continue
        lines.append(f"\\multicolumn{{6}}{{l}}{{{title}}} \\\\")
        for label, dp, da, rv, gn, verdict in rows:
            das = f"${pm(*da)}$" if da else "--"
            lines.append(f"\\quad {label} & ${pm(*dp)}$ & {das} & ${pm(*rv)}$ & ${pm(*gn)}$ & {verdict} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(ROOT, "paper", "table_validation.tex"), "w").write("\n".join(lines))
    vb = {lab: x for lab, *x in val_b}
    for tag, lab in (("Base", "Baseline ($\\gamma=0.95$, memory)"), ("Myopic", "Myopic ($\\gamma=0$)"),
                     ("None", "No memory"), ("Random", "Uninformative memory"),
                     ("Noise", "Noisy profits ($\\sigma=0.1$)"), ("NoiseMyopic", "Noisy profits, myopic"),
                     ("Cf", "Counterfactual updates")):
        if lab in vb:
            macro(f"Bert{tag}", fmt(vb[lab][0][0]))
            macro(f"Bert{tag}Rival", fmt(vb[lab][2][0]))
            macro(f"Bert{tag}Gain", fmt(vb[lab][3][0]))
    vq = {lab: x for lab, *x in val_q}
    for tag, lab in (("Base", "Baseline ($\\gamma=0.95$, memory)"), ("Myopic", "Myopic ($\\gamma=0$)"),
                     ("None", "No memory"), ("Random", "Uninformative memory"),
                     ("Cf", "Counterfactual updates"), ("CfNone", "Counterfactual, no memory")):
        if lab in vq:
            macro(f"Quote{tag}", fmt(vq[lab][1][0]) if vq[lab][1] else "--")
            macro(f"Quote{tag}Profit", fmt(vq[lab][0][0]))
            macro(f"Quote{tag}Rival", fmt(vq[lab][2][0]))
            macro(f"Quote{tag}Gain", fmt(vq[lab][3][0]))
    base = vq.get("Baseline ($\\gamma=0.95$, memory)")
    if base:
        (rv, rvc), (gn, gnc), verdict = base[2], base[3], base[4]
        responds = rv + rvc < 0
        macro("QuoteBaseRivalWord", f"yes (${fmt(rv)}$)" if responds else "no")
        macro("QuoteBaseGainWord", f"loses (${fmt(gn)}$)" if gn + gnc < 0 else f"pays ($+{fmt(gn)}$)")
        macro("QuoteVerdict", "collusion" if verdict == "punishment" else "learning bias")

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
    # Placeholders for numbers whose experiments have not finished yet, so the
    # paper always compiles; a missing number shows as "--".
    import re
    used = set()
    for f in (glob.glob(os.path.join(ROOT, "paper", "sections", "*.tex"))
              + glob.glob(os.path.join(ROOT, "paper", "table_*.tex"))):
        used |= set(re.findall(r"\\([A-Z][A-Za-z]+)", open(f).read()))
    for name in sorted(used - set(macros)):
        if name in {"Delta", "Large", "Big", "Longrightarrow", "Rightarrow", "Pr", "E"}:
            continue
        fh.write(f"\\providecommand{{\\{name}}}{{{'' if name.endswith('Sentence') else '--'}}}\n")
print(f"wrote {len(macros)} macros; figures: {sorted(os.listdir(FIG))}")
