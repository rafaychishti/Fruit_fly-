#!/usr/bin/env python3
"""
Phase 1 — Physical fly baseline.

Loads the real DeepMind/HHMI "flybody" MJCF model (sourced from
google-deepmind/mujoco_menagerie, Apache-2.0) into MuJoCo, reports its
structure (joints/actuators/sensors/bodies), runs a small set of scripted
control experiments, benchmarks simulation speed, and optionally renders
a video.

IMPORTANT — scientific honesty (see docs/assumptions.md):
Every controller in this script is EXPLICITLY PROGRAMMED. Nothing here is
claimed to be emergent. This script exists only to establish that the body
model itself is mechanically sound and controllable, before any neural
circuit (biological or otherwise) is connected to it in later phases.

Usage:
    python3 scripts/run/run_body.py --mode standing --duration 2.0
    python3 scripts/run/run_body.py --mode random --duration 2.0 --record out.mp4
    python3 scripts/run/run_body.py --mode tripod --duration 3.0 --record out.mp4
"""
import argparse
import json
import os
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "osmesa")

import numpy as np
import mujoco

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = REPO_ROOT / "embodiment" / "flybody" / "fruitfly.xml"


def inspect_model(m: mujoco.MjModel) -> dict:
    def names(obj_type, n):
        return [mujoco.mj_id2name(m, obj_type, i) for i in range(n)]

    report = {
        "nq_generalized_coords": m.nq,
        "nv_velocity_dof": m.nv,
        "nu_actuators": m.nu,
        "njnt_joints": m.njnt,
        "nbody_bodies": m.nbody,
        "nsensor": m.nsensor,
        "timestep_s": float(m.opt.timestep),
        "gravity": m.opt.gravity.tolist(),
        "actuator_names": names(mujoco.mjtObj.mjOBJ_ACTUATOR, m.nu),
        "joint_names": names(mujoco.mjtObj.mjOBJ_JOINT, m.njnt),
        "body_names": names(mujoco.mjtObj.mjOBJ_BODY, m.nbody),
        "sensor_names": names(mujoco.mjtObj.mjOBJ_SENSOR, m.nsensor),
    }
    return report


def make_controller(mode: str, m: mujoco.MjModel):
    """Returns a function (data, t) -> None that sets data.ctrl in place.
    Every branch here is an explicitly programmed heuristic — see module
    docstring. None of it is a claim about biological plausibility.
    """
    rng = np.random.default_rng(0)
    act_names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]

    if mode == "standing":
        def ctrl(data, t):
            data.ctrl[:] = 0.0
        return ctrl

    if mode == "random":
        def ctrl(data, t):
            data.ctrl[:] = rng.normal(0.0, 0.05, size=m.nu)
        return ctrl

    if mode == "tripod":
        # Crude alternating-tripod-like drive on the three "power" leg DOFs
        # per leg (coxa lift, femur, tibia). Legs T1_left/T2_right/T3_left
        # move in antiphase with T1_right/T2_left/T3_right. This is a hand
        # -engineered oscillator, included ONLY to show the body can produce
        # leg-cycling motion — it is not a locomotion controller in any
        # serious sense and is not expected to yield stable forward walking.
        groups = {
            "A": ["T1_left", "T2_right", "T3_left"],
            "B": ["T1_right", "T2_left", "T3_right"],
        }
        dof_kinds = ["coxa_{}", "femur_{}", "tibia_{}"]
        idx = {name: i for i, name in enumerate(act_names)}
        freq_hz = 4.0

        def ctrl(data, t):
            data.ctrl[:] = 0.0
            phase_a = np.sin(2 * np.pi * freq_hz * t)
            phase_b = -phase_a
            for label, legs, phase in [("A", groups["A"], phase_a), ("B", groups["B"], phase_b)]:
                for leg in legs:
                    for kind in dof_kinds:
                        name = kind.format(leg)
                        if name in idx:
                            data.ctrl[idx[name]] = 0.15 * phase
            # keep claws adhered so legs can push against the ground
            for name in act_names:
                if name.startswith("adhere_claw"):
                    data.ctrl[idx[name]] = 1.0
        return ctrl

    raise ValueError(f"unknown mode: {mode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["standing", "random", "tripod"], default="standing")
    ap.add_argument("--duration", type=float, default=2.0, help="sim seconds")
    ap.add_argument("--record", type=str, default=None, help="output mp4 path")
    ap.add_argument("--record-fps", type=float, default=30.0)
    ap.add_argument("--camera", type=str, default="track1",
                     help="named camera from the MJCF to render from (e.g. track1/hero/side/eye_left)")
    ap.add_argument("--out-dir", type=str, default=str(REPO_ROOT / "experiments" / "001_body_baseline"))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    m = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    d = mujoco.MjData(m)

    report = inspect_model(m)
    with open(out_dir / "inspection_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"[inspect] nq={report['nq_generalized_coords']} nv={report['nv_velocity_dof']} "
          f"nu={report['nu_actuators']} njnt={report['njnt_joints']} "
          f"nbody={report['nbody_bodies']} nsensor={report['nsensor']} "
          f"timestep={report['timestep_s']}s")

    ctrl_fn = make_controller(args.mode, m)

    renderer = None
    frames = []
    frame_every = None
    if args.record:
        renderer = mujoco.Renderer(m, height=480, width=640)
        frame_every = max(1, int(round(1.0 / (args.record_fps * m.opt.timestep))))

    n_steps = int(round(args.duration / m.opt.timestep))
    mujoco.mj_resetData(m, d)

    t0 = time.perf_counter()
    for step in range(n_steps):
        t = step * m.opt.timestep
        ctrl_fn(d, t)
        mujoco.mj_step(m, d)
        if renderer is not None and step % frame_every == 0:
            renderer.update_scene(d, camera=args.camera)
            frames.append(renderer.render().copy())
    wall_s = time.perf_counter() - t0

    real_time_factor = args.duration / wall_s if wall_s > 0 else float("inf")
    benchmark = {
        "mode": args.mode,
        "n_steps": n_steps,
        "sim_duration_s": args.duration,
        "wall_clock_s": wall_s,
        "steps_per_sec": n_steps / wall_s if wall_s > 0 else float("inf"),
        "real_time_factor": real_time_factor,
        "final_qpos_sample": d.qpos[:6].tolist(),
        "final_body_com": mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, 1),
        "nan_or_inf_detected": bool(np.any(~np.isfinite(d.qpos)) or np.any(~np.isfinite(d.qvel))),
    }
    with open(out_dir / f"benchmark_{args.mode}.json", "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"[benchmark] {n_steps} steps in {wall_s:.2f}s wall-clock "
          f"({benchmark['steps_per_sec']:.0f} steps/s, "
          f"real-time factor {real_time_factor:.3f}x, "
          f"finite={not benchmark['nan_or_inf_detected']})")

    if args.record and frames:
        import imageio
        imageio.mimwrite(args.record, frames, fps=args.record_fps, codec="libx264", quality=7)
        print(f"[render] wrote {len(frames)} frames to {args.record}")


if __name__ == "__main__":
    main()
