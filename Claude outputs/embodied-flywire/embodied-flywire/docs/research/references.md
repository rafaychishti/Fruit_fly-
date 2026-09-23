# References

## Primary infrastructure
- FlyWire / Codex — https://codex.flywire.ai/ , FAQ: https://codex.flywire.ai/faq , download API: https://codex.flywire.ai/api/download
- Flybody (DeepMind + HHMI Janelia) — https://github.com/TuragaLab/flybody
- Flybody model via MuJoCo Menagerie — https://github.com/google-deepmind/mujoco_menagerie/tree/main/flybody
- FlyGym / NeuroMechFly — https://github.com/NeLy-EPFL/flygym , docs: https://neuromechfly.org/
- FlyGym legacy (1.x) — https://github.com/NeLy-EPFL/flygym-gymnasium
- NeuroMechFly scientific reference — Nature Methods (2024): https://www.nature.com/articles/s41592-024-02497-y
- MuJoCo — https://mujoco.org/ , https://github.com/google-deepmind/mujoco

## Research reference implementations (unverified claims — see ecosystem.md)
- Eon Systems PBC org — https://github.com/eonsystemspbc
  - `fly-brain` (GPL-2.0, 750★) — Brian2/Brian2CUDA/PyTorch/NEST GPU Drosophila brain emulation
  - `drosophila_brain_model_lif` (MIT) — LIF model building on Phil Shiu's original work
  - `flybody` (Apache-2.0) — fork of TuragaLab/flybody
- `rndlabsoy/fly-brain-full` (MIT) — https://github.com/rndlabsoy/fly-brain-full — whole-connectome LIF + NeuroMechFly v2 + MuJoCo, claims computational-individuality result
- `vaibhavkedarisetti/fruit-fly-lab` — https://github.com/vaibhavkedarisetti/fruit-fly-lab — FAFB v783 + LIF interactive whole-brain sim

## Cited scientific work (referenced by the above, not yet independently read)
- Shiu et al., 2024, "A leaky integrate-and-fire computational model based on the connectome of the entire adult *Drosophila* brain", cited by NeuroMechFly/FlyGym docs and by `fruit-fly-lab`'s README. Likely the direct scientific basis for most LIF-on-FlyWire reference implementations above — should be read in full before Phase 2/4 modeling decisions are finalized.

## How each reference was retrieved (given this sandbox's network constraints — see data-sources.md)
- Repo summaries: Anthropic `WebFetch` against the repo's GitHub root page.
- Actual model files (flybody MJCF + 85 mesh `.obj`s): individual `raw.githubusercontent.com` fetches, paths extracted directly from the MJCF's own `<mesh file="...">` references.
- Nothing below the level of "public repo summary" has been read for `fly-brain-full`, `fruit-fly-lab`, or the Eon Systems repos yet — that is the next reconnaissance step before Phase 2 modeling choices are locked in.
