"""Synthetic sparse weighted connectivity generator.

Purpose: give Phase 2 something deterministic and FlyWire-shaped (signed
weights, sparse, directed) to test the dynamics loop against, WITHOUT
depending on any real connectome data (which is currently unreachable from
this sandbox -- see docs/research/data-sources.md). This is explicitly a
placeholder to be replaced by real ingested connectivity in Phase 3/4, not
a model of anything biological.
"""
import numpy as np
from scipy import sparse


def make_random_sparse_signed(
    n: int,
    p_connect: float,
    frac_excitatory: float = 0.8,
    weight_scale: float = 0.15,
    seed: int = 0,
) -> sparse.csr_matrix:
    """Returns an (n, n) sparse CSR weight matrix W where W[i, j] is the
    synaptic weight from presynaptic neuron j to postsynaptic neuron i.
    No self-connections. Excitatory weights positive, inhibitory negative,
    consistent per-source-neuron (a neuron's outgoing synapses are all one
    sign) -- mirroring real connectomes' neurotransmitter-determined sign
    convention (see fly-brain-full's stated design in ecosystem.md),
    though the actual assignment here is uniform-random, not biological.
    """
    rng = np.random.default_rng(seed)
    mask = rng.random((n, n)) < p_connect
    np.fill_diagonal(mask, False)

    is_excitatory_source = rng.random(n) < frac_excitatory
    sign_per_source = np.where(is_excitatory_source, 1.0, -1.0)

    magnitude = rng.exponential(scale=weight_scale, size=(n, n))
    signed = magnitude * sign_per_source[None, :]  # broadcast over columns (source j)
    w = np.where(mask, signed, 0.0)
    return sparse.csr_matrix(w)
