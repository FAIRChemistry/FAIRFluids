"""Sample / measurement access helpers shared across operations and inspection."""

from __future__ import annotations

from fairfluids.core.lib import Fluid, Measurement, Sample


def _ensure_fluid_sample(fluid: Fluid) -> Sample:
    """Ensure a fluid has a sample block and return it."""
    if fluid.sample is None:
        fluid.sample = Sample()
    return fluid.sample


def _get_measurements(fluid: Fluid) -> list[Measurement]:
    """Access measurements from the canonical sample block."""
    return _ensure_fluid_sample(fluid).measurement
