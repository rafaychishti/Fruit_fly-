# Ecosystem reconnaissance (Phase 0)

Compiled 2026-09-23. This is a survey, not an endorsement — every claim below
is attributed to its source and treated as provisional until we've
independently verified it (per the project's Phase 0 exit criterion).

## 1. FlyWire / Codex — biological connectome

- URL: https://codex.flywire.ai/ , FAQ: https://codex.flywire.ai/faq
- Datasets currently listed: FAFB v783 (Female Adult Fly Brain, Oct 2023),
  BANC v888 (Female Adult Fly Brain + Nerve Cord, May 2026), MANC v1.2.1
  (Male Adult Fly Nerve Cord), MAOL v1.1 (Male optic lobe), MCNS v1.0 (Male
  brain + nerve cord). The public FAQ text we could fetch did not itself
  state neuron/synapse counts — the project brief's figures (e.g. FAFB
  ~139,255 neurons) come from Codex's dataset pages / third-party repos
  citing Codex, not the FAQ, and should be re-verified against the download
  portal before being used in any manifest.
- **Access model (hard constraint):** Interactive use requires Google
  sign-in. Programmatic/API access requires a personal API token from the
  user's Codex account page. CAVE/FlyWire tokens are additionally needed for
  live root-ID mapping and edit-history operations.
- Citation requirements exist and are stated on the download portal itself
  (not reproduced in the FAQ) — must be pulled per-dataset before use.
- MANC/MAOL/MCNS: Codex says to use the respective project homepages/
  archives for canonical downloads rather than Codex's own portal.
- **Status in this environment: BLOCKED.** `codex.flywire.ai` is refused by
  this sandbox's network egress policy at the proxy layer (403 on CONNECT,
  independent of authentication), and even if it weren't, we hold no
  FlyWire account or API token on the user's behalf. See
  `docs/research/data-sources.md` for what this means for Phase 3.

## 2. Flybody — physical fly body (Google DeepMind + HHMI Janelia)

- URL: https://github.com/TuragaLab/flybody, Apache-2.0.
- Anatomically detailed Drosophila body for MuJoCo: full articulated body,
  joints, collision geometry, actuators, MJCF model, locomotion/flight/
  vision-guided-flight RL task environments, Ray/DMPO distributed training,
  tutorial notebooks.
- The same body model ships redistributed in
  `google-deepmind/mujoco_menagerie/flybody` (also Apache-2.0, requires
  MuJoCo ≥ 2.2.2). **We obtained this exact model** (see below) and it is
  what Phase 1 in this repo runs against.
- What we actually pulled and verified in this sandbox:
  `embodiment/flybody/fruitfly.xml` (1046 lines) + 85 referenced `.obj`
  mesh files (134 MB), fetched file-by-file over `raw.githubusercontent.com`
  (git clone / `github.com` / `api.github.com` / `codeload.github.com` are
  all blocked here — see data-sources.md). MuJoCo 3.14.0 compiles it
  cleanly: 109 generalized coords, 108 velocity DOF, **78 actuators**, 103
  joints, 68 bodies, 15 sensors (1 accelerometer, 1 gyro, 1 velocimeter, 6
  tarsal force sensors, 6 claw touch sensors), timestep 1e-4 s. It also
  ships pre-built tracking/POV cameras, including `eye_left`/`eye_right`
  compound-eye cameras (fovy 140°) — directly useful for Phase 8 vision
  experiments later.
- Confirmed via Eon Systems' GitHub org: they maintain their own fork of
  `flybody` (16 stars on their fork) — one more independent user of the same
  body model, worth checking for any patches later.

## 3. FlyGym / NeuroMechFly — alternative embodiment + full sensory suite

- URL: https://github.com/NeLy-EPFL/flygym, docs: https://neuromechfly.org/,
  paper: Nature Methods (2024), Apache-2.0.
- NeuroMechFly is a micro-CT-based digital-twin biomechanical model;
  FlyGym is the Python simulation/training harness around it.
- **2.x rewrite (March 2026):** per NeuroMechFly's own documentation, ~10x
  CPU speedup (~2x real-time) and, via a Warp/MJWarp GPU backend, ~300x
  speedup (~60x real-time). This is the path to real-time-or-faster
  whole-connectome-scale runs described in Phase 10/11 of the brief — but
  it needs a GPU, which this sandbox does not have (see
  data-sources.md).
- Sensory modalities: vision (hexagonal-lattice compound eyes), olfaction
  (antennal/palp receptors), full mechanosensory feedback (joint angles,
  actuator forces, contact forces, proprioceptive site positions).
- 1.x is frozen in `flygym-gymnasium` (legacy API); use 2.x for new work per
  the brief's own instruction.
- Not yet installed/tested in this sandbox — next reconnaissance step if we
  pick FlyGym over raw Flybody+MuJoCo for Phase 1 sensory work.

## 4. MuJoCo — physics engine

- https://mujoco.org/, https://github.com/google-deepmind/mujoco, Apache-2.0.
- **Installed and verified in this sandbox:** `pip install mujoco` → 3.14.0,
  no GPU required for CPU stepping; headless rendering works via OSMesa
  (`libosmesa6-dev` + `MUJOCO_GL=osmesa`), confirmed by rendering real frames
  of the fly model (see `experiments/001_body_baseline/`).
