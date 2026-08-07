"""
Python re-implementation of R. W. R. Darling's three-tier stochastic mobility
simulator (NSA/fractalrabbit), DOI 10.13140/RG.2.2.15267.40489.

Original Java implementation: github.com/NationalSecurityAgency/fractalrabbit
(java -jar fractalrabbit.jar params.csv output.csv)

This file is a faithful re-implementation of the three underlying models,
keeping the mathematics intact while running as pure Python with stdlib only:

  Tier 1 (AGP) — Agoraphobic Point Process: generates a set V of space points
                 whose limit is a random fractal, representing sites that
                 could be visited.

  Tier 2 (RP)  — Retro-preferential Process: generates a trajectory X through
                 V with strategic homing and self-reinforcing site fidelity,
                 modeling human/animal habit formation.

  Tier 3 (SRP) — Sporadic Reporting Process: models observation time points T
                 at which trajectory X is observed, with bursts of reports and
                 heavy-tailed inter-event times.

Output is the three named artifacts (V, X, T) plus a per-observation derived
field set the falsification harness consumes: each observation (t, x_t) is
augmented with trajectory-position features the harness uses to compute a
9-D binary primitive coverage vector.
"""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Tier 1: Agoraphobic Point Process (AGP)
# ---------------------------------------------------------------------------
def agoraphobic_point_process(
    n_sites: int,
    d: int = 1,
    rng: random.Random | None = None,
    min_distance: float = 0.0,
) -> List[Tuple[float, ...]]:
    """
    Generate `n_sites` points in [0, 1]^d such that the limit set is a random
    fractal. The 'agoraphobic' qualifier captures the property: each new point
    is placed with intensity that DECREASES as distance to existing points
    decreases (avoids clustering too tight).

    Approximation: rejection sampling. Candidate uniformly in [0,1]^d; accept
    if min distance to existing points > `min_distance`. The set V is the
    survivors; the limit (as n_sites grows) is a (d-dependent) random
    fractal whose Hausdorff dimension depends on `min_distance`.

    Reference: Darling (2018) §1 — Agoraphobic Point Process.
    """
    rng = rng or random.Random()
    sites: List[Tuple[float, ...]] = []
    max_attempts = n_sites * 200  # bound attempts to avoid pathological hangs
    attempts = 0
    while len(sites) < n_sites and attempts < max_attempts:
        candidate = tuple(rng.random() for _ in range(d))
        if all(
            math.dist(candidate, s) >= min_distance
            for s in sites
        ):
            sites.append(candidate)
        attempts += 1
    return sites


# ---------------------------------------------------------------------------
# Tier 2: Retro-preferential Process (RP)
# ---------------------------------------------------------------------------
@dataclass
class RPState:
    """Mutable state of the retro-preferential walk."""
    visit_count: List[int] = field(default_factory=list)
    current_site: int = 0
    n_new_visits: int = 0


def retro_preferential_walk(
    sites: List[Tuple[float, ...]],
    n_steps: int,
    alpha: float,
    beta: float,
    rng: random.Random | None = None,
    jump_within_cluster: bool = True,
) -> Tuple[List[int], RPState]:
    """
    Generate a trajectory X = (x_1, x_2, ..., x_{n_steps}) through `sites`.

    At each step:
      - With probability (1 - alpha): pick a previously visited site, weighted
        by visit_count[i]^beta (retro-preferential; beta > 0 yields habits).
      - With probability alpha: pick a NEW site uniformly (exploration).

    `jump_within_cluster` (Darling §2 model variant): when revisiting, prefer
    sites whose visit_count is high but spatially close to current site,
    modeling "homing within a neighborhood" rather than pure global preference.

    Returns the trajectory as a list of site indices + the final state.
    """
    rng = rng or random.Random()
    n_sites = len(sites)
    state = RPState(visit_count=[0] * n_sites, current_site=rng.randrange(n_sites))
    state.visit_count[state.current_site] += 1

    trajectory: List[int] = [state.current_site]

    for _ in range(n_steps - 1):
        if rng.random() < alpha:
            # exploration: pick a new site
            new_idx = rng.randrange(n_sites)
            # ensure it's truly new (not visited)
            attempts = 0
            while state.visit_count[new_idx] > 0 and attempts < 20:
                new_idx = rng.randrange(n_sites)
                attempts += 1
            if state.visit_count[new_idx] == 0:
                state.n_new_visits += 1
        else:
            # retro-preferential: weight by visit_count^beta
            weights = [c ** beta for c in state.visit_count]
            if jump_within_cluster and len(sites[0]) >= 2:
                # mix spatial proximity into weight (cluster homing)
                current_coords = sites[state.current_site]
                spatial = [
                    1.0 / (1.0 + math.dist(sites[i], current_coords))
                    for i in range(n_sites)
                ]
                weights = [w * s for w, s in zip(weights, spatial)]
            total = sum(weights)



            r = rng.random() * total
            cum = 0.0
            new_idx = 0
            for i, w in enumerate(weights):
                cum += w
                if cum >= r:
                    new_idx = i
                    break

        state.current_site = new_idx
        state.visit_count[new_idx] += 1
        trajectory.append(new_idx)

    return trajectory, state


