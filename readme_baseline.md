# README — Experimental Protocol & Apparatus
## Exception-Aware Distributed Event Systems Under Delayed Reconciliation

> **Purpose of this document**  
> This README defines the *experimental stage*, *instrumentation*, *unknowns*, and *constraints* for all experiments in this project.  
>
> It intentionally **does not contain results, interpretations, or conclusions**.  
> Its sole function is to make the experiments *rigorous, bounded, and defensible* under critical peer review.

---

## 1. Scientific Posture

This project adopts a **systems-science posture**, not a theory-first or framework-proposal posture.

The experiments are designed under the following principles:

- Distributed systems are evaluated **under uncertainty**, not after reconciliation.
- Conflicts between observations are treated as **normal system state**, not anomalies.
- Delays are treated as **structural properties**, not tuning artifacts.
- Decisions are evaluated by **measured outcomes**, not internal confidence alone.

No claim is made without a corresponding measurement.

### Scope Note (Domain-Agnostic by Role, Not by Business Semantics)

This suite is **domain-agnostic by role** for systems where:

- Decisions are made under **partial, delayed, and potentially conflicting evidence**
- There exists a **late truth / adjudication signal** (modeled as `ReconciliationSignal`) that can label outcomes for evaluation

This is not a claim of “domain universality” for domains without an evaluable reconciliation/adjudication signal.

### Pipeline Positioning (Where the Thesis Lives)

These experiments target a specific cog in a larger distributed-system pipeline: the **pre-commit decision layer** that sits between **Signals/Evidence** and an **irreversible Command**. The suite measures what happens **before reconciliation collapses uncertainty**, while treating downstream consensus/ledger/state-machine machinery as standard infrastructure (see Appendix D for the full pipeline framing).

---

## 2. Core Unknowns (What Must Be Measured)

The experiments are structured around unknowns that cannot be resolved analytically.

### U1 — Decision correctness under conflict
- How state representations behave when multiple sources disagree.
- How delayed reconciliation affects downstream decisions.
- How different semantics alter observable outcomes.

### U2 — Timing of action under uncertainty
- How uncertainty evolves over time given partial evidence.
- How delay interacts with cost.
- How decision timing policies differ in observable behavior.

### U3 — Stability under non-stationary cost regimes
- How systems behave when cost changes non-linearly.
- How policies respond to abrupt external shocks.
- Whether degradation is gradual or catastrophic.

### U4 — State representation overhead (“conflict budget”)
- Memory overhead of preserving conflicts as sets/structures rather than scalars.
- Compute overhead (update, query, decision) as disagreement grows.
- Regimes where overhead becomes prohibitive; characterize a practical conflict budget.

### U5 — Formal decision boundary under delayed reconciliation
- Conditions under which WAIT is provably better than ACT given observable quantities.
- Whether threshold rules exist based on conflict measures (e.g., entropy), delay distributions, and cost asymmetry.

### U6 — Failure modes & impossibility boundaries
- Whether overwrite semantics admits unbounded/catastrophic cost amplification under specific shock patterns.
- Whether bounded regret is impossible under certain observability/delay conditions without conflict preservation.

These unknowns define the experiments. Anything not tied to them is out of scope.

---

## 3. Experimental Philosophy

To avoid hand-calibrated or self-confirming experiments, the apparatus enforces:

- **Explicit semantics**  
  All objects (events, decisions, reconciliation signals) are schema-defined.

- **Artifact persistence**  
  Intermediate and final outputs are materialized and versioned.

- **Comparative baselines**  
  Every experiment includes multiple system semantics evaluated under identical workloads.

- **External independence**  
  At least one experiment incorporates externally produced data.

- **Bounded inference**  
  Claims are restricted to the regimes explicitly tested.

---

## 4. Experimental Stage (Infrastructure Overview)

### 4.1 Mandatory Infrastructure

These components exist to enforce rigor and reproducibility.

- Configuration system for parameterized runs
- Deterministic randomization for controlled stochastic regimes
- Schema validation for all core objects
- Persistent artifact storage for all runs
- Reproducible CLI-based execution
- Stable figure generation from saved artifacts

None of these components define system semantics; they only ensure honest measurement.

---

### 4.2 External Sophistication (Bounded)

Optional components may be activated to increase realism without expanding scope.

