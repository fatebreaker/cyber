# Literature claims to verify against the original papers

The PDFs of the cited papers could not be fetched from this environment
(publisher, arXiv, NBER and SSRN hosts are blocked by the network policy).
Claims below come from search-result summaries or from the public
reimplementation of Dou et al. (Esquinas Coves 2026), not from the papers.
Each must be checked against the original before submission.

Status: [ ] unverified, [x] verified against the paper, [!] needs a change.

## Dou, Goldstein & Ji (2025), NBER w34054 — checked against the PDF (uploaded 2026-10-01)

- [x] Model: I informed speculators, information-insensitive investors, market
      maker trading off pricing error and inventory with weight theta (Sec. 3).
- [x] Calibration: I = 2, xi = 500, theta = 0.1, rho = 0.95, sigma_u = 0.1 (low)
      and 100 (high); n_v = 10 (equiprobable normal quantiles), n_x = 15 on
      the cartel-to-Nash bracket +-iota, iota = 0.1, n_p = 31 (Sec. 4.2).
- [!] Learning: alpha = 0.01, beta = 5e-7 with VALUE-SPECIFIC counters,
      eps = exp(-beta t(v)). Our main replication used alpha = 0.05 (from
      Esquinas) and calendar-time exploration. FIXED in text; faithful runs
      (exp16) use alpha = 0.01, value counters, their common price grid.
- [x] State (p_{t-1}, v_{t-1}, v_t); separate Q-matrices per speculator.
- [!] Price grid: one common grid over [p_L - iota span, p_H + iota span],
      p_H/L = lambda^N I max/min{x^M, x^N} +- 1.96 sigma_u. Our "grid" binning
      is per lagged value. Added price_bins = "dou" (exact) for exp16.
- [!] Market maker: rolling-window OLS over T_m = 10,000 periods, estimating
      both the z-demand slope and E[v|y] (eq. 4.1-4.2). Ours: EWMA moments,
      half-life 2,000, xi known. Disclosed in limitations.
- [x] Q init: payoff vs uniform rivals, zero noise, lambda^N (Sec. 4.2).
- [x] 1,000 sessions; convergence = greedy strategies unchanged for 1e6
      periods; 2e7 to 5e10 periods.
- [x] Channel names: "artificial intelligence" (price trigger) and "artificial
      stupidity" (over-pruning); mechanism of over-pruning = asymmetric
      exploitation after adverse vs beneficial noise shocks (Sec. 5.1).
- [!] Regimes: (i) high xi & low sigma_u -> price trigger; (ii) high xi & high
      sigma_u -> over-pruning; (iii) low xi (xi = 5) -> over-pruning.
      Our earlier wording ("over-pruning only at xi = 0") was wrong. FIXED.
- [x] Noise-shock test (Sec. 5.3, Fig. 3): shocks of 0.25, 2.5, 11.5, 15% of
      average |x_i|; no response to small, similar aggressive response to
      larger shocks, punishment ~2 periods.
- [x] Deviation test (Fig. 5): at xi = 500, sigma_u = 0.1 both speculators trade
      aggressively at t = 4; at high sigma_u and at xi = 5 the rival does not
      react.
- [x] Removing p_{t-1} from the state drops Delta_C to zero at xi = 500,
      sigma_u = 0.1 (Sec. 5.3). Tested in exp16: we get 0.29 -> 0.24, not 0.
- [x] Theory: price-trigger equilibria impossible with high sigma_u or low xi
      (Prop. 3.1). Our sustainability section now credits this.
- [x] Their collusion index Delta_C is profit-based (normalized trading
      profitability). Our Dou-replication tables report intensity; profit
      index to be shown alongside in the exp16 results.
- [x] Benchmarks at sigma_u = 0.1, xi = 500: our code gives chi^N = 166.667,
      chi^M = 125, lambda ~ 0.002 (consistent with their formulas; their
      paper computes benchmarks with the discretized sigma_v-hat = 0.938).

## Esquinas Coves (2026), GitHub report — read directly (LaTeX source)

- [x] Delta_chi: separate 0.720, sequential 0.919, averaged 0.902 at xi = 0;
      0.309 / 0.866 / 0.865 at xi = 500; five seeds at xi = 500 separate
      0.307-0.328; T = 5e8.
- [x] Price-trigger signature sharper under shared tables at xi = 500.

## Others

- [x] Calvano et al. (2020, AER 110(10):3267-3297): Q-learning Bertrand,
      punishment shown by impulse response to a one-period deviation to the
      static best response (>95% of cases unprofitable), gradual return; Q init
      = discounted payoff vs uniform rivals (eq. 8); alpha = 0.15, beta = 4e-6
      is their highlighted point. Verified from the AER PDF.
