"""Shared fixtures for the emerald_monitor test suite.

Matplotlib is switched to the non-interactive Agg backend *before* anything imports
``emerald_monitor`` (which imports ``matplotlib.pyplot`` at module scope), so no test can open a
window or block on ``plt.show()``.
"""

import time

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend selection)
import pytest  # noqa: E402

from emerald_monitor import ResourceMonitor  # noqa: E402

from helpers import FAST_INTERVAL, SAMPLE_WINDOW, drain  # noqa: E402


@pytest.fixture
def monitor():
    """An unstarted monitor with a fast sampling interval, always drained afterwards."""
    m = ResourceMonitor(logging_interval=FAST_INTERVAL)
    yield m
    if m.is_alive():
        drain(m)


@pytest.fixture
def sampled_monitor(monitor):
    """A monitor that has sampled for a short window and then been fully stopped."""
    monitor.start_logging()
    time.sleep(SAMPLE_WINDOW)
    return drain(monitor)


@pytest.fixture(autouse=True)
def close_figures():
    """Keep figures created by the plotting tests from accumulating across the suite."""
    yield
    plt.close('all')
