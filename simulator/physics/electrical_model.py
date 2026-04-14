"""
Electrical response model for wind turbine converter and grid interaction.

Models:
  - Frequency-watt (droop) response
  - Reactive power and power factor control
  - Grid-code style LVRT/HVRT ride-through curves
  - Converter operating modes
  - Synthetic inertia response

This model sits between the turbine physics and the grid model,
producing realistic converter-side electrical behavior.
"""

import math
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ElectricalSpec:
    """Converter and grid-code parameters."""

    # Frequency-watt (droop) response
    droop_pct: float = 5.0           # 5% droop → 100% power change over 5% freq change
    freq_deadband_hz: float = 0.15   # no response within ±0.15 Hz of nominal
    freq_response_tau_s: float = 2.0 # first-order time constant for P response

    # Reactive power limits
    q_max_mvar: float = 0.8          # max reactive power (capacitive)
    q_min_mvar: float = -0.8         # min reactive power (inductive)
    power_factor_setpoint: float = 1.0  # target PF (1.0 = unity)
    q_response_tau_s: float = 1.5    # reactive power time constant

    # Voltage support
    voltage_deadband_pct: float = 3.0   # no Q response within ±3% of nominal
    voltage_droop_pct: float = 4.0      # Q/V droop
    voltage_support_enabled: bool = True

    # Ride-through curves (time limits in seconds)
    # LVRT: voltage thresholds as fraction of nominal
    lvrt_zero_ride_s: float = 0.15     # ride through 0V for 150ms
    lvrt_50pct_ride_s: float = 0.60    # ride through 50% V for 600ms
    lvrt_80pct_ride_s: float = 3.0     # ride through 80% V for 3s
    lvrt_90pct_ride_s: float = 10.0    # ride through 90% V for 10s
    # HVRT
    hvrt_120pct_ride_s: float = 0.50   # ride through 120% V for 500ms
    hvrt_110pct_ride_s: float = 5.0    # ride through 110% V for 5s

    # Synthetic inertia
    inertia_constant_h: float = 3.5    # virtual inertia constant (seconds)
    inertia_enabled: bool = True
    inertia_response_tau_s: float = 0.5

    # Converter limits
    apparent_power_max_mva: float = 2.5  # max apparent power


@dataclass
class RideThroughState:
    """Tracks ride-through accumulation for LVRT/HVRT."""
    lvrt_accum_s: float = 0.0
    hvrt_accum_s: float = 0.0
    lvrt_band: int = 0         # 0=normal, 1=90%, 2=80%, 3=50%, 4=zero
    hvrt_band: int = 0         # 0=normal, 1=110%, 2=120%
    recovery_timer_s: float = 0.0


