"""Phase 2 exit-criterion script: simulate a small synthetic LIF network
correctly and deterministically, and prove it (same seed -> identical
spike train, bit for bit).

This has no connection to any real connectome. It exists to validate the
dynamics-loop machinery (neurons/connectivity/backends wiring) before
Phase 3 swaps in real FlyWire-derived connectivity.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from neural.neurons.lif import LIFPopulation, LIFParams
from neural.connectivity.random_sparse import make_random_sparse_signed


def run(n: int, steps: int, seed: int, external_drive: float):
    params = LIFParams()
    pop = LIFPopulation(n, params, seed=seed)
    weights = make_random_sparse_signed(n, p_connect=0.05, seed=seed)

    rng = np.random.default_rng(seed + 1)
    spike_raster = np.zeros((steps, n), dtype=bool)
    recent_spikes = np.zeros(n, dtype=np.float64)

    t0 = time.perf_counter()
    for t in range(steps):
        # external stochastic drive to a random 10% of neurons each step,
        # plus recurrent input from last step's spikes through `weights`.
        external = (rng.random(n) < 0.1).astype(np.float64) * external_drive
        recurrent = weights.dot(recent_spikes)
        input_current = external + recurrent
        spikes = pop.step(input_current)
        spike_raster[t] = spikes
        recent_spikes = spikes.astype(np.float64)
    wall_s = time.perf_counter() - t0

    return spike_raster, wall_s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--steps", type=int, default=5000)  # 5000 * 0.2ms = 1s
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--external-drive", type=float, default=0.6)
    ap.add_argument("--out-dir", type=str,
                     default=str(Path(__file__).resolve().parents[2] / "experiments" / "002_neural_baseline"))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raster, wall_s = run(args.n, args.steps, args.seed, args.external_drive)
    raster2, _ = run(args.n, args.steps, args.seed, args.external_drive)
    deterministic = bool(np.array_equal(raster, raster2))

    total_spikes = int(raster.sum())
    firing_rate_hz = total_spikes / args.n / (args.steps * LIFParamsDt()) if args.steps else 0.0

    digest = hashlib.sha256(raster.tobytes()).hexdigest()[:16]

    result = {
        "n_neurons": args.n,
        "n_steps": args.steps,
        "sim_duration_s": args.steps * LIFParamsDt(),
        "seed": args.seed,
        "wall_clock_s": wall_s,
        "steps_per_sec": args.steps / wall_s if wall_s > 0 else float("inf"),
        "total_spikes": total_spikes,
        "mean_firing_rate_hz": firing_rate_hz,
        "deterministic_rerun_identical": deterministic,
        "raster_sha256_16": digest,
    }
    with open(out_dir / f"result_seed{args.seed}.json", "w") as f:
        json.dump(result, f, indent=2)
    np.save(out_dir / f"raster_seed{args.seed}.npy", raster)

    print(json.dumps(result, indent=2))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 4))
        ts, ns = np.nonzero(raster)
        ax.scatter(ts * LIFParamsDt(), ns, s=1, c="black")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("neuron index")
        ax.set_title(f"Synthetic LIF network raster (n={args.n}, seed={args.seed}) -- NOT real connectome data")
        fig.tight_layout()
        fig.savefig(out_dir / f"raster_seed{args.seed}.png", dpi=120)
        print(f"[plot] wrote {out_dir / f'raster_seed{args.seed}.png'}")
    except Exception as e:
        print(f"[plot] skipped ({e})")


def LIFParamsDt():
    return LIFParams().dt_ms / 1000.0


if __name__ == "__main__":
    main()
