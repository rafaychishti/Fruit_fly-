# Architecture

## Target pipeline (per project brief, section 8)

```
FlyWire Connectome
        v
Neural preprocessing + cell-type mapping
        v
Neural dynamics (LIF / conductance / other validated models)
        v
motor neurons
        v
Motor transformation / muscle interface
        v
Flybody / NeuroMechFly + MuJoCo
        v
Environment
        v
Sensory simulation (vision, mechanosensation, proprioception, olfaction, gustation)
        |
        +---------------------------> back to neural dynamics (closed loop)
```

The system is meant to run continuously, not as disconnected offline
stages. Nothing below claims we have built this yet — see "Status" per
stage.

## Status as of this bootstrap session (2026-09-23)

| Stage | Status | Where |
|---|---|---|
| Physical body (Flybody MJCF, 78 actuators, 15 sensors) | **Running** — compiles in MuJoCo 3.14.0, headless-rendered, benchmarked | `embodiment/flybody/`, `scripts/run/run_body.py`, `experiments/001_body_baseline/` |
| Physics engine (MuJoCo) | **Running**, CPU-only, ~600-1000 steps/s | same |
| Neural dynamics engine (LIF) | **Skeleton only** — deterministic synthetic network, no real connectome | `neural/`, `experiments/002_neural_baseline/` |
| Connectome ingestion | **Not started — blocked** on network access to `codex.flywire.ai` from this sandbox | `docs/research/data-sources.md` |
| Motor interface (neurons -> muscles) | Not started | `embodiment/motors/`, `embodiment/muscles/` (empty) |
| Sensory simulation (vision/olfaction/etc.) | Not started; FlyGym identified as the likely source, not yet installed | `embodiment/sensors/` (empty) |
| Closed loop runtime | Not started | `simulation/closed_loop/` (empty) |
| Dashboard / visualization | Not started | `visualization/` (empty) |

## Design principles carried over from the brief, restated here

1. **Infrastructure vs. emergent behavior is a hard line.** Body,
   morphology, physics, sensory transduction, connectivity, neuron/synapse
   models, actuator/muscle mechanics, and environment mechanics are things
   *we provide*. Locomotion, turning, navigation, orientation, feeding,
   grooming, escape, state transitions, exploration are *hypotheses to
   test*, never hand-coded into the controller once a real neural circuit
   is in the loop. The one exception, made explicit every time it's used:
   `scripts/run/run_body.py`'s `--mode tripod` is a **hand-engineered**
   oscillator used only to sanity-check the body's actuators before any
   neural circuit exists — it is not, and must never be presented as, a
   locomotion result.
2. **No-RL primary experiment.** The central experiment is
   connectome -> neural dynamics -> motor neurons -> body, not
   observation -> trained-policy -> action. RL controllers may exist only
   as explicitly labeled baselines for comparison.
3. **Every behavior gets classified**, once we have any: EMERGENT /
   PARTIALLY ENGINEERED / EXPLICITLY PROGRAMMED / LEARNED. See
   `docs/assumptions.md` for the running list of engineered pieces so far.
4. **Small before big.** Phase 1 baseline uses the full anatomical body but
   zero neural circuitry; Phase 2 will use a tiny *synthetic* LIF network
   (tens of neurons) before any FlyWire data is ingested at all, and even
   then Phase 3/4 target a small, behaviorally-relevant sub-circuit, not
   the whole connectome.

## Repository layout

See the top-level directory tree (created this session) for the full
section-15 layout. Populated so far: `docs/`, `embodiment/flybody/`,
`scripts/run/`, `experiments/001_body_baseline/`, `neural/` (skeleton). All
other directories exist as placeholders for later phases.
