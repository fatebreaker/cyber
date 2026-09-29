# Cross-Benchmark Generalization of LLM Security Agents

**Working title:** *One Skill or Many? Measuring Cross-Benchmark Generalization of
LLM Agents on Security Tasks*

## 1. Motivation

LLM agents are now evaluated on a growing set of security benchmarks —
CyberGym (vulnerability reproduction from OSS-Fuzz), Cybench / NYU-CTF
(capture-the-flag), CVE-Bench (real web-app exploitation), and patch-oriented
suites such as SWE-bench. Almost every result is produced with a *different
agent scaffold* on a *single* benchmark. As a result the field cannot answer a
basic question:

> When Model A beats Model B on CyberGym, is that because A has stronger
> **security reasoning**, or because A's scaffold happened to fit that
> benchmark's harness, prompt format, and tooling?

Without controlling the scaffold, benchmark scores confound three things:
(1) the model's underlying capability, (2) scaffold/harness fit, and
(3) contamination (the vulnerability appeared in pretraining data).

## 2. Research questions

- **RQ1 (Transfer).** Under a *single fixed scaffold*, do per-model scores
  correlate across benchmarks? Is there evidence of one latent
  "security-reasoning" capability, or are the axes independent?
- **RQ2 (Task difficulty transfer).** Do tasks that are hard for one model tend
  to be hard for all models (a shared difficulty axis), or is difficulty
  model-specific?
- **RQ3 (Contamination).** How much of measured performance is explained by the
  target vulnerability predating the model's training cutoff?
- **RQ4 (Failure modes).** Are the dominant failure modes shared across
  benchmarks, or benchmark-specific?

## 3. Contributions

1. **A unified evaluation harness** with a common `Task / Agent / Grader`
   interface that adapts CyberGym, Cybench/NYU-CTF, and CVE-Bench to one API.
   Reusable, open-sourced — a standalone artifact.
2. **A controlled cross-benchmark study**: one fixed ReAct-style scaffold run
   identically across all benchmarks and several API models.
3. **A transfer analysis**: rank-correlation matrix across benchmarks and a
   task-difficulty transfer analysis (RQ1, RQ2).
4. **A contamination-controlled slice**: tasks partitioned by training-cutoff
   date, with the resulting score gap reported (RQ3).
5. **A shared failure-mode taxonomy**, hand-labeled on a stratified sample
   (RQ4).

## 4. Method

### 4.1 Fixed scaffold

A single deliberately-simple ReAct agent (observe → think → act) with a small,
fixed tool set: shell/exec, file read, file write, and a `submit` action. The
*same* system prompt, tool schema, step budget, and context-management policy
are used on every benchmark. Simplicity is intentional: the claim is about
transfer under a controlled scaffold, not about maxing any single leaderboard.

### 4.2 Benchmarks (initial)

| Benchmark        | Task type                       | Grader signal                              |
|------------------|---------------------------------|--------------------------------------------|
| CyberGym         | Reproduce OSS-Fuzz vuln (PoC)   | PoC triggers pre-patch ∧ neutralized post-patch |
| Cybench / NYU-CTF| CTF challenge                   | Flag string match                          |
| CVE-Bench        | Exploit real web app in sandbox | Exploit-success oracle                     |

All run in isolated containers; **no network egress** from task environments
except what a benchmark explicitly requires.

### 4.3 Models

API models only (Claude, GPT, and one open-weights model served via API), all
driven through one thin client abstraction so the scaffold is byte-identical
across providers.

### 4.4 Analysis

- Per-benchmark success rate with bootstrap CIs.
- Spearman ρ of per-model scores across every benchmark pair (RQ1).
- Per-task solve-vector correlation / IRT-style difficulty estimate (RQ2).
- Contamination gap Δ = score(pre-cutoff) − score(post-cutoff) (RQ3).
- Taxonomy distribution over a stratified hand-labeled sample (RQ4).

## 5. Threats to validity

- **Grader reliability.** PoC-based graders can pass for the wrong reason; we
  add differential checks (correct crash signature) and audit a sample.
- **Scaffold bias.** A single scaffold may systematically disadvantage one
  benchmark; we report this as a limitation and include a scaffold-ablation on
  a subset.
- **Contamination is a spectrum.** Cutoff dates are coarse; we treat Δ as a
  lower bound on the contamination effect.

## 6. Ethics & scope

Strictly **defensive / evaluation** framing. All targets are existing public
benchmark artifacts (patched OSS-Fuzz vulns, CTF challenges, sandboxed CVE
apps). No new exploits against live third-party systems; no capability
uplift beyond reproducing already-public, already-patched issues in a sandbox.
Task environments run without outbound network access.

## 7. Milestones

1. Harness core + CyberGym adapter + one model end-to-end (smoke test).
2. Add Cybench + CVE-Bench adapters; fixed scaffold frozen.
3. Full sweep across models; collect trajectories.
4. Transfer + contamination analysis; taxonomy labeling.
5. Writeup. Target venue: USENIX Security / IEEE S&P / a top ML-security
   workshop (e.g. NeurIPS D&B track for the harness + dataset artifact).
