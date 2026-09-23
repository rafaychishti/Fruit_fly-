# Data sources and access constraints

This file records exactly what could and could not be reached from the
development sandbox used to bootstrap this repo (2026-09-23), so the next
session doesn't have to rediscover it. "This sandbox" = a 2-vCPU / 7.8 GB
RAM / no-GPU cloud container with an organization-managed egress proxy.

## Network reachability, tested directly

| Host | Result | Notes |
|---|---|---|
| `codex.flywire.ai` | **403 at the proxy** (`connect_rejected`, "policy denial") | Blocked before any FlyWire authentication is even attempted. Not a credentials problem — a network policy one. |
| `github.com`, `api.github.com`, `codeload.github.com` | **403** | Blocks browsing, the REST API, git clone over HTTPS, and tarball downloads. |
| `raw.githubusercontent.com` | **200, works** | Individual file fetches by exact path work fine. This is how we retrieved the flybody MJCF + all 85 mesh files (see below) — one file per request, no directory listing available this way. |
| `data.jsdelivr.com` (GitHub mirror/API) | **403** | Not a usable workaround for directory listing. |
| `pypi.org`, `files.pythonhosted.org` | **200**, direct (in the proxy's no-proxy allowlist) | `pip install` works normally. |
| `archive.ubuntu.com` (apt) | **200** | `apt-get install` works for system packages (used for `libosmesa6-dev` etc.). |
| `download.docker.com` | 403 | Irrelevant to this project, noted only because `apt-get update` surfaced it. |

Anthropic's own `WebFetch`/`WebSearch` tools reach GitHub pages and (some)
API-shaped URLs (e.g. `github.com/OWNER/REPO` root pages) that raw `curl`/
`git` cannot, because they run over Anthropic's infrastructure rather than
this sandbox's egress proxy. They are subject to the target site's
`robots.txt`, though — e.g. GitHub's `.../tree/<branch>/<path>` directory
pages were disallowed. Plain `github.com/OWNER/REPO` and
`raw.githubusercontent.com/...` file fetches worked.

## What this means per phase

- **FlyWire/Codex data (Phase 3): blocked from this sandbox regardless of
  credentials.** Getting real connectome data into this project requires
  either (a) the user downloading it themselves outside this sandbox and
  uploading the resulting file(s), or (b) running the ingestion step in an
  environment whose egress policy allows `codex.flywire.ai` and the FlyWire
  authentication flow. Recommend (a): the files involved (parquet/CSV
  connectivity tables for a *small* circuit, per the brief's own "don't
  ingest everything" instruction) should be small enough to upload directly.
- **GitHub repos we can't `git clone` (Eon Systems repos, `fly-brain-full`,
  `fruit-fly-lab`, `flygym`, `TuragaLab/flybody` itself):** readable
  file-by-file via `raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>`
  when we know the exact path, and summarizable via `WebFetch` on the repo's
  root page. Full clones (needed e.g. for `fly-brain-full`'s 270 MB Git-LFS
  connectome payload) are not currently possible from here.
- **mujoco_menagerie's `flybody/` (Phase 1): fully obtained.** We parsed
  `fruitfly.xml`'s own `<mesh file="...">` / `<texture file="...">`
  references to get an exact file list (no guessing), then fetched all 85
  referenced `.obj` files individually over `raw.githubusercontent.com`.
  134 MB total, all 85 succeeded, MuJoCo 3.14.0 compiles the result cleanly.
  This is the general workaround pattern for "I need files from a GitHub
  repo I can't clone" in this environment: get one file that lists its own
  dependencies (a lockfile, an MJCF, a manifest), then fetch each dependency
  by exact raw path.
- **GPU-dependent work (FlyGym 2.x's MJWarp backend, `fly-brain-full`'s
  PyTorch-GPU LIF at 5 kHz over 138k neurons, Phase 10 scaling benchmarks):
  not runnable in this sandbox at all** — no GPU is present
  (`nvidia-smi`: not found). CPU-only MuJoCo stepping benchmarked at
  ~600-1000 steps/s (real-time factor ≈ 0.06-0.10x) on this hardware; see
  `experiments/001_body_baseline/`. A small (≤ few thousand neuron) LIF
  network should still be tractable on CPU for Phase 2-4; whole-connectome
  work (Phase 10-11) will need GPU hardware this sandbox doesn't have.

## Licensing flags to carry forward

- Flybody / mujoco_menagerie flybody: **Apache-2.0** — permissive, fine to
  vendor into this repo (done, in `embodiment/flybody/`).
- FlyGym/NeuroMechFly: **Apache-2.0**.
- MuJoCo: **Apache-2.0**.
- Eon Systems `fly-brain`: **GPL-2.0** — copyleft; read for ideas, be
  deliberate before copying code into a differently-licensed repo.
- Eon Systems `drosophila_brain_model_lif`: **MIT** — permissive, best
  candidate for a close-reading reference in Phase 2.
- `fly-brain-full`: **MIT** (code) — but the *connectome data it bundles* is
  still subject to FlyWire's own terms regardless of the wrapping repo's
  license.
- **FlyWire data itself: CC BY-NC-SA 4.0** (attribution, non-commercial,
  share-alike) per `fruit-fly-lab`'s stated terms. This is the constraint
  that actually matters for Phase 3 onward, independent of which repo we
  get the data through. Re-verify the exact terms on Codex's own download
  portal before ingesting anything, since our fetch of the Codex FAQ
  explicitly deferred citation/license terms to that portal page.