Examples of realism axes:

- Event transport substrate (e.g., log-based replay)
- Durable late-truth source (e.g., database-backed reconciliation)
- Observability instrumentation (e.g., latency and causal tracing)
- External exogenous signal (e.g., time-series shock input)

At most two realism axes are active in any experiment.

---

## 5. Canonical Experimental Objects

All experiments operate over the same immutable object types.

### Event
- Entity identifier (domain-neutral “thing being acted upon”)
- Source identifier
- Event time
- Receipt time
- Observation payload
- Immutable identity

### DecisionRecord
- Decision timestamp
- Action identifier
- Explicit evidence set reference
- Confidence estimate
- Expected cost
- Policy identifier

### ReconciliationSignal
- Entity identifier
- Truth window
- Authoritative outcome
- Arrival timestamp

Decisions reference **evidence sets**, not single values.

---

## 6. Systems Under Test

Each experiment evaluates the same workload under multiple semantics.

### Baseline A — Overwrite semantics
- Single mutable state per entity
- Conflicts collapse implicitly

### Baseline B — Eventual consistency semantics
- Last-writer-wins resolution by receipt time
- Conflicts resolved implicitly over time

### Proposed — Exception-aware semantics
- Conflicts preserved as first-class state
- Duplicate, missing, and forked observations explicitly represented

No baseline is treated as a strawman.

---

## 7. Experiment 1 — Conflict & Delay Correctness

### Purpose
Evaluate decision correctness when conflicts and delays are present.

### Controlled Variables
- Conflict rate between sources
- Delay distributions
- Missing observation probability

### Fixed Elements
- Workload
- Decision trigger logic
- Cost definition

### Measurements
- Decision correctness relative to reconciliation
- Time to reconciliation
- Explanation completeness

---

## 8. Experiment 2 — Cost-Aware Decision Policies

### Purpose
Evaluate how different timing policies behave under uncertainty.

### Controlled Variables
- Decision policy
- Delay cost curvature

### Fixed Elements
- Evidence stream
- State semantics

### Measurements
- Total incurred cost
- Tail cost behavior
- Induced decision delay

---

## 9. Experiment 3 — Exogenous Shock Stress Test

### Purpose
Evaluate policy stability under non-stationary cost regimes.

This experiment is also the primary place to surface **catastrophic failure modes** (unbounded or practically unbounded amplification) if they exist.

### External Dependency
- One externally produced time series used solely as a shock signal.

### Measurements
- Cost amplification during shock windows
- Policy oscillation or instability
- Sensitivity to volatility
- Evidence of bounded vs unbounded amplification under declared shock families (if observed, reported with regimes and assumptions)

---

## 9.1 Experiment 4 — State Overhead & Conflict Budget (Representation Cost)

### Purpose
Quantify the memory and compute overhead introduced by conflict-preserving state representations, and characterize a practical conflict budget.

### Controlled Variables
- Conflict size/entropy regimes (synthetic or workload-induced)
- Entity cardinality and event rate
- State semantics (Baseline A/B vs Proposed)

### Fixed Elements
- Evidence stream family (declared generator)
- Artifact schema and measurement tooling

### Measurements
- M7 State overhead (memory)
- M8 State overhead (compute)
- M9 Conflict budget

---

## 10. Explicit Non-Claims

This work does **not** claim:

- Domain universality
- Optimality beyond tested regimes
- Adversarial robustness
- Replacement of existing DS abstractions

---

## 11. Reproducibility Contract

Every experiment run records:

- Configuration parameters
- Random seed
- Code version
- Artifact paths
- Execution timestamp

Figures are generated only from saved artifacts.

---

## 12. Review Readiness Checklist

This document ensures reviewers can identify:

- What was measured
- How it was measured
- Under which assumptions
- Within which regimes
- With which limitations

No claim is made without an associated artifact.

---

## 13. Threats to Validity (Pre-Registered)

This section enumerates *anticipated threats* prior to observing results. These are **not post-hoc limitations**; they are design constraints acknowledged in advance.

### 13.1 Internal Validity
- Instrumentation bias introduced by synthetic injectors
- Dependence on modeled delay and conflict distributions
- Sensitivity to random seed selection

Mitigation approach:
- Fixed seeds recorded per run
- Distribution families declared explicitly
- Comparative evaluation across identical workloads

