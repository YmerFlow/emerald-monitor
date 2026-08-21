"""The resource_monitor(...) context manager."""

import time

import pytest

from emerald_monitor import ResourceMonitor, resource_monitor

from helpers import FAST_INTERVAL, SAMPLE_WINDOW, drain


def test_yields_a_started_monitor():
    with resource_monitor(logging_interval=FAST_INTERVAL) as monitor:
        assert isinstance(monitor, ResourceMonitor)
        assert monitor.running is True
        assert monitor.is_alive() is True
    drain(monitor)


def test_stops_logging_on_exit():
    with resource_monitor(logging_interval=FAST_INTERVAL) as monitor:
        time.sleep(SAMPLE_WINDOW)
    assert monitor.running is False
    drain(monitor)
    assert monitor.is_alive() is False


def test_collects_logs_over_the_managed_block():
    with resource_monitor(logging_interval=FAST_INTERVAL) as monitor:
        time.sleep(SAMPLE_WINDOW)
    drain(monitor)

    logs = monitor.get_logs()
    assert len(logs) >= 1
    assert len(logs) == len(monitor.epoch_time)
    assert logs.elapsed_time.is_monotonic_increasing


def test_passes_the_logging_interval_through_positionally():
    with resource_monitor(FAST_INTERVAL) as monitor:
        assert monitor.logging_interval == FAST_INTERVAL
    drain(monitor)


def test_uses_the_default_interval_when_called_with_no_arguments():
    with resource_monitor() as monitor:
        assert monitor.logging_interval == 1
    drain(monitor)


def test_stops_logging_when_the_block_raises():
    """The stop lives in a finally, so a failing job must not leave a sampler running."""
    with pytest.raises(ValueError, match='boom'):
        with resource_monitor(logging_interval=FAST_INTERVAL) as monitor:
            time.sleep(SAMPLE_WINDOW)
            raise ValueError('boom')

    assert monitor.running is False
    drain(monitor)
    assert monitor.is_alive() is False
