# Experiment notes

All runs: I = 2 learners, P = 0, sigma_v = sigma_u = 1, 5 values, 31 orders,
gamma = 0.95, market-maker half-life 2000, 20k evaluation periods of greedy
play. Delta = 0 is Nash, 1 is full collusion. ± is a 95% CI across sessions.

## exp1: first pass (Q: beta_decay 4e-6, 1.5M steps, 200 sessions)

| memory | Delta intensity | Delta info | Delta profit |
|---|---|---|---|
| none | 0.27 ± 0.04 | 0.28 ± 0.03 | 0.17 ± 0.08 |
| flow | 0.66 ± 0.02 | 0.70 ± 0.02 | 0.41 ± 0.04 |
| residual | 0.31 ± 0.02 | 0.68 ± 0.02 | -1.43 ± 0.05 |

`residual` was under-explored: its table is 5x larger than `flow`'s, and profit
below Nash with low informativeness means orders were reacting to noise.
Superseded by exp2.

## exp2: slower exploration (Q: beta_decay 1e-6, 6M steps, 200 sessions)

| memory | Delta intensity | Delta info | Delta profit | order R² | policy change (last 100k) |
|---|---|---|---|---|---|
| none (control) | 0.24 ± 0.04 | 0.26 ± 0.04 | 0.13 ± 0.06 | 0.98 | 0.75 |
| flow | 0.67 ± 0.02 | 0.69 ± 0.02 | 0.48 ± 0.03 | 0.96 | 0.44 |
| residual | 0.88 ± 0.01 | 0.95 ± 0.01 | 0.46 ± 0.03 | 0.95 | 0.46 |

Readings:
- Learners that can monitor rivals suppress trading far beyond the memoryless
  control. The gap between `none` and the memory conditions is the candidate
  strategic-collusion component. `none` itself sits at about 0.25, which is the
  learning-bias ("artificial stupidity") component.
- `flow` and `none` barely moved between exp1 and exp2, so those outcomes are
  robust to the exploration schedule. `residual` moved from 0.31 to 0.88, so it
  needed the extra exploration.
- Delta profit is smaller than Delta intensity because the Nash-to-collusive
  profit gap is only 6% at I = 2 and orders are not perfectly linear in v.
  Intensity and informativeness are the more reliable collusion measures here.

Open problem — convergence: 44-75% of greedy table entries still changed in the
last 100k steps. Outcomes are tight across 200 sessions and stable across
schedules, so the flips are likely among near-equivalent orders and in
off-path states, but that has to be shown. Next: decaying learning rate
(noisy rewards keep a constant-alpha table moving), and on-path, magnitude-
weighted change metrics.

## exp1: DQN (beta_decay 2e-5, 300k steps, 50 sessions, residual memory)

| Delta intensity | Delta info | Delta profit |
|---|---|---|
| -0.44 ± 0.08 | -0.23 ± 0.05 | -1.05 ± 0.18 |

DQN over-trades relative to Nash: more competitive than Nash, not collusive.
Preliminary only: 20x fewer steps than Q and not tuned. It is consistent with
collusion depending on the algorithm (Deng et al., 2024), which is the reason
to test every intervention across algorithms.

## exp3: punishment test and learning-rate schedule (Q, 6M steps, 200 sessions)

Punishment test: 40 paired deviation events per session. The deviator plays
its myopic best response for one period; rival d_beta is the change in the
rivals' trading intensity at later lags (positive = punishment).

| run | Delta intensity | Delta info | on-path order shift (grid steps, last 100k) | rival d_beta, lag 1 | deviator discounted gain (16 periods) |
|---|---|---|---|---|---|
| const alpha, residual (= exp2) | 0.88 ± 0.01 | 0.95 ± 0.01 | 1.39 | +0.001 ± 0.005 | +0.053 ± 0.005 |
| visits alpha, none | -0.60 ± 0.03 | -0.38 ± 0.02 | 0.81 | 0 (by construction) | +0.017 ± 0.002 |
| visits alpha, flow | -0.19 ± 0.03 | 0.03 ± 0.02 | 2.52 | +0.001 ± 0.005 | +0.047 ± 0.006 |
| visits alpha, residual | -0.50 ± 0.02 | -0.01 ± 0.02 | 4.74 | +0.002 ± 0.008 | +0.087 ± 0.007 |

(The const-alpha residual run reproduces exp2 exactly with the same seed.)

Findings:
1. **No punishment anywhere.** Rivals do not react to a deviation at any lag,
   and deviating pays in every condition. The near-collusive outcome in the
   const-alpha residual run (Delta 0.88) is therefore *not* sustained by
   trigger strategies. It is a supracompetitive outcome without enforcement,
   which fits Dou et al.'s "artificial stupidity" (learning-bias) channel
   rather than their "artificial intelligence" (price-trigger) channel.