### 13.2 External Validity
- Restricted domain of entity-like identifiers (a “thing” with repeated observations and actions)
- Simplified source independence assumptions
- Limited classes of reconciliation signals

Mitigation approach:
- Explicit scope bounding in claims
- External data used only as stress input, not validation
- No cross-domain generalization asserted

### 13.3 Construct Validity
- Definitions of "correctness" tied to reconciliation signal
- Definitions of "cost" tied to specified loss functions

Mitigation approach:
- Formal object schemas
- Artifact-backed metric computation
- No proxy metrics without definition

---

## 14. Appendix A — Experiment Contracts (Pre-Execution)

This appendix specifies **formal experiment contracts**. These define *what is run*, *what varies*, and *what is observed* — not what is concluded.

### A.1 Experiment 1 — Conflict & Delay Correctness

**Purpose**
- Characterize decision outcomes under conflicting, delayed observations

**Shared Process**
- Uses the canonical event model
- Uses identical workload and injectors across systems
- Produces identical artifact types

**Varied Inputs**
- Conflict rates
- Delay distributions
- Missing observation probabilities

**Fixed Elements**
- Decision trigger definition
- Loss definition
- Reconciliation semantics

**Recorded Outputs**
- Decision artifacts
- Reconciliation artifacts
- Metric summaries

---

### A.2 Experiment 2 — Cost-Aware Decision Policies

**Purpose**
- Characterize the impact of decision timing policies under uncertainty

**Linkage to Experiment 1**
- Reuses identical evidence streams
- Reuses identical state semantics

**Varied Inputs**
- Policy definitions
- Delay cost curvature

**Fixed Elements**
- Evidence arrival process
- State representation

**Recorded Outputs**
- Cost aggregates
- Tail behavior metrics
- Policy timing traces

---

### A.3 Experiment 3 — Exogenous Shock Stress Test

**Purpose**
- Characterize policy behavior under non-stationary cost regimes

**Linkage to Experiment 2**
- Reuses policy implementations
- Reuses decision artifacts

**Additional Inputs**
- External time-series shock signal

**Recorded Outputs**
- Shock-window cost metrics
- Policy stability indicators

---

## 15. Appendix B — Dependency Justification (Measurement Role)

Dependencies are included **only** where they enforce rigor or realism.

### Core Measurement Dependencies
- Numerical computation: deterministic stochastic regimes
- Dataframes: trace alignment and episode aggregation
- Columnar storage: immutable experimental artifacts
- Configuration system: parameterized and sweepable runs
- Schema validation: semantic integrity
- CLI execution: reproducibility
- Plotting: artifact-derived figures

### Optional Realism Dependencies
- Event transport substrate: replay realism
- Durable store / CDC: late truth realism
- Observability tooling: latency and causal measurement

No dependency defines correctness semantics.

---

## 16. Appendix C — Reviewer Attack Matrix (Preemptive)

This matrix enumerates *anticipated reviewer critiques* and the corresponding experimental design feature that addresses them.

| Reviewer Claim | Apparatus Response |
|--------------|-------------------|
| Results are hand-tuned | Config-driven runs, fixed seeds, persisted artifacts |
| Baselines are weak | Multiple real-world semantic baselines |
| Claims are over-generalized | Explicit non-claims and bounded regimes |
| Metrics are subjective | Formal definitions and schema-backed computation |
| Experiments are toy | External data stress and optional real substrates |

---

## 17. Protocol Addendum — Pre-Registered Definitions & Analysis Commitments

This addendum is **pre-execution**. It makes key definitions and analysis choices explicit so outcomes cannot be redefined after results are observed.

### 17.1 Operational Definitions

- **Correctness**: A `DecisionRecord` is correct iff its selected action matches the authoritative outcome in the first `ReconciliationSignal` that covers the decision’s declared truth window, under the experiment’s reconciliation semantics.
- **Decision time**: The timestamp at which the system emits a `DecisionRecord` (not the event time of any evidence item).
- **Delay**: Always specify which delay is being measured:
  - evidence delay: event time → receipt time
  - reconciliation delay: decision time → reconciliation arrival time
  - truth delay: decision time → reconciliation truth-window coverage
