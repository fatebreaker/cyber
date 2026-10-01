# Literature claims to verify against the original papers

The PDFs of the cited papers could not be fetched from this environment
(publisher, arXiv, NBER and SSRN hosts are blocked by the network policy).
Claims below come from search-result summaries or from the public
reimplementation of Dou et al. (Esquinas Coves 2026), not from the papers.
Each must be checked against the original before submission.

Status: [ ] unverified, [x] verified against the paper, [!] needs a change.

## Dou, Goldstein & Ji (2025), NBER w34054 — critical

- [ ] Model: multiple informed speculators, information-insensitive investors
      z = -xi (p - v_bar), market maker minimising theta (p - E[v|y])^2 + (y+z)^2
      (model.tex Sec 3.1; eq. 1).
- [ ] Benchmarks at sigma_u = 0.1, theta = 0.1, xi = 500, I = 2:
      chi^N ~ 166.667, chi^M = 125, lambda^N ~ 0.002 (tests, appendix).
- [ ] Q-learning protocol: state (p_{t-1}, v_{t-1}, v_t); 10 values; 15 orders
      per value on the cartel-to-Nash bracket +-10%; 31 price bins per lagged
      value; alpha = 0.05; rho = 0.95; beta = 5e-6 with value-specific exploration
      counters; Q initialised to payoff against uniform rivals (method.tex,
      results_dou.tex).
- [ ] Separate Q-tables per speculator is their specification (results_dou.tex).
- [ ] Two channels named "price-trigger" (artificial intelligence) and
      "over-pruning" / "homogenised learning biases" (artificial stupidity)
      (intro.tex, related.tex).
- [ ] Noise-shock impulse response is their test, Section 5.3, shock sizes as %
      of E|x| (method.tex D2).
- [ ] Their classification: over-pruning only at xi = 0 / low sigma_u (their
      "case iii"); price triggers when information-insensitive investors are
      present (model.tex Sec 3.3, results_kyle.tex, related.tex).
- [ ] Training horizons 2e7 to 5e10 periods; 1,000 sessions; convergence
      criterion (discussion_body.tex limitations).
- [ ] Does their market maker learn lambda or use the equilibrium value?
      (our market maker learns; stated as a difference in limitations).

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
