# Phase 4 — First Real-Circuit Neural Simulation

**STATUS: implementation and experiment complete. NOT YET COMMITTED.**
Per the project lead's explicit instruction, this phase's code and
results are reported here for review first; the commit/tag happens
only after that review. Phase 3.2 (connectivity ingestion) was already
separately accepted and is committed as
`phase-3.2-connectivity-forensic-validation`.

**This is a neural-circuit validation experiment. It is NOT an
embodied behavioral experiment.** No MuJoCo, no `SensoryEncoder`, no
`MotorDecoder`, no actuator, no behavioral claim of any kind is made
anywhere in this phase. Biological scope is strictly
LC4/LPLC2 → DNp01 — no TTMn, no PSI, no VNC circuitry, no MaleCNS, no
other cross-dataset motor pathway.

## 1. The FlyWire graph

`neural/flywire/graph.py`'s `FlyWireGraph`, built from the Phase
3.2-validated `circuit_connectivity_filtered.csv` via
`load_flywire_circuit(synapse_file="circuit_connectivity_filtered.csv")`:

```
n_neurons: 316
n_synapses (edge-records, one per pre/post/neuropil): 11,203
n_connections (distinct pre/post pairs, any neuropil): 10,711
total_synapse_count: 18,470
n_synapses_dropped_missing_endpoint: 152,531  (rows touching neurons outside our 316 -- correctly out of scope, not an error)
n_connected_components: 2
largest_component_size: 163
cell_type_counts: {"LC4": 104, "LPLC2": 210, "DNp01": 2}
```

Every neuron retains its real `root_id`, `identified_type`, `side`,
and source provenance (`data/flywire/manifest.json`). Every edge
retains its real `pre_id`, `post_id`, `neuropil`, `synapse_count`, and
the per-connection neurotransmitter-probability fields
(`gaba_avg`/`ach_avg`/etc.) in `metadata` — **nothing is silently
discarded**. Two changes were made to `neural/flywire/graph.py` and
`neural/flywire/synapses.py` to satisfy this:

- `Synapse` gained a `neuropil` field (previously dropped).
- `FlyWireGraph.from_records()`'s dedup key changed from `(pre, post)`
  to `(pre, post, neuropil)`, so a pair connected across multiple
  neuropils is kept as separate, fully-labeled edges instead of being
  silently merged into one. A new `pair_totals()` method (and
  `n_connections` property) gives the total-synapses-per-pair view
  when that's what's wanted instead.
- `out_degree()`/`in_degree()` were fixed to count **distinct
  partners** via `pair_totals()`, not raw edge-records — otherwise a
  multi-neuropil pair would have silently double-counted a partner
  after the dedup-key change above. Caught during this phase's own
  design review, not by a test failure; verified by the full suite
  re-run afterward.

All 316 neurons and all 10,711 connections are real, checksum-verified
FlyWire data (Phase 3.2). The full graph, including the substantial
LC4↔LPLC2 lateral connectivity, is preserved in `FlyWireGraph` — see
item 3 below for what this phase's simulation actually uses of it.

## 2. REAL / DATA-DERIVED vs. MODELED vs. ENGINEERED

Full breakdown: `docs/interfaces/flywire-backend.md`. Summary:

**REAL / DATA-DERIVED**: which 316 neurons exist and their identity/
side/position; which pairs are connected and in which neuropil;
`syn_count` per edge; direction (independently verified, Phase 3.2);
the neurotransmitter-probability fields (retained, not interpreted).

**MODELED** (every one has an `ASSUMPTION FW-###` entry in
`docs/assumptions.md`):
- FW-001: LIF dynamics and every LIF parameter value, reused verbatim
  from earlier synthetic-network defaults, identical across all 316
  neurons regardless of real cell type.
- FW-002: synaptic weight `w = 0.01 × total_syn_count`, all-excitatory.
  `syn_count` is real; this mapping to a simulate-able weight is not.
