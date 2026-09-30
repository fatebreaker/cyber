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

## Next steps

1. Convergence: decaying alpha, on-path policy-change metric, save final policies.
2. Mechanism: impulse response. Force one learner to deviate once and trace
   whether the other punishes (the evidence Calvano et al. use for real collusion).
3. More I (3, 4) and sigma_u values; longer DQN and PPO runs with tuning.
4. Interventions: passive traders (avoid I = P + 1), disclosure noise, order
   cap, tick size, across all three algorithms.
