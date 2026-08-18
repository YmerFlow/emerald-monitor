"""The DataFrame returned by ResourceMonitor.get_logs()."""

import time

import pandas as pd
import pytest

from helpers import SAMPLE_WINDOW

# The columns get_logs() pre-allocates, in order.
BASE_COLUMNS = ['epoch_time', 'elapsed_time', 'memory_rss',
                'cpu_times_user', 'cpu_times_system', 'cpu_times_total']

# Added row by row, so they only exist once at least one sample has been collected.
PER_SAMPLE_COLUMNS = ['gm_year', 'gm_month', 'gm_day', 'gm_time']


def test_returns_a_dataframe(sampled_monitor):
    assert isinstance(sampled_monitor.get_logs(), pd.DataFrame)


def test_has_the_documented_columns(sampled_monitor):
    logs = sampled_monitor.get_logs()
    assert list(logs.columns[:len(BASE_COLUMNS)]) == BASE_COLUMNS
    for column in PER_SAMPLE_COLUMNS:
        assert column in logs.columns


def test_row_count_matches_the_samples_collected(sampled_monitor):
    assert len(sampled_monitor.get_logs()) == len(sampled_monitor.epoch_time)


def test_epoch_time_column_matches_the_raw_samples(sampled_monitor):
    logs = sampled_monitor.get_logs()
    assert logs.epoch_time.tolist() == pytest.approx(sampled_monitor.epoch_time)


def test_epoch_time_is_a_plausible_wall_clock(sampled_monitor):
    logs = sampled_monitor.get_logs()
    now = time.time()
    assert (logs.epoch_time <= now).all()
    # Everything was sampled within the last few seconds, not at some 1970 default.
    assert (logs.epoch_time > now - 60).all()


def test_elapsed_time_starts_at_zero(sampled_monitor):
    logs = sampled_monitor.get_logs()
    assert logs.elapsed_time.iloc[0] == pytest.approx(0.0, abs=1e-9)


def test_elapsed_time_is_monotonic_non_decreasing(sampled_monitor):
    logs = sampled_monitor.get_logs()
    assert logs.elapsed_time.is_monotonic_increasing
    assert (logs.elapsed_time.diff().dropna() >= 0).all()


def test_elapsed_time_does_not_exceed_the_sampling_window(sampled_monitor):
    logs = sampled_monitor.get_logs()
    # Generous slack: the assertion is about the clock being sane, not about scheduler precision.
    assert logs.elapsed_time.max() < SAMPLE_WINDOW + 10.0


def test_elapsed_time_is_epoch_time_relative_to_the_first_sample(sampled_monitor):
    logs = sampled_monitor.get_logs()
    expected = logs.epoch_time - logs.epoch_time.iloc[0]
    assert logs.elapsed_time.tolist() == pytest.approx(expected.tolist())


def test_memory_rss_is_positive_and_in_gigabytes(sampled_monitor):
    logs = sampled_monitor.get_logs()
    assert (logs.memory_rss > 0).all()
    # A test process using more than a terabyte of RSS would mean the unit conversion is wrong.
    assert (logs.memory_rss < 1024).all()


def test_cpu_times_are_non_negative_and_non_decreasing(sampled_monitor):
    logs = sampled_monitor.get_logs()
    for column in ['cpu_times_user', 'cpu_times_system', 'cpu_times_total']:
        assert (logs[column] >= 0).all()
        # psutil cpu_times are cumulative counters for the process.
        assert (logs[column].diff().dropna() >= 0).all()


def test_cpu_times_total_is_user_plus_system(sampled_monitor):
    logs = sampled_monitor.get_logs()
    assert logs.cpu_times_total.tolist() == pytest.approx(
        (logs.cpu_times_user + logs.cpu_times_system).tolist())


def test_empty_frame_when_the_monitor_never_ran(monitor):
    """get_logs() before any sampling must return an empty frame, not raise."""
    logs = monitor.get_logs()
    assert isinstance(logs, pd.DataFrame)
    assert len(logs) == 0
    assert list(logs.columns) == BASE_COLUMNS


def test_repeated_calls_are_stable_after_stopping(sampled_monitor):
    first = sampled_monitor.get_logs()
    second = sampled_monitor.get_logs()
    pd.testing.assert_frame_equal(first, second)
