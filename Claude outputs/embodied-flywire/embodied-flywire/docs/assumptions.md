# Assumptions and approximations log

Every approximation the project makes, tracked here as required by section
9 of the brief. New entries append; nothing gets silently removed.

## Phase 1 — physical body baseline (2026-09-23)

1. **Body model provenance.** We use the DeepMind/HHMI Flybody MJCF exactly
   as distributed in `google-deepmind/mujoco_menagerie` (Apache-2.0),
   unmodified except for being vendored file-by-file into this repo (see
   `docs/research/data-sources.md` for why: this sandbox cannot `git
   clone` GitHub repos). We have not diffed it against `TuragaLab/flybody`'s
   own copy to confirm they're identical — assumed equivalent, not verified.
2. **No active postural/balance control exists yet.** `--mode standing`
   (zero control) and `--mode tripod` (a hand-tuned antiphase sinusoid on
   coxa/femur/tibia actuators, claws force-adhered) were both run for 1.5
   simulated seconds. **Finding, not a bug:** in both cases the fly tips
   over and ends up dorsal-side-down within ~1 second under gravity (see
   `experiments/001_body_baseline/*_last.png`). This is expected — insect
   legs need active tone/reflexes to support body weight, and neither
   controller provides any feedback (no proprioceptive or tarsal-contact
   loop is closed yet). Recorded here so it isn't mistaken for an emergent
   finding about "the fly can't stand" once a real neural circuit is
   involved later — right now there is no controller sophisticated enough
   to draw that conclusion from.
3. **`--mode tripod` is EXPLICITLY PROGRAMMED**, per the brief's own
   behavior-classification requirement (section 9/17). It exists only to
   confirm the actuators respond and produce leg-cycling motion, not as a
   locomotion result of any scientific interest. It should be deleted or
   clearly quarantined once a real motor interface (Phase 5) exists, so it
   can't be mistaken for a baseline "engineered" comparison condition later.
4. **Simulation timestep (1e-4 s) is fixed by the model**, not chosen by
   us. Combined with this sandbox's CPU-only ~600-1000 steps/s, real-time
   factor is ≈0.06-0.10x. Any claim of real-time closed-loop operation
   later must either run on different hardware (GPU) or explicitly report
   its real-time factor rather than assume it's 1.0x.
5. **Headless rendering uses OSMesa software rasterization**, not a GPU
   renderer. Visual quality/lighting is not tuned; frames are for
   diagnostic and dashboard purposes only, not for anything vision-model
   dependent yet (Phase 8 vision experiments will need to reconsider
   render fidelity/eye-camera calibration before drawing conclusions from
   what the fly "sees").
6. **Network/data-access constraints are environmental, not scientific**,
   but they gate what's possible: FlyWire/Codex is unreachable from this
   sandbox regardless of credentials (policy-level block, confirmed by
   direct testing), and no GPU is present. These are recorded in
   `docs/research/data-sources.md` and restated here because they will
   determine which phases can proceed without a different environment or
   the user's direct involvement (e.g. downloading a FlyWire dataset
   themselves and uploading it).

## Phase 2 — synthetic LIF network skeleton (2026-09-23)

7. **Connectivity is synthetic random, not biological**, by design (see
   `neural/connectivity/random_sparse.py` docstring) -- purely to validate
   the dynamics-loop plumbing before any real data exists. 200 neurons,
   5% connection probability, ran deterministically (identical SHA-256 of
   the spike raster across two independent runs with the same seed) at
   ~41,000 steps/s on this sandbox's 2 vCPUs -- see
   `experiments/002_neural_baseline/`.
8. **Connectivity generation is currently O(n^2) (dense mask before sparsifying)** --
   fine at n=200, but this will NOT scale to the 1k/10k/50k/whole-connectome
   sizes in Phase 10 (138k^2 ~= 1.9e10 entries). Needs to be rewritten to
   generate sparse structure directly (e.g. drawing edges rather than
   masking a dense matrix) before Phase 10, and obviously replaced
   entirely once real connectivity is ingested in Phase 3.
9. **LIF timestep chosen as 0.2 ms (5 kHz)** to match the timestep
   `fly-brain-full` reportedly uses (per its own README, unverified) --
   borrowed as a starting point, not derived independently. Notably
   coarser than MuJoCo's own 0.1 ms physics timestep; Phase 5/6 will need
   to decide how the two clocks relate (sub-stepping one relative to the
   other) rather than assuming they can just share a step count.

## Still undocumented (known gaps, not yet assumptions because not yet built)
Neuron dynamics beyond LIF, membrane properties, synaptic dynamics/delays/
strengths, neurotransmitter effects, neuromodulation, sensory transduction
detail, motor-neuron-to-muscle mapping, muscle dynamics, developmental/
physiological state. These get their own entries once Phase 2+ actually
makes a choice about each.
