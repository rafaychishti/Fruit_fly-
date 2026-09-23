# Embodied FlyWire Drosophila

Open, reproducible, real-time embodied simulation of *Drosophila
melanogaster*, coupling biological connectivity from the FlyWire connectome
to a physics-based virtual fly body. See `docs/architecture.md` for the
full target pipeline and `docs/assumptions.md` for every approximation
made along the way. This is a research scaffold, not a finished system --
read the status table in `docs/architecture.md` before assuming any phase
beyond Phase 1/2 is working.

## What's real right now

- `embodiment/flybody/` -- the actual DeepMind/HHMI Flybody MJCF model (78
  actuators, 15 sensors, 68 bodies), Apache-2.0, vendored from
  `google-deepmind/mujoco_menagerie`.
- `scripts/run/run_body.py` -- loads it, inspects it, runs three scripted
  (explicitly non-biological) control conditions, benchmarks simulation
  speed, and records video. See `experiments/001_body_baseline/`.
- `neural/` -- a minimal, deterministic, vectorized LIF neuron population +
  synthetic sparse connectivity generator, validated (not biological --
  see `docs/assumptions.md`). See `experiments/002_neural_baseline/`.

## What's explicitly NOT done yet

- No real FlyWire connectome data is in this repo. `codex.flywire.ai` is
  unreachable from the sandbox this was bootstrapped in, independent of
  credentials -- see `docs/research/data-sources.md` for exactly what was
  tested and what it would take to unblock.
- No neural-to-motor interface, no closed sensorimotor loop, no vision/
  olfaction/gustation simulation, no dashboard.
- Nothing here is claimed to demonstrate emergent behavior. Every
  controller currently in the repo is explicitly programmed and labeled as
  such (see `docs/assumptions.md` item 3).

## Quickstart

```bash
pip install -r requirements.txt
python3 scripts/run/run_body.py --mode standing --duration 1.5 --record out.mp4
python3 neural/dynamics/run_network.py --n 200 --steps 5000
```

## Repository layout

Follows the structure in `docs/architecture.md`. Directories that exist
but are still empty are placeholders for later phases (see the status
table there) -- their presence is not a claim that phase is done.

## License

TBD -- the body model is Apache-2.0; any FlyWire-derived data used later
will carry CC BY-NC-SA 4.0 terms (non-commercial, share-alike,
attribution). This repo's own license needs to be chosen compatibly with
both before any real connectome data lands in it.
