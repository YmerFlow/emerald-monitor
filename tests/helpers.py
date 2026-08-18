"""Constants and helpers shared by the emerald_monitor tests."""

# Fast enough that the whole suite stays well under a few seconds, slow enough that the
# sampling loop does not simply spin the CPU.
FAST_INTERVAL = 0.01

# How long a monitor is allowed to sample for. Many multiples of FAST_INTERVAL so that
# "at least one sample was collected" is not a coin flip on a loaded machine.
SAMPLE_WINDOW = 0.2

# Upper bound on any join()/settle wait, so a hung thread fails the test instead of the suite.
JOIN_TIMEOUT = 5.0


def drain(monitor, timeout=JOIN_TIMEOUT):
    """Stop a running monitor and wait for its sampling thread to actually exit.

    ``ResourceMonitor.stop_logging()`` only clears the ``running`` flag; the thread can still be
    parked in ``time.sleep(logging_interval)`` and append one more sample afterwards. Tests must
    not read ``get_logs()`` while ``run()`` may be mid-append, because ``get_logs()`` sizes the
    frame from ``epoch_time`` and then indexes ``cpu_times``/``memory_info``, which are appended
    a moment later. Joining here keeps the tests deterministic without asserting anything about
    that timing.
    """
    monitor.stop_logging()
    if monitor.is_alive():
        monitor.join(timeout)
    return monitor