- FW-003: this phase's simulation is scoped to `LC4→DNp01` and
  `LPLC2→DNp01` only (293 of the graph's 10,711 real connections) —
  a disclosed scope choice, not data loss; `FlyWireGraph` still holds
  every real edge.
- FW-004: the stimulus protocol (fixed current, fixed window, fixed
  target population) is a synthetic circuit-probe, not a visual/
  looming encoding model.

**ENGINEERED**: `FlyWireCircuitTopology`, `build_topology()`,
`FlyWireBackend`'s step/reset loop, and this experiment's stimulus
scheduling, logging, and plotting code.

No LIF parameter is described anywhere as a biological measurement.
No claim is made that `weight = syn_count` is biologically validated.

## 3. FlyWireBackend

`neural/backends/flywire_backend.py`'s `FlyWireBackend` implements the
**existing** `NeuralBackend` ABC
(`neural/interface/neural_controller_interface.py`) — the same seam
`LIFBackend` (Phase 2.5) already proved out. No parallel architecture
was created; `simulation/`, `embodiment/`, the `SensoryEncoder`/
`MotorDecoder` ABCs, and `LIFBackend` itself are all untouched (full
78-test suite, including the original Phase 2/2.5/2.5.1 tests,
confirmed unmodified/passing — see item 9).

`FlyWireBackend.step(sensory_input, dt_s)` accepts an external-current
vector indexed in `topology.root_ids` order, computes
`synaptic_input = W.dot(recent_spikes)` (real-graph-derived recurrent
input) plus the external input, steps the underlying `LIFPopulation`,
and returns the DNp01 sub-population's spike vector as the ABC's
"motor-neuron output activity" (DNp01 — the descending/output neuron
of this minimal circuit — is the closest analogue this circuit has to
a motor-neuron layer; there is no motor neuron in FAFB's brain-only
volume, see Phase 3.1 item 3). The full 316-neuron spike vector is
exposed separately as `self.last_spikes` for rastering.

`build_topology(graph, ablate_edge_classes=(...))` builds the
deterministic neuron ordering and the scoped weight matrix; ablation
zeroes a named edge class's contribution to `W` (and records
`weight=0.0` in its `edge_list` entries) **without mutating the
underlying `FlyWireGraph`** — verified directly by
`test_ablation_does_not_mutate_underlying_graph`.

## 4. Synaptic weight is not a claimed biological quantity

`w = WEIGHT_SCALE_PER_SYNAPSE * syn_count` (`WEIGHT_SCALE_PER_SYNAPSE
= 0.01`), all-excitatory. This is exactly `ASSUMPTION FW-002` in
`docs/assumptions.md`, documented there in full, including why sign
could not be correctly assigned from this dataset (receptor identity,
not just presynaptic neurotransmitter identity, is needed) and why an
all-excitatory network is expected to bias the circuit toward *more*
activity than a correctly-signed one would show. `0.01` was picked
once, as a round number, and never searched, tuned, or adjusted based
on how the resulting activity looked — see item 10.

## 5. Controlled stimulus experiment

`experiments/007_flywire_neural_simulation/exp_stimulus_response.py`.
Config: `seed=0`, `dt_ms=0.2`, 500 steps (100 ms total), stimulus
window `[10, 60] ms`, stimulus current `3 × rheobase = 0.15`
(rheobase `= v_threshold / tau_m_ms = 0.05`) into every neuron of the
stimulated type(s), zero everywhere/everywhen else. DNp01 never
receives direct external current in any condition.

Base conditions:

| Condition | Stimulated | DNp01 spikes | First DNp01 spike (ms after stim onset) |
|---|---|---|---|
| A_no_input | none | 0 | — |
| B_LC4 | LC4 only | 4 | 18.6 |
| C_LPLC2 | LPLC2 only | 7 | 8.2 |
| D_combined | LC4 + LPLC2 | 10 | 8.2 |

## 6. Required outputs

- **Raster** (LC4/LPLC2/DNp01 rows distinguished by color):
  `raster_base_conditions.png`, `raster_ablation_conditions.png`.
- **Population firing rates over time**: `firing_rates_base_conditions.png`.
- **Connectivity visualization of the real recovered graph** (edge
  magnitude = real `syn_count`, explicitly labeled dataset-derived,
  never presented as the modeled weight): `connectivity_lc4_lplc2_to_dnp01.png`.
- **Stimulus-response summary** (stimulus, duration, # stimulated
  neurons, spike counts per group, first-spike latency, DNp01
  response, seed/config, per condition): `stimulus_response_summary.json`.

## 7. Controls and causal ablations

Controls A–D above (no input; LC4; LPLC2; combined). Two causal
ablations, each with its relevant stimulation repeated:

| Condition | Ablated edge class | Stimulated | DNp01 spikes |
|---|---|---|---|
| E_LC4_ablated__LC4_stim | LC4→DNp01 | LC4 only | **0** |
| F_LC4_ablated__combined_stim | LC4→DNp01 | LC4+LPLC2 | 7 |
| G_LPLC2_ablated__LPLC2_stim | LPLC2→DNp01 | LPLC2 only | **0** |
| H_LPLC2_ablated__combined_stim | LPLC2→DNp01 | LC4+LPLC2 | 4 |

