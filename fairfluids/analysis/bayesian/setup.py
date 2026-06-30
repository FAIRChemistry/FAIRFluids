"""Thin convenience wrappers over JAX / NumPyro runtime configuration.

These mirror the top-level helpers in Catalax so callers do not have to remember
the exact ``jax.config`` / ``numpyro`` incantations:

    from fairfluids.analysis.bayesian import set_platform, enable_x64

    set_platform("cpu")
    enable_x64()
"""

from __future__ import annotations


def set_platform(platform: str = "cpu") -> None:
    """Select the JAX backend (``"cpu"``, ``"gpu"`` or ``"tpu"``)."""
    import numpyro

    numpyro.set_platform(platform)


def set_host_count(n: int) -> None:
    """Set the number of host devices so NumPyro can run ``n`` chains in parallel."""
    import numpyro

    numpyro.set_host_device_count(int(n))


def enable_x64(flag: bool = True) -> None:
    """Enable (or disable) 64-bit floats in JAX — recommended for stable MCMC."""
    import jax

    jax.config.update("jax_enable_x64", bool(flag))


__all__ = ["set_platform", "set_host_count", "enable_x64"]
