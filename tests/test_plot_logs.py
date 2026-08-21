"""ResourceMonitor.plot_logs(), rendered headlessly.

conftest pins matplotlib to the Agg backend, so ``plt.show()`` inside plot_logs() is a no-op and
nothing is drawn to a screen. These tests only check that the call builds the expected figure
without raising -- the appearance of the plot is not asserted.
"""

import matplotlib.pyplot as plt
import pytest


def new_figure(before):
    """The single figure created since the ``before`` snapshot of plt.get_fignums()."""
    created = set(plt.get_fignums()) - set(before)
    assert len(created) == 1
    return plt.figure(created.pop())


@pytest.mark.parametrize('time_key', ['elapsed_time', 'epoch_time'])
def test_builds_a_four_panel_figure(sampled_monitor, time_key):
    before = plt.get_fignums()
    assert sampled_monitor.plot_logs(time_key=time_key) is None

    fig = new_figure(before)
    assert len(fig.axes) == 4
    # Memory, memory change, cpu times, cpu times change -- every panel has at least one line.
    assert all(len(ax.lines) >= 1 for ax in fig.axes)
    assert fig.axes[-1].get_xlabel() == f'{time_key} (s)'


def test_honors_the_figsize_argument(sampled_monitor):
    before = plt.get_fignums()
    sampled_monitor.plot_logs(figsize=(4, 3))

    fig = new_figure(before)
    # tight_layout adjusts the axes, not the canvas.
    assert tuple(fig.get_size_inches()) == (4, 3)


def test_plots_the_memory_series_actually_sampled(sampled_monitor):
    before = plt.get_fignums()
    sampled_monitor.plot_logs()

    fig = new_figure(before)
    xdata, ydata = fig.axes[0].lines[0].get_data()
    logs = sampled_monitor.get_logs()
    assert len(xdata) == len(logs)
    assert ydata.tolist() == pytest.approx(logs.memory_rss.tolist())