Interpretation, restricted explicitly to this model: within this LIF
model and stimulus configuration, edge ablation demonstrates that the
simulated DNp01 response depends on the included LC4/LPLC2
connectivity, not on the stimulus alone. Removing a pathway that is
the *only* modeled route to DNp01 under that stimulation (E, G)
silences DNp01 completely in the simulation. Removing one pathway
while the other stays intact (F, H) reduces but does not eliminate the
simulated DNp01 response, and the surviving response (F=7, H=4) is
numerically identical to that pathway's own solo condition (C=7, B=4)
— expected, since in this scoped topology LC4 and LPLC2 drive DNp01
independently (there is no LC4↔LPLC2 edge inside the simulated `W`);
this is a consistency check on the model's mechanism, not a claim
about the biological circuit. This is model-internal evidence about
how the implemented dynamics use the included connectivity — it is
**not** biological causal evidence about the real Drosophila circuit,
and is not presented as such. See the "Synaptic-scale sensitivity"
section below for whether this observation holds up under a different
arbitrary choice of the one MODELED parameter (weight scale) this
result could plausibly be sensitive to.

## 8. Determinism

`D_combined` was run twice with an identical seed (0) and identical
config. Full 316-neuron, 500-step boolean spike arrays compared with
`np.array_equal`: **exact_equal = True**. Recorded in
`stimulus_response_summary.json`'s `determinism_check` field.

## 9. Tests

`tests/test_flywire_backend.py` — 23 new tests covering exactly the
list this phase specified: graph loading, neuron count, edge count,
directionality, syn_count preservation, LIF state initialization,
deterministic stepping, spike generation, causal edge ablation, and
no-input behavior (see the file for the full list; each test name
states which requirement it covers).

Full suite: **78 passed** (`pytest tests/ -q`). This includes every
pre-existing test from Phases 0–3.2. One pre-existing test,
`test_manifest_documents_the_connectivity_blocker` in
`test_flywire_ingestion.py`, was updated (renamed to
`test_manifest_documents_connectivity_acquisition`) because it
asserted the **now-stale** pre-Phase-3.2 fact that
`manifest.json`'s `synapse_connectivity` status was `"BLOCKED"` — that
status is genuinely `"ACQUIRED"` now, with the project lead's
acceptance, so the test's expected value was updated to match, not
weakened; it still asserts the real MD5 checksum and the presence of
the `not_fabricated` provenance field. No other existing test was
touched.

## 10. Scientific restrictions — compliance

- **No MuJoCo integration.** Not imported, not referenced, anywhere in
  this phase's code.
- **No behavioral emergence claimed.** Every plot and doc explicitly
  labels this a neural-circuit validation experiment, not a behavioral
  one.
- **No parameter tuning for a "desired" look.** `WEIGHT_SCALE_PER_SYNAPSE
  = 0.01` and the LIF params were fixed once (reused from Phase 2.5.1,
  a round constant for the weight scale) *before* the experiment was
  ever run, and never adjusted afterward based on the resulting
  raster/firing-rate shape.
- **No RL, no optimization against a target response.**
- **No inference of biological realism from a visually plausible
  raster.** The observed regular, periodic bursting (LC4/LPLC2 firing
  at a steady ~50 Hz once past threshold under sustained 3× rheobase
  current, DNp01 following each burst) is the expected, unremarkable
  behavior of a leaky integrate-and-fire neuron under constant
  superthreshold current with a 2 ms refractory period — a property
  of the LIF model and this stimulus choice, not evidence of anything
  biological. This project does not claim it is.
- **No fabricated synaptic weights, no added VNC circuitry.** Scope
  remained exactly LC4/LPLC2 → DNp01 throughout.
- **The circuit was not silent, unstable, or hypersynchronous** at
  this stimulus level — it produced a modest, non-degenerate response
  (4–10 DNp01 spikes per 100 ms trial, single-hemisphere-scale
  activity, no runaway firing, no all-or-nothing collapse). This is
  reported as observed, not adjusted toward or away from any target.

## Synaptic-scale sensitivity

Requested by the project lead as a scientific gate before acceptance:
`ASSUMPTION FW-002`'s weight mapping uses an arbitrary, never-fit
constant (`WEIGHT_SCALE_PER_SYNAPSE = 0.01`). Before treating item 7's
ablation result as a stable qualitative finding, this section checks
whether it survives a small, pre-registered change to that one
arbitrary constant.