- [ ] Calvano et al. (2023, IJIO) "Genuine or spurious?": role of exploration.
- [ ] Klein (2021, RAND): sequential pricing, similar results.
- [ ] Asker, Fershtman & Pakes (2022 AEA P&P; 2024 JEMS): asynchronous ->
      near-monopoly, synchronous/counterfactual -> competitive.
- [ ] Abada & Lambin (2023, MS): wording now limited to "quickly reach seemingly
      collusive outcomes; regulator can restore competition by enforcing
      decentralised learning or intervening in learning".
- [x] Banchio & Mantegazza: collusion via spontaneous coupling, not punishment.
- [~] den Boer, Meylahn & Schinkel: published in Management Science, 2026
      (OpenAlex). Volume/pages and the content claim still unchecked.
- [ ] Colliard, Foucault & Lovo (RFS, forthcoming?): Q-learning market makers,
      mark-ups from limited experimentation and noisy feedback. Check status.
- [ ] Cartea, Chang & Penalva (2022): tick size bounds excess rents.
- [ ] Cont & Xiong (2024, Math Finance): tacit collusion of market makers.
- [x] Deng, Schiffer & Bichler (2024, arXiv:2406.02437): collusion depends on
      algorithm; TQL more collusive than DRL; PPO least.
- [x] Fish, Gonczarowski & Shorrer (arXiv:2404.00806v6, 2026): LLM pricing
      agents reach supracompetitive prices.
- [ ] Thrun & Schwartz (1993), van Hasselt (2010): max-operator over-estimation.
- [ ] Even-Dar & Mansour (2003): learning rates for Q-learning.
- [ ] All bibliographic details (volumes, pages, years) in refs.bib.

## Added with the validation, theory and dealer sections

- [x] Calvano et al. (2020) baseline: a_i = 2, a_0 = 0, mu = 1/4, c = 1, m = 15,
      xi = 0.1 grid extension, alpha = 0.15, beta = 4e-6, delta = 0.95, memory
      one; Nash price ~1.473 and monopoly ~1.925 (our code reproduces these
      numbers); Delta ~0.85 at baseline; impulse response shows punishment
      followed by gradual return.
- [x] Banchio & Mantegazza (arXiv:2202.05946v5, 2023): "spontaneous coupling",
      collusion without reward-punishment among memoryless eps-greedy
      Q-learners; also explains AFP's asynchronous vs synchronous result.
      Bib entry switched to the arXiv version actually read.
- [ ] Green & Porter (1984, Econometrica 52(1):87-100): trigger strategies
      under imperfect monitoring with price wars on the equilibrium path.
- [ ] Abreu, Pearce & Stacchetti (1990, Econometrica 58(5):1041-1063).
- [ ] Glosten & Milgrom (1985, JFE 14(1):71-100): zero-profit competitive quote.
- [ ] Commission Delegated Regulation (EU) 2017/589 (RTS 6): investment firms
      must test algorithms before deployment (check article and wording:
      testing environments / conformance testing).
- [ ] Colliard, Foucault & Lovo: our dealer market is "stylised", not their
      model; check that the description of their findings matches the paper.
- [ ] Kushner & Yin (2003) / Borkar (2008): constant-step SA iterates
      concentrate within O(sqrt(alpha)) of the ODE equilibrium (check the
      exact theorem and its conditions, e.g. Kushner-Yin ch. 10, Borkar ch. 9).

## Finding from verification (2026-10-01)

Calvano et al.'s "modest profit gains" for memoryless algorithms use delta = 0,
alpha = 0.25, beta = 1e-4 (online appendix A4.1). We reproduce Delta = 0.16
with that spec; the same spec with delta = 0.95 gives 0.93. Added to the
validation section and table.

## Bibliographic metadata checked against Crossref (2026-10-01)

- [x] Green & Porter 1984, Econometrica 52(1):87-100
- [x] Abreu, Pearce & Stacchetti 1990, Econometrica 58(5):1041-1063
- [x] Glosten & Milgrom 1985, JFE 14(1):71-100
- [x] Klein 2021, RAND 52(3):538-558
- [x] Abada & Lambin 2023, Management Science 69(9):5042-5065 (pages added)
- [x] Calvano et al. 2023, IJIO 90:102973 (article number added)
- [x] Asker, Fershtman & Pakes 2024, JEMS 33(2):276-304 (issue added)
- [x] Cont & Xiong 2024, Mathematical Finance 34(2):467-521 (added)
- [x] den Boer, Meylahn & Schinkel, Management Science, online 2026-06-09,
      doi 10.1287/mnsc.2024.08557 (no volume yet)

Metadata only: the content claims for these papers (and for Dou et al.,
Colliard-Foucault-Lovo, Cartea et al., Asker et al. 2022) still need the
full texts, which are paywalled or on SSRN (blocks automated access).
