"""Unified MCMC progress reporting for multi-group fits."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from types import TracebackType


class UnifiedMcmcProgress:
    """One tqdm bar advanced from the main thread after each MCMC job.

    NumPyro reports sampling progress via ``jax.io_callback``, which runs on
    worker threads. Updating Jupyter/tqdm from those threads creates a ZMQ
    socket per refresh and can exhaust file descriptors (``Too many open files``).

    This helper therefore disables NumPyro's built-in bar and advances a single
    unified bar once per completed ``(model, group)`` fit on the main thread.
    """

    def __init__(
        self,
        *,
        total_steps: int,
        description: str = "MCMC",
    ) -> None:
        self._total_steps = max(int(total_steps), 1)
        self._description = description
        self._bar: Any = None
        self._steps_per_job = 0
        self._jobs_done = 0

    def configure_job(self, *, steps_per_job: int) -> None:
        self._steps_per_job = max(int(steps_per_job), 0)

    def complete_job(self, **postfix: Any) -> None:
        if self._bar is None or self._steps_per_job <= 0:
            return
        self._jobs_done += 1
        self._bar.update(self._steps_per_job)
        if postfix:
            self._bar.set_postfix(**postfix, refresh=True)

    def __enter__(self) -> UnifiedMcmcProgress:
        from tqdm.auto import tqdm

        self._bar = tqdm(
            total=self._total_steps,
            desc=self._description,
            unit="step",
            dynamic_ncols=True,
            leave=True,
            mininterval=0.3,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if self._bar is not None:
            if exc_type is None and self._bar.n < self._total_steps:
                remaining = self._total_steps - self._bar.n
                if remaining > 0:
                    self._bar.update(remaining)
            self._bar.close()
        return False


@contextmanager
def unified_mcmc_progress(
    *,
    total_steps: int,
    description: str = "MCMC",
) -> Iterator[UnifiedMcmcProgress]:
    """Context manager wrapper around :class:`UnifiedMcmcProgress`."""
    progress = UnifiedMcmcProgress(total_steps=total_steps, description=description)
    with progress as active:
        yield active


def total_mcmc_steps(
    *,
    num_jobs: int,
    num_warmup: int,
    num_samples: int,
    num_chains: int,
) -> int:
    """Total sampler steps across all independent MCMC jobs and chains."""
    return num_jobs * num_chains * (num_warmup + num_samples)