```
DATA-DERIVED:
    syn_count  -- real, checksum-verified, Phase-3.2-validated per-edge
                  synapse count (unaffected by weight_scale; identical
                  edge_list syn_count values at every scale tested,
                  see test_weight_scale_is_a_multiplicative_factor_on_
                  every_edge_weight)

MODELED:
    conversion from syn_count to LIF efficacy
        w = weight_scale * syn_count, all-excitatory (ASSUMPTION FW-002)
        weight_scale tested at {0.005, 0.01 (baseline), 0.02} -- fixed
        before running, never searched or fit to any target output

OBSERVED:
    spike counts under each tested scale (below)
```

**Method**: `experiments/007_flywire_neural_simulation/exp_weight_sensitivity.py`.
Every condition, the stimulus (current, window, target neurons), the
LIF parameters, the seed, and the ablation edge classes are held
byte-identical to the baseline experiment (imported directly from
`exp_stimulus_response.py`, not retyped) — only `weight_scale` varies.
The original 0.01 baseline result in items 5–8 above is **unchanged**;
this is a separate, additional analysis.

**Results** (DNp01 spike counts, 100 ms trial, 50 ms stimulus window):

| Condition | scale=0.005 | scale=0.01 (baseline) | scale=0.02 |
|---|---|---|---|
| LC4 alone | 0 | 4 | 10 |
| LPLC2 alone | 2 | 7 | 10 |
| combined | 7 | 10 | 10 |
| LC4 ablation (LC4 stim, LC4→DNp01 removed) | 0 | 0 | 0 |
| LPLC2 ablation (LPLC2 stim, LPLC2→DNp01 removed) | 0 | 0 | 0 |

Full per-condition detail (firing rates, synchrony fractions, membrane-
potential extrema) is in `weight_sensitivity_results.json`.

**Silence / synchrony / instability / saturation — as observed, no
invented thresholds**:

- **Silent**: at `scale=0.005`, LC4-alone stimulation produces **zero**
  DNp01 spikes, even though LC4 itself fires normally (520 spikes over
  the trial, ~100 Hz during the stimulus window) — at this scale, the
  LC4→DNp01 pathway's aggregate weight is insufficient to cross
  threshold on its own. No condition was silent in *every* population
  (LC4/LPLC2 always fire, since they receive the stimulus current
  directly regardless of weight_scale).
- **Synchronous**: LC4 and LPLC2 each show ~95–96% of their own
  population spiking in the same step at every scale tested (max
  synchrony fraction 0.952 / 0.962) — this is a property of the
  stimulus protocol (identical external current to every neuron of
  that type, near-identical seeded initial membrane potential), not of
  weight_scale, and is present in the baseline too. DNp01's two
  neurons go from never co-spiking (fraction 0.0, scale=0.005,
  LC4-alone) to co-spiking at least once whenever any response exists
  (fraction 1.0 in every other nonzero case) — with only 2 DNp01
  neurons, "synchrony fraction" here is coarse (0, 0.5, or 1.0) and
  should be read as such.
- **Numerically unstable**: none. Membrane potential stayed in
  `[~-0.02, ~1.0]` (i.e. within one reset/threshold cycle of rest) at
  every scale, every condition; `any_nonfinite_membrane_potential` was
  `False` in all 15 (condition × scale) runs.
- **Saturated**: DNp01's response caps at 10 spikes (rate 100 Hz) at
  `scale=0.02` for LC4-alone, LPLC2-alone, and combined alike —
  identical to LC4/LPLC2's own driven rate (100 Hz, 22% of the LIF
  model's refractory-limited theoretical maximum of ~455 Hz). This
  reads as DNp01 locking one-to-one onto its input population's spike
  train once synaptic drive is strong enough to guarantee threshold
  crossing on every incoming volley — not as the network approaching
  the model's own maximum firing rate.

**Is the qualitative finding scale-dependent?** Two separate
qualitative claims from item 7, checked separately:

1. *"Stimulating a pathway produces a DNp01 response."* **Not robust**
   for LC4 alone: the response is present at 0.01 and 0.02 but is
   **exactly zero** at 0.005. It *is* robust for LPLC2 alone and for
   the combined condition (present, nonzero, at all three scales) —
   consistent with LPLC2 contributing more total real synapse count
   onto DNp01 than LC4 (1,080 vs. 805, Phase 3.2) and therefore more
   modeled weight at every scale. **This is a genuine model-sensitivity
   finding, reported as such**: whether LC4-alone stimulation produces
   any DNp01 response in this model depends on where the arbitrary
   weight scale falls, at least across the bracket tested.
