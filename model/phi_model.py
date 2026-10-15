"""
Phi: a controllable threshold model of a self-sustaining absorbed state.

Reference implementation of the equation behind the interactive simulator
(simulator/index.html) and the meditation protocol (protocol/protocol.md).

    dPhi/dt = (alpha*I - beta)*Phi + kappa*Phi^2 - gamma*Phi^3 + D*lap(Phi) + s + eta*xi

Phi(x, t) is a latent variable: the intensity of the absorbed state at
location x on a two-dimensional body map. It is not claimed to be a physical
field. Each term is mapped to something the practitioner trains or measures:

    alpha   coupling: how strongly attention engages body signals (interoception)
    I       richness: how many body regions are bound into one state
    beta    noise: mind-wandering and arousal noise (the session "gate")
    kappa   self-feedback: the pleasure-attention loop (attention strengthens a
            pleasant sensation, the sensation holds attention)
    gamma   saturation: the ceiling that caps the state at a plateau
    D       spread: how the state diffuses across the body map
    s       steady drive: a generated spark (goodwill, recalled joy)
    eta     fluctuations: spontaneous sensations (a noticed spark)

Outside the held region the net gain is r_out < 0 (unattended regions decay).

Inside the held region, with r = alpha*I - beta, the reaction terms
f(Phi) = r*Phi + kappa*Phi^2 - gamma*Phi^3 give three regimes:

    r < -kappa^2/(4*gamma)            only rest exists        -> no seed possible
    -kappa^2/(4*gamma) < r < 0        rest and seed coexist   -> needs a spark
    r > 0                             rest is unstable        -> any fluctuation ignites

The middle window is what makes the state controllable: entry needs a spark
above the threshold, gamma caps the plateau, and exit is a deliberate move of r
below the fold at -kappa^2/(4*gamma).

Requires numpy. Dimensionless units throughout.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import numpy as np


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class Params:
    alpha: float = 0.7      # coupling
    I: float = 1.0          # richness
    beta: float = 1.5       # noise
    kappa: float = 2.0      # self-feedback
    gamma: float = 1.0      # saturation (ceiling)
    D: float = 1.0          # spread
    r_out: float = -1.5     # net gain outside the held region
    s: float = 0.0          # steady drive inside the held region
    eta: float = 0.0        # fluctuation strength

    @property
    def r(self) -> float:
        """Net gain inside the held region."""
        return self.alpha * self.I - self.beta

    def with_(self, **kw) -> "Params":
        return replace(self, **kw)


# ---------------------------------------------------------------------------
# Reaction terms and their fixed points
# ---------------------------------------------------------------------------

def reaction(phi, r, kappa=2.0, gamma=1.0, s=0.0):
    """Local growth rate f(Phi) = r*Phi + kappa*Phi^2 - gamma*Phi^3 + s."""
    return r * phi + kappa * phi**2 - gamma * phi**3 + s


def reaction_slope(phi, r, kappa=2.0, gamma=1.0):
    return r + 2 * kappa * phi - 3 * gamma * phi**2


def fixed_points(r, kappa=2.0, gamma=1.0, s=0.0):
    """
    Non-negative fixed points of the reaction terms, classified.

    Returns a dict with keys 'rest', 'threshold', 'seed' (float or None).
    Phi is an intensity, so negative roots are ignored.
    """
    if gamma == 0:
        # As written, without saturation: r*Phi + kappa*Phi^2 + s = 0
        roots = np.roots([kappa, r, s]) if kappa != 0 else np.array([-s / r])
    else:
        roots = np.roots([-gamma, kappa, r, s])
    real = sorted(float(z.real) for z in np.atleast_1d(roots)
                  if abs(z.imag) < 1e-9 and z.real >= -1e-9)
    if s == 0 and (not real or abs(real[0]) > 1e-9):
        real = sorted(set([0.0] + real))
    pts = [(x, reaction_slope(x, r, kappa, gamma) < 0) for x in real]
    stable = [x for x, st in pts if st]
    unstable = [x for x, st in pts if not st]
    out = {"rest": None, "threshold": None, "seed": None}
    if stable and stable[0] <= (unstable[0] if unstable else np.inf):
        out["rest"] = stable[0]
    if unstable:
        out["threshold"] = unstable[0]
    hi = [x for x in stable if out["threshold"] is not None and x > out["threshold"]]
    if hi:
        out["seed"] = hi[-1]
    elif stable and out["rest"] is None:
        out["seed"] = stable[-1]
    return out


def fold_gain(kappa=2.0, gamma=1.0):
    """Net gain below which no seed level exists (saddle-node / exit point)."""
    return -kappa**2 / (4 * gamma)


def regime(r, kappa=2.0, gamma=1.0):
    if gamma > 0 and r < fold_gain(kappa, gamma):
        return "no seed"
    if r < 0:
        return "bistable"
    return "rest unstable"


# ---------------------------------------------------------------------------
# Held regions on the body map (equal area for every shape)
# ---------------------------------------------------------------------------

def held_region(n=120, radius=14, shape="round"):
    """Boolean mask of the held region. Shapes keep the same area."""
    y, x = np.mgrid[0:n, 0:n]
    c = n / 2
    dx, dy = x - c, y - c
    if shape == "round":
        m = dx**2 + dy**2 < radius**2
    elif shape == "stretched":
        a, b = radius * 2.2, radius / 2.2
        m = (dx / a) ** 2 + (dy / b) ** 2 < 1
    elif shape == "scattered":
        rr = radius / np.sqrt(5)
        off = 0.28 * n
        m = np.zeros_like(dx, dtype=bool)
        for ox, oy in [(0, 0), (-off, -off), (off, -off), (-off, off), (off, off)]:
            m |= (dx - ox) ** 2 + (dy - oy) ** 2 < rr**2
    else:
        raise ValueError(shape)
    m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = False
    return m


def disc(n, radius):
    y, x = np.mgrid[0:n, 0:n]
    return (x - n / 2) ** 2 + (y - n / 2) ** 2 < radius**2


# ---------------------------------------------------------------------------
# Spatial simulation
# ---------------------------------------------------------------------------

def laplacian(P):
    """Five-point Laplacian with zero-flux (Neumann) edges."""
    Pp = np.pad(P, 1, mode="edge")
    return Pp[:-2, 1:-1] + Pp[2:, 1:-1] + Pp[1:-1, :-2] + Pp[1:-1, 2:] - 4 * P


def simulate(p: Params, mask, phi0, T=200.0, dt=0.1, rng=None, record_every=None,
             r_schedule=None):
    """
    Integrate the field with explicit Euler.

    p           Params
    mask        boolean held region
    phi0        initial field (array, same shape as mask)
    r_schedule  optional function t -> net gain inside the region (overrides p.r)
    Returns (final field, times, mean Phi inside the region over time).
    """
    rng = np.random.default_rng(rng)
    P = phi0.astype(float).copy()
    R = np.where(mask, p.r, p.r_out)
    S = np.where(mask, p.s, 0.0)
    n_steps = int(round(T / dt))
    rec = record_every or max(1, n_steps // 400)
    ts, ins = [], []
    noise_amp = p.eta * np.sqrt(dt)
    for k in range(n_steps):
        t = k * dt
        if r_schedule is not None:
            R = np.where(mask, r_schedule(t), p.r_out)
        f = R * P + p.kappa * P**2 - p.gamma * P**3 + S
        P = P + dt * (f + p.D * laplacian(P))
        if noise_amp:
            P = P + noise_amp * rng.standard_normal(P.shape)
        np.clip(P, -2.0, 50.0, out=P)
        if k % rec == 0:
            ts.append(t)
            ins.append(float(P[mask].mean()))
    return P, np.array(ts), np.array(ins)


def outcome(p: Params, mask, phi0, T=200.0, dt=0.1, rng=None):
    """
    Mean Phi inside the held region at the end, and whether the state held,
    meaning it did not drain back to rest.
    """
    P, _, ins = simulate(p, mask, phi0, T=T, dt=dt, rng=rng)
    rest = fixed_points(p.r, p.kappa, p.gamma, p.s)["rest"] or 0.0
    held = ins[-1] > rest + 0.1
    return float(ins[-1]), bool(held)


# ---------------------------------------------------------------------------
# Mean-field (single-region) dynamics, for sessions and early warnings
# ---------------------------------------------------------------------------

def simulate_mean_field(r_of_t, kappa=2.0, gamma=1.0, eta=0.0, phi0=0.0,
                        T=400.0, dt=0.01, kick=None, rng=None):
    """
    dPhi/dt = r(t)*Phi + kappa*Phi^2 - gamma*Phi^3 + eta*xi

    kick: optional list of (time, amount) pulses added to Phi (a spark).
    """
    rng = np.random.default_rng(rng)
    n = int(round(T / dt))
    t = np.arange(n) * dt
    phi = np.empty(n)
    x = phi0
    kicks = sorted(kick or [])
    ki = 0
    sq = eta * np.sqrt(dt)
    for k in range(n):
        while ki < len(kicks) and t[k] >= kicks[ki][0]:
            x += kicks[ki][1]
            ki += 1
        r = r_of_t(t[k])
        x = x + dt * (r * x + kappa * x**2 - gamma * x**3)
        if sq:
            x += sq * rng.standard_normal()
        phi[k] = x
    return t, phi


def early_warning(series, window):
    """Rolling variance and lag-1 autocorrelation over a sliding window."""
    n = len(series)
    var = np.full(n, np.nan)
    ac1 = np.full(n, np.nan)
    for i in range(window, n):
        w = series[i - window:i]
        w = w - np.polyval(np.polyfit(np.arange(window), w, 1), np.arange(window))
        var[i] = w.var()
        a, b = w[:-1], w[1:]
        sa, sb = a.std(), b.std()
        ac1[i] = ((a - a.mean()) * (b - b.mean())).mean() / (sa * sb) if sa > 0 and sb > 0 else np.nan
    return var, ac1


def onset_time(t, phi, level):
    idx = np.argmax(phi > level)
    return t[idx] if phi[idx] > level else None


if __name__ == "__main__":
    p = Params()
    fp = fixed_points(p.r, p.kappa, p.gamma)
    print(f"net gain r = {p.r:+.2f}, regime: {regime(p.r, p.kappa, p.gamma)}")
    print(f"rest = {fp['rest']}, threshold = {fp['threshold']:.3f}, seed = {fp['seed']:.3f}")
    print(f"exit (fold) at r = {fold_gain(p.kappa, p.gamma):.2f}")