- CPU-only single-core benchmark on this 2-vCPU sandbox: ~600-1000 steps/s
  at the model's native 1e-4 s timestep with rendering on/off respectively
  → real-time factor ≈ 0.06-0.10x (i.e. 10-16x slower than real time). This
  is the number to beat before any real-time closed-loop demo is credible
  on hardware like this; GPU (via FlyGym 2.x/MJWarp) or a coarser timestep
  are the two obvious levers, both deferred to later phases.

## 5. Eon Systems (eonsystemspbc) — research references

GitHub org: https://github.com/eonsystemspbc. Repos relevant to this
project, as listed on their org page:

- **fly-brain** (750 stars, GPL-2.0): "Emulation of the Drosophila Fly
  brain" across Brian2, Brian2CUDA, PyTorch, NEST GPU, and neuromorphic
  chips. The most-starred and most directly relevant reference; GPL-2.0
  means anything we borrow from it (vs. merely read for ideas) would need
  care about license compatibility with our own (still TBD) license.
- **drosophila_brain_model_lif** (MIT, 10 stars/50 forks): a fork building
  on Phil Shiu's original LIF model of the Drosophila brain — this is very
  likely the reference implementation behind the Shiu et al. 2024 *Nature
  Methods* connectome-to-behavior LIF paper that both `fruit-fly-lab` and
  FlyGym's docs cite. MIT license makes this the most reusable LIF
  reference we've found so far. Worth a close read in Phase 2/3.
- **flybody** — a fork of TuragaLab/flybody, Apache-2.0, no changes
  identified yet.
- **pathintegrationBPU** — path integration in the fly brain, minor.
- **NEURD-sandbox** — connectomics data-wrangling utilities (proofreading
  transforms), not simulation; possibly useful for Phase 3 preprocessing
  patterns.

## 6. fly-brain-full (rndlabsoy) — whole-connectome embodied reference impl

- https://github.com/rndlabsoy/fly-brain-full, MIT license.
- **Claims** (per its own README, not independently verified by us):
  FlyWire v783, 138,639 neurons, 15,091,983 directed weighted synapses;
  LIF dynamics at 5 kHz (0.2 ms timestep) on GPU via PyTorch, with
  continuous Hebbian plasticity on all synapses; alternative Brian2CUDA/NEST
  GPU backends; sensory pipelines for vision (T1-T5→LC4→giant fiber loom
  detection), olfaction (~2,600 ORNs→PNs→Kenyon cells), gustation (~200
  tarsal taste receptors), mechanosensation; ~1,100 descending neurons
  decoding escape/walk/groom/flight/feed via an explicit "Brain-Body Bridge"
  motor decoder; NeuroMechFly v2 + MuJoCo body.
- **Headline result claimed:** two identically-initialized flies diverge
  behaviorally (81% vs 47% escape rate) and synaptically (0.50% of synapses
  differ) after 24 h of simulated embodied experience — framed as
  "computational individuality."
- ~11,500 lines of Python, 20 modules, 270 MB of data (incl. connectome)
  via Git LFS, 20 timestamped experiment sessions claimed reproducible from
  the repo.
- **Caveats we can already flag without opening the code:** the fetched
  summary contains no discussion of validation against real fly behavior,
  no enumeration of which components are engineered vs. learned vs.
  emergent (which section 9/17 of our own brief requires of *us*), and the
  repo is not clonable in this sandbox (`github.com` blocked; the 270 MB
  LFS payload would also need to come from a Git-LFS media host, unverified
  reachability). Treat every claim here as **unverified pending independent
  inspection** — this is exactly the posture the brief itself demands.

## 7. fruit-fly-lab (vaibhavkedarisetti)

- https://github.com/vaibhavkedarisetti/fruit-fly-lab.
- Interactive whole-brain simulation on real FlyWire FAFB v783 (139,255
  neurons, ~3.7M connections cited), LIF dynamics per Shiu et al. 2024.
  Modules: `brain/` (connectome + populations), `simulation/` (LIF engine +
  stimulus delivery), `web/` (browser visualization), `experiments/`,
  `tests/` (74 tests, data-provenance + "biological accuracy" checks per its
  own description).
- **Explicitly requires the user to download FlyWire FAFB v783 themselves**
  from flywire.ai after creating an account — same access model and same
  blocker as Codex itself.
- **License note:** the underlying FlyWire data is CC BY-NC-SA 4.0 —
  non-commercial, share-alike, attribution required. This directly
  constrains what *we* can do with any FlyWire-derived data too, regardless
  of which pipeline we use to obtain it — flag this now in
  `docs/data-schema.md` / any future licensing doc, before Phase 3.

## What each provides vs. what we still need (Phase 0 exit criterion)

| Component | Who provides it | Status here |
|---|---|---|
| Physical body + actuators + sensors | Flybody (DeepMind/HHMI), via mujoco_menagerie | **Have it, running** (Phase 1) |
| Physics engine | MuJoCo | **Have it, running** |
| Biomechanical alt. body + full sensory sim | FlyGym/NeuroMechFly 2.x | Identified, not yet installed |
| Connectome data | FlyWire/Codex | **Blocked** — needs user's own Codex/CAVE account + a network path this sandbox doesn't have |
| LIF reference implementations | Eon `drosophila_brain_model_lif` (MIT), `fly-brain-full`, `fruit-fly-lab` | Identified, license-clear MIT one earmarked for close reading in Phase 2 |
| Motor decoding / brain-body bridge pattern | `fly-brain-full`'s description | Design pattern noted, code unverified |
| What we must build ourselves | Neural backend modularity, FlyWire ingestion glue, ablation harness, reproducibility manifests, dashboard | Not started beyond a Phase-2 LIF skeleton |