- **Conflict**: Two or more observations in the same evidence window that are not mutually consistent under the declared observation schema.
- **Conflict size**: The number of mutually inconsistent observations simultaneously represented for an entity at a decision point (implementation-specific, but must be counted consistently).
- **Conflict entropy (normalized)**: For a decision point with candidate outcomes \(\{o_i\}\) and implied belief weights \(\{p_i\}\), \(H = -\sum_i p_i \log p_i\), optionally normalized by \(\log k\) where \(k\) is the number of candidates. If weights are not available, use a declared proxy (e.g., uniform over candidates).
- **Explanation completeness**: The fraction of decision-relevant evidence items (per the policy’s admissibility rules) that are referenced by the decision’s evidence-set pointer and can be retrieved from persisted artifacts.

### 17.2 Pre-Registered Metrics (Artifact-Computable)

- **M1 Decision correctness rate**: correct decisions / total decisions, per configuration and overall.
- **M2 Time-to-reconciliation**: distribution of reconciliation arrival times relative to decision time.
- **M3 Regret / excess cost**: observed cost(policy) − observed cost(best baseline), per episode.
- **M4 Tail risk**: 95th/99th percentile episode cost and worst-k episodes.
- **M5 Deferral rate**: fraction of opportunities where policy outputs WAIT/DEFER vs ACT.
- **M6 Explanation completeness**: as defined above.
- **M7 State overhead (memory)**: bytes per entity and bytes per decision point attributable to state representation (including conflict sets/structures).
- **M8 State overhead (compute)**: per-event update time and per-decision query time as functions of conflict size/entropy.
- **M9 Conflict budget**: the maximum conflict size/entropy such that (a) update+query latency remains below a declared threshold and (b) memory per entity remains below a declared threshold, reported per configuration.

### 17.3 Baseline Fairness & Comparability Contract

- Same workload generator, seeds, evidence streams, reconciliation signals, and cost functions across all systems.
- Same decision opportunities (systems are evaluated on identical decision points).
- No system receives privileged access to reconciliation signals (late truth is always late).
- If a system uses an additional signal class, it must be declared as an experimental factor and/or made available to all systems.

### 17.4 Analysis Plan (Bounded)

- **Primary comparisons**: Proposed vs Baseline A and Baseline B on M1 and M3 using matched seeds.
- **Stratification**: do not collapse regimes without also reporting per-configuration results (conflict/delay/missingness buckets).
- **Uncertainty**: confidence intervals via bootstrap over episodes/runs (unit = episode/run), not over individual events.
- **Multiple comparisons**: if sweeping many configurations, control false discovery rate (FDR) or avoid significance claims and report effect sizes + confidence intervals.
- **Outliers**: no trimming unless pre-declared; if trimming is used, report both trimmed and untrimmed.

### 17.4.1 Unit of Analysis (Declared)

- **Primary unit**: episode/run (a single seeded execution of a declared configuration).
- **Secondary units (reported but not used for CI resampling unless declared)**: decisions, entities.

### 17.4.2 Theoretical Addendum Commitments (If Pursued)

These are **not results**; they are pre-registered targets for formal contribution beyond empirical measurement.

- **Decision boundary (ACT vs WAIT)**:
  - Goal: derive sufficient conditions where WAIT dominates ACT under delayed reconciliation.
  - Allowed inputs: observable conflict measures (conflict size/entropy), delay distribution assumptions, and cost asymmetry parameters.
  - Output form: an explicit inequality/threshold rule (even if conservative) that can be evaluated from artifacts.

- **Robustness / catastrophic failure modes**:
  - Goal: exhibit a class of shock patterns and cost regimes where overwrite semantics admits unbounded (or practically unbounded) amplification, while conflict-preserving semantics remains bounded under a declared policy class.
  - Acceptable evidence: a formal bound + a matching adversarial construction, plus artifact-based empirical confirmation within tested regimes.

- **Impossibility / regret lower bounds**:
  - Goal: connect to known impossibility/limits (e.g., partial observability with delayed labels) by proving lower bounds or impossibility of bounded regret under overwrite semantics for a declared decision class, and showing how conflict preservation changes the conditions.
  - Acceptable evidence: theorem + proof under explicit assumptions; if only conjectures are achieved, label them explicitly as conjectures and test them empirically without upgrading to a claim.