2. *"Ablating a pathway's only route to DNp01 removes the
   corresponding response."* This holds at all three scales — but only
   trivially where there was a response to remove (LPLC2 ablation,
   scale ≥ 0.005; LC4 ablation, scale ≥ 0.01). At `scale=0.005`, LC4
   ablation and the intact LC4-alone condition are **identical (both
   0)**, because there was no response to remove in the first place —
   the ablation test is not informative in that regime, and this
   report does not claim otherwise.

**Conclusion**: this is not presented as evidence for or against any
particular scale being biologically plausible — none of the three
values tested is claimed to be. It is reported as a characterization
of this specific model's sensitivity to its one disclosed, arbitrary
parameter: the combined-stimulus and LPLC2-driven results are
qualitatively stable across the bracket tested; the LC4-alone result
is not, and that instability is disclosed rather than hidden behind
the single baseline number.

**Determinism at each scale**: re-checked directly (not assumed) —
identical seed, two independent runs, exact spike-array equality at
`scale ∈ {0.005, 0.01, 0.02}`. All three: `exact_equal=True`
(`weight_sensitivity_results.json`'s `determinism_by_scale`).

**Tests**: `tests/test_weight_sensitivity.py` (8 test items) verify the
scale parameter is actually wired through `build_topology()`/
`FlyWireBackend` (exact `w = scale * syn_count` per edge, exact 4×
ratio between the 0.005/0.02 matrices), that its effect is confined to
DNp01's input (LC4/LPLC2's own spike trains are scale-invariant, since
they have no incoming edges in this scoped topology), that increasing
scale never *decreases* DNp01's spike count (a structural monotonicity
property of this feedforward-only topology, not a specific observed
value), and that deterministic stepping holds at each of the three
pre-registered scales. No test asserts a specific spike count as a
regression value.

## Acceptance

Given: real graph (item 1), explicit REAL/MODELED/ENGINEERED boundary
(item 2), `FlyWireBackend` extending the existing `NeuralBackend` ABC
without breaking `LIFBackend` (item 3), a disclosed, non-biological
weight mapping (item 4), a deterministic controlled-stimulus
experiment (item 5) with all required outputs (item 6), all required
controls and two causal ablations demonstrating that, within this LIF
model and stimulus configuration, the simulated DNp01 response depends
on the included LC4/LPLC2 connectivity (item 7), verified exact
determinism (item 8) — now re-verified at three synaptic scales, see
above — a full test suite covering the specified list with 86/86
passing (item 9), no violation of any of the ten scientific
restrictions (item 10), and a transparent, pre-registered
weight-scale-sensitivity characterization (per the project lead's
scientific gate above) that discloses rather than hides where the
baseline's qualitative finding is and isn't robust — this phase's
implementation and experiment are complete and ready for review.

Per the gate's acceptance rule: (1) execution remains deterministic at
every scale tested; (2) the sensitivity experiment ran cleanly, no
non-finite values, no crashes; (3) the arbitrary weight assumption
(`ASSUMPTION FW-002`) is characterized transparently, including the
LC4-alone result's non-robustness; (4) causal language throughout this
report is restricted to the model ("within this LIF model...", never
"biological proof"); (5) no biological claim is made from the LIF
response itself anywhere in this document.

## STOP

**Do not commit.** Per the project lead's explicit instruction, this
report is the stop point: the experiment, the weight-sensitivity
analysis, and the tests are to be reviewed before Phase 4 is
committed. **Do not begin MuJoCo integration** or any further phase
until that review and an explicit go-ahead.

## Files this phase added/changed

- `neural/flywire/synapses.py`, `neural/flywire/graph.py` (edited —
  neuropil-preserving, `pair_totals()`, fixed degree counting)
- `neural/backends/flywire_backend.py` (new)
- `docs/interfaces/flywire-backend.md` (new)
- `docs/assumptions.md` (items 19–22, `ASSUMPTION FW-001..004`)
- `experiments/007_flywire_neural_simulation/exp_stimulus_response.py`
  (+ its output JSON and 4 PNGs) — baseline, unchanged since first
  report
- `experiments/007_flywire_neural_simulation/exp_weight_sensitivity.py`
  (new) (+ `weight_sensitivity_results.json`)
- `tests/test_flywire_backend.py` (new, 23 tests)
- `tests/test_weight_sensitivity.py` (new, 8 test items)
- `tests/test_flywire_ingestion.py` (one test updated to match Phase
  3.2's accepted manifest status)
- this file
