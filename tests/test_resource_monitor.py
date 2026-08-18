"""Construction and start/stop lifecycle of ResourceMonitor."""

import threading
import time

from emerald_monitor import ResourceMonitor

from helpers import FAST_INTERVAL, JOIN_TIMEOUT, SAMPLE_WINDOW, drain


def test_default_logging_interval_is_one_second():
    assert ResourceMonitor().logging_interval == 1


def test_constructs_with_given_logging_interval():
    assert ResourceMonitor(logging_interval=0.25).logging_interval == 0.25


def test_is_a_daemon_thread(monitor):
    """A non-daemon sampler would keep the interpreter alive after the main program finished."""
    assert isinstance(monitor, threading.Thread)
    assert monitor.daemon is True


def test_fresh_monitor_is_idle_and_has_no_samples(monitor):
    assert monitor.running is False
    assert monitor.is_alive() is False
    assert monitor.epoch_time == []
    assert monitor.cpu_times == []
    assert monitor.memory_info == []


def test_start_logging_starts_the_thread(monitor):
    monitor.start_logging()
    try:
        assert monitor.running is True
        assert monitor.is_alive() is True
    finally:
        drain(monitor)


def test_start_then_stop_collects_at_least_one_sample(sampled_monitor):
    n = len(sampled_monitor.epoch_time)
    assert n >= 1
    # A ceiling loose enough to survive a loaded machine, tight enough to catch a sampling loop
    # that stopped honoring logging_interval altogether.
    assert n < 10 * (SAMPLE_WINDOW / FAST_INTERVAL)


def test_sample_lists_stay_the_same_length(sampled_monitor):
    n = len(sampled_monitor.epoch_time)
    assert len(sampled_monitor.cpu_times) == n
    assert len(sampled_monitor.memory_info) == n


def test_stop_logging_clears_running_and_ends_the_thread(monitor):
    monitor.start_logging()
    time.sleep(SAMPLE_WINDOW)
    monitor.stop_logging()
    assert monitor.running is False
    # stop_logging() does not join, so the thread may still be inside its final
    # time.sleep(); give it a bounded chance to notice the flag and exit.
    monitor.join(JOIN_TIMEOUT)
    assert monitor.is_alive() is False


def test_no_further_samples_long_after_stopping(sampled_monitor):
    n = len(sampled_monitor.epoch_time)
    time.sleep(20 * FAST_INTERVAL)
    assert len(sampled_monitor.epoch_time) == n


def test_start_logging_twice_does_not_start_a_second_thread(monitor, capsys):
    """The ``running`` guard is what keeps a second Thread.start() from raising RuntimeError."""
    before = set(threading.enumerate())
    monitor.start_logging()
    try:
        after_first = set(threading.enumerate())
        assert after_first - before == {monitor}

        assert monitor.start_logging() is None
        assert set(threading.enumerate()) - before == {monitor}
        assert monitor.is_alive() is True
        assert 'already in progress' in capsys.readouterr().out
    finally:
        drain(monitor)