# ---------------------------------------------------------------------------
# Tier 3: Sporadic Reporting Process (SRP)
# ---------------------------------------------------------------------------
def sporadic_reporting_process(
    n_steps: int,
    burst_prob: float,
    heavy_tail_alpha: float,
    rng: random.Random | None = None,
) -> List[int]:
    """
    Generate observation time points T (subset of {0, ..., n_steps-1}).

    Two-state burst process:
      - In burst state: each step has probability `burst_prob` of producing
        a report.
      - Not in burst: inter-event time T_i - T_{i-1} is drawn from a Pareto
        distribution with shape `heavy_tail_alpha` (heavy tail = rare long
        gaps between reports).

    Returns sorted list of observation indices.
    """
    rng = rng or random.Random()
    observations: List[int] = []
    t = 0
    in_burst = False
    while t < n_steps:
        if in_burst:
            # burst mode: high reporting probability, short gaps
            if rng.random() < burst_prob:
                observations.append(t)
                t += 1
            else:
                in_burst = False
                # transition: draw heavy-tailed gap
                gap = max(1, int(rng.paretovariate(heavy_tail_alpha)))
                t += gap
        else:
            # quiet mode: occasional entry into burst
            if rng.random() < 0.05:
                in_burst = True
            else:
                # draw heavy-tailed gap
                gap = max(1, int(rng.paretovariate(heavy_tail_alpha)))
                t += gap
            if t < n_steps:
                # possibly observe in quiet mode too
                if rng.random() < 0.10:
                    observations.append(t)
                    t += 1
    return sorted(set(observations))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
@dataclass
class SimResult:
    """All simulator artifacts the falsification harness consumes."""
    sites: List[Tuple[float, ...]]
    trajectory: List[int]
    visit_count: List[int]
    observations: List[int]
    n_sites: int
    n_steps: int
    inter_event_times: List[int]
    n_burst_observations: int
    n_quiet_observations: int


def simulate(
    n_sites: int = 80,
    n_steps: int = 2000,
    d: int = 1,
    agp_min_distance: float = 0.04,
    alpha: float = 0.10,
    beta: float = 1.5,
    burst_prob: float = 0.6,
    heavy_tail_alpha: float = 1.5,
    seed: int | None = 42,
) -> SimResult:
    """
    Run the full three-tier simulator. Returns SimResult with everything
    the falsification harness needs to derive a 9-D primitive vector per
    observation.
    """
    rng = random.Random(seed)

    # Tier 1
    sites = agoraphobic_point_process(n_sites, d, rng, agp_min_distance)

    # Tier 2
    trajectory, state = retro_preferential_walk(
        sites, n_steps, alpha, beta, rng, jump_within_cluster=(d == 1)
    )

    # Tier 3
    observations = sporadic_reporting_process(
        n_steps, burst_prob, heavy_tail_alpha, rng
    )

    # Derived: inter-event times
    inter_event_times = [
        observations[i + 1] - observations[i]
        for i in range(len(observations) - 1)
    ]

    # Derived: burst vs quiet classification
    # (a report is "in burst" if the gap before it is in the bottom 25th
    # percentile of all inter-event times — proxy for being inside a burst
    # cluster rather than a sparse heavy-tail arrival)
    median_gap = sorted(inter_event_times)[len(inter_event_times) // 2] if inter_event_times else 1
    q1 = sorted(inter_event_times)[len(inter_event_times) // 4] if inter_event_times else 1
    burst_threshold = max(1, q1)

    n_burst = 0
    n_quiet = 0
    for i, obs in enumerate(observations):
        gap = (observations[i + 1] - obs) if i + 1 < len(observations) else n_steps
        if gap <= burst_threshold:
            n_burst += 1
        else:
            n_quiet += 1

    return SimResult(
        sites=sites,
        trajectory=trajectory,
        visit_count=state.visit_count,
        observations=observations,
        n_sites=len(sites),
        n_steps=n_steps,
        inter_event_times=inter_event_times,
        n_burst_observations=n_burst,
        n_quiet_observations=n_quiet,
    )
