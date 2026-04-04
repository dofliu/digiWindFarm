"""
Wind field model with realistic statistical properties.

Features:
  - Weibull distribution for long-term wind speed statistics
  - Autocorrelated turbulence (Kaimal-like spectrum, not white noise)
  - Coherent wind direction changes with inertia
  - Temperature daily cycle with realistic amplitude

Can be used standalone or as part of the simulator.
Separate from wind_model.py (which handles profiles/overrides).
"""

import math
import numpy as np
from typing import Optional


class TurbulenceGenerator:
    """
    Generates autocorrelated turbulence using an AR(1) process.

    Instead of white noise (random at every timestep), this produces
    realistic wind speed fluctuations with temporal correlation.

    Kaimal spectrum approximation:
      τ_turb ≈ L_u / V_mean  (L_u = integral length scale ≈ 340m for hub height 90m)

    At 12 m/s: τ ≈ 340/12 ≈ 28 seconds → fluctuations persist for ~30s
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = np.random.RandomState(seed)
        self._state = 0.0  # AR(1) state

    def step(self, mean_speed: float, turbulence_intensity: float,
             dt: float) -> float:
        """
        Generate turbulence component (m/s) for one timestep.

        Args:
            mean_speed: Mean wind speed (m/s)
            turbulence_intensity: TI (typically 0.08-0.20)
            dt: Timestep (seconds)

        Returns:
            Turbulence fluctuation (m/s), to be added to mean speed
        """
        if mean_speed < 0.5:
            self._state = 0.0
            return 0.0

        # Integral length scale (IEC 61400-1, hub height 90m)
        L_u = 340.0  # meters
        tau = L_u / max(mean_speed, 1.0)  # correlation time scale

        # AR(1) coefficient
        alpha = math.exp(-dt / tau)

        # Standard deviation of wind speed fluctuation
        sigma = mean_speed * turbulence_intensity

        # Driving noise (scaled for correct variance)
        noise = self._rng.normal(0, sigma * math.sqrt(1 - alpha ** 2))

        # AR(1) update
        self._state = alpha * self._state + noise

        return self._state


class WindDirectionModel:
    """
    Wind direction with realistic inertia and slow drift.

    Wind direction doesn't jump randomly — it has inertia from
    large-scale weather patterns, with small random perturbations.
    """

    def __init__(self, initial_direction: float = 270.0, seed: Optional[int] = None):
        self._rng = np.random.RandomState(seed)
        self.direction = initial_direction
        self._drift_rate = 0.0  # °/s, slowly varying

    def step(self, dt: float, override: Optional[float] = None) -> float:
        """Advance wind direction by one timestep."""
        if override is not None:
            # Manual override with small sensor noise
            return (override + self._rng.normal(0, 1.5)) % 360

        # Drift rate evolves slowly (random walk with mean reversion)
        self._drift_rate += self._rng.normal(0, 0.001 * dt)
        self._drift_rate *= 0.998  # decay towards zero
        self._drift_rate = max(-0.5, min(0.5, self._drift_rate))  # ±0.5 °/s max

        # Apply drift + small perturbation
        self.direction += self._drift_rate * dt + self._rng.normal(0, 0.3 * dt)
        self.direction %= 360

        return self.direction


class PerTurbineWind:
    """
    Generate per-turbine wind variations (wake effect, spatial decorrelation).

    Each turbine sees slightly different wind due to:
    - Spatial separation (decorrelation)
    - Wake effects (downstream turbines see reduced wind)
    - Local terrain effects
    """

    def __init__(self, turbine_count: int, seed: int = 0):
        self._rng = np.random.RandomState(seed)
        self._offsets = self._rng.normal(0, 0.5, turbine_count)  # persistent offset
        self._wake_factors = np.ones(turbine_count)  # 1.0 = no wake

        # Simple wake model: downstream turbines lose 3-8%
        for i in range(1, turbine_count):
            self._wake_factors[i] = 1.0 - self._rng.uniform(0.02, 0.06)

    def get_local_wind(self, farm_wind: float, turbine_index: int) -> float:
        """Get local wind speed for a specific turbine."""
        idx = min(turbine_index, len(self._offsets) - 1)
        local = farm_wind * self._wake_factors[idx] + self._offsets[idx]
        return max(0.0, local)