### 17.5 Run Integrity & Stopping Rules

- A run is invalid if schema validation fails, artifacts are incomplete, or seed/config is missing.
- Stopping rules are operational (resource/time budget), not outcome-driven: e.g., stop after N episodes per config or a fixed wall-clock budget declared before execution.

### 17.6 Artifact Traceability (Minimum Set)

Every run must persist:

- `run_manifest.json`: code version, config, seed, start/end time, host info, artifact paths, and checksums.
- `events.parquet` (or equivalent): canonical `Event` stream.
- `decisions.parquet`: `DecisionRecord` stream with evidence-set references.
- `reconciliation.parquet`: `ReconciliationSignal` stream.
- `metrics.json`: computed metrics with metric definitions/version.

Artifacts must be immutable once written (content-addressed or equivalent).

### 17.7 Execution Protocol (Minimum)

To keep runs defensible and repeatable:

- All experiments run via a CLI entrypoint (no manual notebook steps for primary results).
- Each run must:
  - validate schemas before execution begins
  - write artifacts to a unique run directory
  - write `run_manifest.json` last (so its presence implies completeness)
  - fail fast on missing artifacts or schema violations
- A “sweep” is defined as a set of runs over a declared grid of configurations with matched seeds across systems under test.

### 17.8 Sweep Declaration Template (Copy/Paste)

Record sweeps in this format before execution:

- **Sweep ID**:
- **Date**:
- **Workload generator version**:
- **Systems under test**:
- **Fixed seed set**: (e.g., 50 seeds)
- **Configuration grid**:
  - conflict rates:
  - delay distribution family + params:
  - missingness:
  - policy set:
  - cost curvature:
- **Planned episodes per config**:
- **Stopping rule**:
- **Primary metrics**: (subset of M1–M6)

## Closing Note

This experimental framework is intentionally constrained.

Its purpose is not to maximize coverage, but to enable **precise, adversarially robust measurement** of a narrowly defined distributed systems failure mode.

Committee note: the key question is whether the phenomenon being measured (conflicts + delays under delayed reconciliation) is important enough to justify the apparatus. This document is designed so that, if results are interesting, they are hard to dismiss as hand-tuned or anecdotal.

---

## Appendix D — Domain-Agnostic Pipeline Positioning (Non-Result Framing)

This appendix is **positioning**, not an experimental claim. It clarifies the intended domain-agnostic role of the “pre-commit decision layer” without asserting universality of outcomes.

This is a domain-agnostic pipeline by role (blocks defined by systems function, not business context):

0) Reality

The world evolves; you do not control it.

Unknown, delayed, partially observed.

1) Signals / Evidence 


Observable variables about reality and system conditions.

No authority

No commitment

May conflict, lag, be missing, or be adversarial

2) Pre-commit decision layer 

 (thesis contribution candidate)

A domain-agnostic engine that:

Represents uncertainty explicitly

Compares ACT vs WAIT under uncertainty

Enforces admissibility rules (dominance / bounded harm / bounded influence)

Outputs: issue command or defer or issue safer variant

3) Command 


A single irreversible instruction (from the system’s point of view).

Minimal, typed, replayable

4) Consensus / Ordering (optional but common)

Mechanism ensuring a consistent order of commands (within a shard/partition/region).

Raft/Paxos, sequencer, transactional commit, log service, etc.

5) Authoritative ledger / log 


The record of committed commands in order.

6) State machine 


Deterministic application:


7) Derived views / propagation

Caches, dashboards, apps, analytics—allowed to lag.

That’s the full pipeline. The only new piece you add is #2.

Universal elements in “Signals” (works in every domain)

You asked for “NO domain signals.” Here are universal signal classes that every real distributed system has, including Verizon:

A) Demand / intent signals

requests arriving, workload level, user intent, planned operation

B) Resource / capacity signals

CPU, memory, bandwidth, quotas, rate limits, headroom

C) Quality / performance signals

latency, throughput, jitter, loss, error rates, tail behavior

D) Health / fault signals

timeouts, crashes, partitions, partial outages, retries, saturation

E) Policy / constraint signals

permissions, compliance gates, safety constraints, SLO budgets

F) Provenance / trust signals

source identity, confidence, staleness, disagreement across sources

These categories are universal. Only the names change.