2. **Outcomes flip with the learning-rate schedule.** With per-entry decaying
   step sizes, the same markets move from strong under-trading (Delta +0.24 to
   +0.88) to over-trading beyond Nash (Delta -0.19 to -0.60). Likely cause:
   step sizes shrink while the market maker's lambda is still low during
   heavy exploration (about 0.31 at 1M steps versus 0.47 Nash), so estimates
   freeze around best responses to a too-cheap market and over-trade.
3. **Neither schedule converges.** On-path greedy orders still move by 0.8 to
   4.7 grid steps over the last 100k steps. Every greedy entry is visited in
   20k evaluation periods, so on-path and all-entry change coincide here.
4. The monitoring conditions (flow, residual) differ from the memoryless
   control in level, but without punishment the difference cannot be read as
   strategic collusion. More states per value mean fewer visits per entry,
   which changes the size of the learning bias.

Model limitation found while interpreting this: in the Gaussian Kyle model
the detectability of a deviation is invariant to sigma_u. Orders scale with
sigma_u / sigma_v, so deviation size relative to noise depends only on
v / sigma_v. Noise volume therefore cannot move this market into an
easy-monitoring regime, and disclosure noise can only make monitoring worse.

## exp4: perfect monitoring (Q const alpha 0.15, beta_decay 4e-7, 15M steps, 100 sessions)

