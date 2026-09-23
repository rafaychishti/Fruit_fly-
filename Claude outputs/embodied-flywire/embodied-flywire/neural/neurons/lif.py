"""Leaky Integrate-and-Fire neuron population, vectorized (NumPy backend).

Explicitly NOT claimed to be biologically sufficient (per project brief
section 2/9) -- this is the simplest validated starting point, made
swappable so other models (conductance-based, etc.) can be dropped in
later without touching the connectivity or dynamics-loop code.
"""
from dataclasses import dataclass
import numpy as np


@dataclass
class LIFParams:
    tau_m_ms: float = 20.0       # membrane time constant
    v_rest: float = 0.0
    v_reset: float = 0.0
    v_threshold: float = 1.0
    refractory_ms: float = 2.0
    dt_ms: float = 0.2           # 5 kHz, matching the 0.2ms step several
                                  # reference implementations use (see
                                  # docs/research/ecosystem.md, fly-brain-full)


class LIFPopulation:
    """A population of N leaky integrate-and-fire neurons with no
    intrinsic connectivity of its own -- synaptic input is injected from
    outside each step via `inject_current`.
    """

    def __init__(self, n: int, params: LIFParams, seed: int = 0):
        self.n = n
        self.p = params
        rng = np.random.default_rng(seed)
        self.v = np.full(n, params.v_rest, dtype=np.float64)
        # small heterogeneity in resting potential so a synchronous input
        # doesn't produce perfectly synchronous spikes -- documented, not
        # hidden: this is a deliberate, disclosed approximation.
        self.v += rng.normal(0, 0.01, size=n)
        self.refractory_until_ms = np.zeros(n, dtype=np.float64)
        self.t_ms = 0.0
        self.spike_history: list[tuple[float, np.ndarray]] = []

    def step(self, input_current: np.ndarray) -> np.ndarray:
        """Advance one dt. Returns a boolean spike mask of shape (n,)."""
        p = self.p
        active = self.t_ms >= self.refractory_until_ms
        dv = (-(self.v - p.v_rest) / p.tau_m_ms + input_current) * p.dt_ms
        self.v = np.where(active, self.v + dv, self.v)

        spiked = active & (self.v >= p.v_threshold)
        self.v = np.where(spiked, p.v_reset, self.v)
        self.refractory_until_ms = np.where(
            spiked, self.t_ms + p.dt_ms + p.refractory_ms, self.refractory_until_ms
        )
        self.t_ms += p.dt_ms
        return spiked