class ElectricalModel:
    """Converter-level electrical response model.

    Produces:
      - active_power_kw: frequency-adjusted active power
      - reactive_power_kvar: voltage-support or PF-controlled Q
      - power_factor: resulting PF
      - apparent_power_kva: S = sqrt(P² + Q²)
      - converter_mode: current operating mode string
      - freq_watt_derate: power reduction from frequency response (0..1)
      - inertia_power_kw: synthetic inertia contribution
      - ride_through_status: current LVRT/HVRT band
    """

    def __init__(self, spec: Optional[ElectricalSpec] = None,
                 individuality: Optional[Dict] = None):
        self.spec = spec or ElectricalSpec()
        self._ind = individuality or {}

        # State variables
        self._active_power_kw: float = 0.0
        self._reactive_power_kvar: float = 0.0
        self._freq_watt_cmd: float = 1.0       # 1.0 = no derate
        self._inertia_power_kw: float = 0.0
        self._prev_frequency: float = 0.0
        self._prev_frequency_valid: bool = False
        self._ride_through = RideThroughState()
        self._converter_mode: str = "idle"
        self._q_voltage_cmd_kvar: float = 0.0

        # Per-turbine variation
        self._droop_scale = 1.0 + self._ind.get("grid_derate_sensitivity", 1.0) * 0.05 - 0.05
        self._q_bias = self._ind.get("grid_voltage_local_bias", 0.0) * 0.001

    def reset(self):
        self._active_power_kw = 0.0
        self._reactive_power_kvar = 0.0
        self._freq_watt_cmd = 1.0
        self._inertia_power_kw = 0.0
        self._prev_frequency = 0.0
        self._prev_frequency_valid = False
        self._ride_through = RideThroughState()
        self._converter_mode = "idle"
        self._q_voltage_cmd_kvar = 0.0

    def step(
        self,
        gen_power_kw: float,
        grid_frequency_hz: float,
        grid_voltage_v: float,
        nominal_freq_hz: float,
        nominal_voltage_v: float,
        rated_power_kw: float,
        dt: float,
        is_producing: bool,
        is_starting: bool,
    ) -> Dict[str, float]:
        """Advance electrical model one timestep.

        Returns dict with electrical output tags.
        """
        s = self.spec

        if not is_producing and not is_starting:
            self._converter_mode = "idle"
            self._active_power_kw = 0.0
            self._reactive_power_kvar = 0.0
            self._inertia_power_kw = 0.0
            self._freq_watt_cmd = 1.0
            self._prev_frequency_valid = False
            self._ride_through = RideThroughState()
            return self._build_output(nominal_voltage_v)

        # ── 1. Frequency-watt (droop) response ──
        freq_dev = grid_frequency_hz - nominal_freq_hz
        if abs(freq_dev) <= s.freq_deadband_hz:
            freq_watt_target = 1.0
        else:
            # Droop: ΔP/Prated = -Δf / (droop% * f_nom)
            effective_dev = freq_dev - math.copysign(s.freq_deadband_hz, freq_dev)
            droop_gain = 1.0 / (s.droop_pct / 100.0 * nominal_freq_hz)
            delta_p = -effective_dev * droop_gain * self._droop_scale
            freq_watt_target = max(0.0, min(1.0, 1.0 + delta_p))

        # First-order filter for smooth response
        alpha_fw = 1.0 - math.exp(-dt / s.freq_response_tau_s)
        self._freq_watt_cmd += (freq_watt_target - self._freq_watt_cmd) * alpha_fw

        # ── 2. Synthetic inertia response ──
        inertia_target = 0.0
        if s.inertia_enabled and self._prev_frequency_valid and is_producing:
            df_dt = (grid_frequency_hz - self._prev_frequency) / max(dt, 0.01)
            # P_inertia = 2 * H * S_rated * (df/dt) / f_nom
            inertia_target = (
                2.0 * s.inertia_constant_h * rated_power_kw
                * df_dt / nominal_freq_hz
            )
            inertia_target = max(-rated_power_kw * 0.1, min(rated_power_kw * 0.1, inertia_target))

        alpha_in = 1.0 - math.exp(-dt / s.inertia_response_tau_s)
        self._inertia_power_kw += (inertia_target - self._inertia_power_kw) * alpha_in
        self._prev_frequency = grid_frequency_hz
        self._prev_frequency_valid = True

        # ── 3. Active power after frequency response ──
        freq_adjusted_kw = gen_power_kw * self._freq_watt_cmd + self._inertia_power_kw
        freq_adjusted_kw = max(0.0, freq_adjusted_kw)

        # Smooth active power
        alpha_p = 1.0 - math.exp(-dt / 1.0)
        self._active_power_kw += (freq_adjusted_kw - self._active_power_kw) * alpha_p

        # ── 4. Reactive power / voltage support ──
        q_target = self._compute_reactive_power(
            self._active_power_kw, grid_voltage_v, nominal_voltage_v, rated_power_kw
        )
        alpha_q = 1.0 - math.exp(-dt / s.q_response_tau_s)
        self._reactive_power_kvar += (q_target - self._reactive_power_kvar) * alpha_q

        # ── 5. Apparent power limit (converter rating) ──
        max_s_kva = s.apparent_power_max_mva * 1000.0
        s_kva = math.sqrt(self._active_power_kw ** 2 + self._reactive_power_kvar ** 2)
        if s_kva > max_s_kva and s_kva > 0:
            scale = max_s_kva / s_kva
            self._active_power_kw *= scale
            self._reactive_power_kvar *= scale
            s_kva = max_s_kva

        # ── 6. Ride-through evaluation ──
        self._update_ride_through(grid_voltage_v, nominal_voltage_v, dt)

        # ── 7. Converter mode ──
        if is_starting:
            self._converter_mode = "starting"
        elif abs(self._freq_watt_cmd - 1.0) > 0.01:
            self._converter_mode = "freq_response"
        elif abs(self._reactive_power_kvar) > 10.0:
            self._converter_mode = "voltage_support"
        elif self._ride_through.lvrt_band > 0 or self._ride_through.hvrt_band > 0:
            self._converter_mode = "ride_through"
        else:
            self._converter_mode = "normal"

        return self._build_output(nominal_voltage_v)

    def _compute_reactive_power(
        self, active_kw: float, grid_v: float,
        nominal_v: float, rated_kw: float,
    ) -> float:
        """Compute reactive power target from voltage support + PF setpoint."""
        s = self.spec

        # Voltage-based Q command (voltage support / droop)
        q_voltage = 0.0
        if s.voltage_support_enabled and nominal_v > 0:
            v_dev_pct = (grid_v - nominal_v) / nominal_v * 100.0
            if abs(v_dev_pct) > s.voltage_deadband_pct:
                effective_dev = v_dev_pct - math.copysign(s.voltage_deadband_pct, v_dev_pct)
                # Q/S_rated = -ΔV / droop%
                q_voltage = -effective_dev / s.voltage_droop_pct * rated_kw
                q_voltage += self._q_bias * rated_kw * 0.01

        # PF-based Q command
        q_pf = 0.0
        if s.power_factor_setpoint < 1.0 and active_kw > 10.0:
            # Q = P * tan(acos(PF))
            pf = max(0.8, min(1.0, s.power_factor_setpoint))
            q_pf = active_kw * math.tan(math.acos(pf))

        # Combine: voltage support takes priority when active
        q_target = q_voltage if abs(q_voltage) > abs(q_pf) else q_pf

        # Clamp to limits
        q_max = s.q_max_mvar * 1000.0  # kvar
        q_min = s.q_min_mvar * 1000.0
        return max(q_min, min(q_max, q_target))

    def _update_ride_through(self, grid_v: float, nominal_v: float, dt: float):
        """Evaluate LVRT/HVRT ride-through status."""
        rt = self._ride_through

        if nominal_v <= 0:
            return

        v_pu = grid_v / nominal_v  # per-unit voltage

        # LVRT bands
        if v_pu < 0.10:
            rt.lvrt_band = 4
            rt.lvrt_accum_s += dt
        elif v_pu < 0.50:
            rt.lvrt_band = 3
            rt.lvrt_accum_s += dt
        elif v_pu < 0.80:
            rt.lvrt_band = 2
            rt.lvrt_accum_s += dt
        elif v_pu < 0.90:
            rt.lvrt_band = 1
            rt.lvrt_accum_s += dt
        else:
            # Recovery
            if rt.lvrt_band > 0:
                rt.recovery_timer_s += dt
                if rt.recovery_timer_s > 2.0:
                    rt.lvrt_band = 0
                    rt.lvrt_accum_s = max(0.0, rt.lvrt_accum_s - dt * 0.5)
            else:
                rt.lvrt_accum_s = max(0.0, rt.lvrt_accum_s - dt * 0.2)

        # HVRT bands
        if v_pu > 1.20:
            rt.hvrt_band = 2
            rt.hvrt_accum_s += dt
        elif v_pu > 1.10:
            rt.hvrt_band = 1
            rt.hvrt_accum_s += dt
        else:
            if rt.hvrt_band > 0:
                rt.recovery_timer_s += dt
                if rt.recovery_timer_s > 2.0:
                    rt.hvrt_band = 0
                    rt.hvrt_accum_s = max(0.0, rt.hvrt_accum_s - dt * 0.5)
            else:
                rt.hvrt_accum_s = max(0.0, rt.hvrt_accum_s - dt * 0.2)

        if rt.lvrt_band == 0 and rt.hvrt_band == 0:
            rt.recovery_timer_s = 0.0

    def get_ride_through_limit(self) -> float:
        """Return the ride-through time limit for current voltage band (seconds)."""
        s = self.spec
        rt = self._ride_through
        if rt.lvrt_band == 4:
            return s.lvrt_zero_ride_s
        if rt.lvrt_band == 3:
            return s.lvrt_50pct_ride_s
        if rt.lvrt_band == 2:
            return s.lvrt_80pct_ride_s
        if rt.lvrt_band == 1:
            return s.lvrt_90pct_ride_s
        if rt.hvrt_band == 2:
            return s.hvrt_120pct_ride_s
        if rt.hvrt_band == 1:
            return s.hvrt_110pct_ride_s
        return float('inf')

    def should_trip(self) -> Optional[str]:
        """Check if ride-through limits have been exceeded.

        Returns trip reason string, or None if still within limits.
        """
        rt = self._ride_through
        limit = self.get_ride_through_limit()
        accum = rt.lvrt_accum_s if rt.lvrt_band > 0 else rt.hvrt_accum_s
        if accum > limit:
            if rt.lvrt_band > 0:
                return f"lvrt_band{rt.lvrt_band}"
            if rt.hvrt_band > 0:
                return f"hvrt_band{rt.hvrt_band}"
        return None

    def _build_output(self, nominal_voltage_v: float) -> Dict[str, float]:
        p = self._active_power_kw
        q = self._reactive_power_kvar
        s_kva = math.sqrt(p ** 2 + q ** 2) if (p > 0 or abs(q) > 0) else 0.0

        if s_kva > 0 and p > 0:
            pf = p / s_kva
            # Sign convention: leading (capacitive Q > 0) → positive PF sign
            if q < 0:
                pf = -pf
        else:
            pf = 1.0

        rt = self._ride_through
        ride_band = rt.lvrt_band if rt.lvrt_band > 0 else -rt.hvrt_band if rt.hvrt_band > 0 else 0

        return {
            "active_power_kw": round(p, 2),
            "reactive_power_kvar": round(q, 2),
            "power_factor": round(pf, 4),
            "apparent_power_kva": round(s_kva, 2),
            "freq_watt_derate": round(self._freq_watt_cmd, 4),
            "inertia_power_kw": round(self._inertia_power_kw, 2),
            "converter_mode": self._converter_mode,
            "ride_through_band": ride_band,
            "ride_through_accum_s": round(max(rt.lvrt_accum_s, rt.hvrt_accum_s), 3),
        }