| run | memory | Delta intensity | Delta info | Delta profit | rival d_beta lag 1 | deviator gain |
|---|---|---|---|---|---|---|
| orders_s0 | orders (sees rival's exact order) | 0.82 ± 0.01 | 0.90 ± 0.02 | 0.38 ± 0.04 | +0.008 ± 0.011 | +0.060 ± 0.010 |
| orders_s1 | orders | 0.82 ± 0.01 | 0.89 ± 0.02 | 0.39 ± 0.04 | +0.008 ± 0.011 | +0.055 ± 0.011 |
| residual_s0 | residual | 0.90 ± 0.01 | 0.97 ± 0.01 | 0.54 ± 0.04 | +0.001 ± 0.006 | +0.058 ± 0.006 |
| none_s0 | none | 0.27 ± 0.06 | 0.28 ± 0.05 | 0.21 ± 0.10 | 0 | +0.026 ± 0.004 |

Even with perfect monitoring, rivals do not react to a deviation and
deviating pays. Monitoring is not what is missing: Q-learning does not find
punishment strategies in the standard Kyle market. This matches the
detectability result (a deviation is only (I-1)/(2I) noise sd per unit of v)
and Dou et al.'s own regime classification (over-pruning only at xi = 0).

## Previous next-steps list (superseded by the paper plan)

1. Decisive monitoring test: add a perfect-monitoring memory mode (traders see
   rivals' last orders exactly). If punishment still does not appear, Q-learning
   in this market does not find trigger strategies and the collusion here is a
   learning artifact. If it does, monitoring precision is the lever, which maps
   directly onto transparency regulation.
2. Get Dou, Goldstein & Ji's exact specification. They report price-trigger
   collusion, so their setup must include a feature that makes deviations
   detectable (value distribution, noise structure or state design).
3. Convergence: Calvano's criterion (greedy strategy unchanged for 100k
   periods) is not met under either schedule. Try longer runs, alpha decay
   that only starts after exploration has faded, and a final pure-exploitation
   phase.
4. Then: more I and algorithms (DQN, PPO), and the intervention sweep.

## exp5: myopic placebo 2x2 (Q const alpha 0.15, beta 1e-6, 6M steps, 200 sessions x 3 seeds)

| | no memory | residual memory |
|---|---|---|
| gamma 0.95 | 0.24 (Delta profit 0.17) | 0.87 (Delta profit 0.46) |
| gamma 0 (myopic) | 1.27 (Delta profit -0.03) | 1.24 (Delta profit -0.01) |

Myopic learners, which cannot collude, trade below the cartel (Delta > 1) with
competitive profits. Memory matters only for forward-looking learners, and the
deviation test still finds no punishment there. Open question: why memory
raises under-trading for gamma = 0.95. Candidate: state-space size (fewer
updates per entry). Test: memory="random" with 35 states in exp9.

## Single-trader mechanism (I = 1, lambda frozen, no rival)

- Step size (gamma 0): learned/optimal 0.87, 0.81, 0.71, 0.57, 0.43 for alpha
  0.02-0.4; shortfall = 0.91 sqrt(alpha), R^2 0.994. Counterfactual updates:
  1.00-1.01 at every alpha.
- Discount factor (alpha 0.15): 0.64, 0.73, 0.82, 0.89 for gamma 0, 0.5, 0.8,
  0.95. Continuation-value noise is action-independent and dilutes the
  size-dependent payoff noise behind the pruning.
- Irrelevant random states (gamma 0.95): 0.89, 0.84, 0.91, 0.98 for 1, 7, 35,
  155 states. Inconclusive: with lambda frozen the Q initialisation is exactly
  the true expected profit, and with many states most entries stay near it in a
  300k-period run. Not used; the market version (exp9 random35) is the test.

## exp7: Dou et al. calibration, separate Q-tables (sigma_u 0.1, alpha 0.05, bracket grid, price state, 15M steps, 100 sessions)

| xi | learners | Delta intensity | Delta profit | shock response (1 dev, % beta^N) | rival reaction |
|---|---|---|---|---|---|
| 0 | gamma 0.95, price | 0.48 | 0.59 | +0.5 ± 0.6 | none |
| 0 | gamma 0 (myopic) | 0.63 | 0.74 | +0.3 ± 0.5 | none |
| 0 | gamma 0.95, no memory | 0.37 | 0.50 | 0 | 0 |
| 500 | gamma 0.95, price | 0.31 | 0.45 | -0.6 ± 0.5 | none |
| 500 | gamma 0 (myopic) | 0.11 | 0.18 | 0.0 ± 0.3 | none |
| 500 | gamma 0.95, no memory | 0.24 | 0.36 | 0 | 0 |

xi = 500 separate-table Delta 0.31 matches Esquinas Coves's 0.31. Caveat found
later: the default (noise-unit) price binning saturates at xi = 500, so these
learners saw an effectively coarse price state; exp11 reruns with grid binning.

## exp9: interventions (standard Kyle, residual baseline Delta 0.87)

| treatment | Delta intensity |
|---|---|
| reduced transparency (disclosure noise 2 sigma_u) | 0.90 |
| uninformative random memory (35 states) | 0.84 |
| uninformative random memory, myopic | 1.16 |
| counterfactual updates, residual | -0.10 |
| counterfactual updates, no memory | -0.09 |
| two passive Nash traders | aggregate 0.48 vs Nash 1.00 and cartel 1.41 (cartel above Nash), profit 30% below Nash |

## exp10: shared Q-tables (Dou calibration, noise-unit price bins)

Delta intensity: xi 0: 0.68 (gamma 0.95), 0.86 (myopic); xi 500: 0.71, 0.86.
Myopic shared learner at xi 500 responds to noise shocks with a threshold
(0.00, +0.75, +3.34 % of beta^N at 0.05, 0.25, 1 deviation units); the
forward-looking one does not. Rare-state check: greedy play visits only the
two outer price bins; interior bins keep Nash-like initial orders; large
shocks land there. The trigger-like response is an off-path artifact.

## exp8: deep RL (residual memory, 400k steps, 50 sessions)

DQN Delta -0.36 (myopic -0.17); PPO -0.02 (myopic -0.28). No punishment.

## exp6: step size in the market (gamma 0.95)

residual: 0.19, 0.86, 1.12 at alpha 0.05, 0.15, 0.3; no memory: -0.03, 0.24,
0.51. No punishment at any step size.

## exp11/exp12: xi = 500 with grid-range price state (Dou-style binning), 2 seeds for key cells

Noise-unit price binning saturates at xi = 500 (greedy play visits only the
two outer bins), so the main xi = 500 results use bins over the price range
the order grid can produce.

| learners | Delta intensity | shock response at 0.05 / 0.25 / 1 dev (% beta^N) | rival reaction (% beta^N) |
|---|---|---|---|
| separate, gamma 0.95 (2 seeds) | 0.48 | ~0 | -0.5 ± 0.6 |
| separate, gamma 0 | 0.13 | +0.6 ± 0.4 at 1 dev | +0.5 ± 0.5 |
| shared, gamma 0.95 (2 seeds) | 0.62 | 0.1 / 0.1 / -0.3 (n.s.) | +0.4 ± 0.6 |
| shared, gamma 0 (2 seeds) | 0.71 | 0.30 / 1.04 / 4.01 | +2.93 ± 0.17 |

The myopic shared learner shows both "punishment" signatures; deviating still
pays. Rare-state check (grid binning): intensity 0.30 in common states, 0.35
in rare, 0.47 in never-visited (0 = cartel, 1 = Nash): uneven training across
states produces the reactions.

## Validation: Calvano et al. (2020) logit Bertrand (results/bertrand)

100 sessions, 2.5e6 periods, Calvano baseline parameters. Benchmarks
reproduce p^N = 1.473, p^M = 1.925.

| variant | Delta (profit) | rival price at lag 1 | deviator gain | verdict |
|---|---|---|---|---|
| baseline (memory 1, gamma 0.95) | 0.86 | -0.24 | -0.19 | punishment |
| myopic | 0.22 | ~0 | ~0 | none |
| no memory | 0.95 | 0 | +0.055 | none (spontaneous coupling) |
| uninformative memory | 0.05 | 0 | +0.009 | none |
| noisy profits | 0.79 | -0.20 | -0.24 | punishment |
| noisy profits, myopic | 0.03 | ~0 | ~0 | none |
| counterfactual updates | 0.33 | -0.11 | -0.04 | punishment |

## Dealers under adverse selection (results/quotes)

Two Q-learning dealers quote asks; informed buyers (pi = 0.3) buy at v = +0.5,
liquidity buyers have w ~ U[0,1]. a^N = 0.10 (zero profit), a^M = 0.61.

| variant | Delta best ask | Delta profit | punishment |
|---|---|---|---|
| baseline | 0.64 | 0.84 | no (undercutting pays) |
| myopic | 0.84 | 0.97 | no |
| no memory | 0.65 | 0.86 | no |
| uninformative memory | 0.74 | 0.92 | no |
| counterfactual | 0.19 | 0.30 | no |
| counterfactual, no memory | 0.17 | 0.28 | no |

## Sustainability bounds (results/theory/sustain.json)

xi = 0: Nash reversion (grim or one period) sustains no collusion for
delta <= 0.99; the any-punishment necessary condition allows full collusion
at delta = 0.95. xi = 500: grim Nash reversion sustains full collusion for
delta >= 0.8; one-period reversion at most Delta 0.43 (0.44 as delta -> 1).

## Three traders (exp14, numba engine except counterfactual)

residual gamma 0.95: Delta 0.73, no reaction, deviating pays; myopic 1.02;
no memory 0.25; counterfactual -0.12.

## Second seeds (exp13)

All second-seed replications agree with seed 0 to within a few hundredths;
pooled numbers in the paper. Runs marked "engine": "numba" in their JSON use
the compiled engine.

## Dou-scale runs (exp15, 2e8 periods, numba engine, xi = 500, grid price bins)

| learners | Delta intensity | shock 1 dev (% beta^N) | rival reaction (% beta^N) |
|---|---|---|---|
| separate, gamma 0.95 | 0.33 | 0.16 ± 0.40 | -0.31 ± 0.54 |
| separate, gamma 0 | 0.13 | 0.45 ± 0.23 | 0.18 ± 0.30 |
| shared, gamma 0.95 | 0.76 | -0.03 ± 0.37 | 0.01 ± 0.39 |
| shared, gamma 0 | 0.85 | 3.64 ± 0.20 | 2.35 ± 0.16 |

Separate-table index matches Esquinas Coves's 0.31 at 5e8. Diagnostics
unchanged from 1.5e7 periods. On-path greedy entries still change (~0.9
share over the last 1e7 periods) with constant step size.

## Faithful Dou et al. protocol (exp16, 4e8 periods, numba)

alpha = 0.01, value-specific exploration beta = 5e-7, common 31-point price
grid (price_bins = "dou"), xi = 500; our EWMA market maker (theirs: rolling
OLS, T_m = 10,000). Resumed from 3.2e8 checkpoints after a container restart.

| learners | Delta profit | Delta intensity | shock 0.05 / 0.25 / 1 dev (% beta^N) | rival reaction |
|---|---|---|---|---|
| price, gamma 0.95, sigma_u 0.1 | 0.29 | 0.18 | 0.04 / -0.04 / 1.93 ± 0.30 | 0.23 ± 0.19 |
| price, gamma 0 | 0.12 | 0.07 | 0.04 / -0.08 / 2.22 ± 0.26 | -0.04 ± 0.10 |
| lagged value only, gamma 0.95 | 0.24 | 0.14 | n/a | 0 |
| price, gamma 0.95, sigma_u 100 | 0.37 | 0.24 | 0 / 0 / 0 | 0 |

Deviating pays in every condition. Dou et al. report Delta_C ~ 0.75 here,
collusion -> 0 without the lagged price, and trigger responses at 2.5-15%
shocks; we reproduce none of these. The 40% shock response is shared by the
myopic placebo.

## Per-session classification with Dou et al.'s rule (results/per_session)

Faithful protocol, 4e8 periods, 100 sessions, 200 paired replays per session.
Rule (their OA 4.5): price-trigger if both traders' orders rise significantly
one period after a shock moving the price by 1.2%.

| learner | price move 0.12% / 1.2% / 5.5% / 7.2%: share classified trigger | share flat |
|---|---|---|
| gamma 0.95 | 0 / 0 / 0 / 0 % | 100 / 86 / 74 / 63 % |
| gamma 0 (myopic) | 0 / 1 / 6 / 5 % | 100 / 80 / 65 / 68 % |

Medium-shock session responses: IQR [-0.08, 0.10]% of the mean order.
Their alpha/beta grid (OA Fig. IA.9): baseline cell 0.7, three of four
neighbours 0.3; our faithful Delta_C 0.29.
